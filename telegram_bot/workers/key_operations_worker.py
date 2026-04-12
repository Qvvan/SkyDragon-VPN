"""
Воркер обработки операций с ключами (таблица key_operations).

Запускается как фоновая задача вместе с ботом.
Читает pending-операции, вызывает PanelGateway для каждого сервера,
обновляет статус.
"""
import asyncio
from datetime import datetime

from database.context_manager import DatabaseContextManager
from handlers.services.identifiers import encode_numbers, generate_deterministic_uuid
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger

_POLL_INTERVAL = 5.0       # секунд между опросами при пустой очереди
_STALE_RESET_INTERVAL = 60 # секунд между проверками зависших операций
_BATCH_SIZE = 20


async def _execute_operation(op, server) -> None:
    """
    Выполняет одну операцию на одном сервере (все порты).
    Кидает исключение при ошибке — вызывающий код обновит статус.
    """
    sub_uuid = encode_numbers(op.user_id, op.subscription_id)
    client_id = generate_deterministic_uuid(op.user_id, op.subscription_id)
    available_ports = server.available_ports or [443]

    action = op.action

    success_count = 0
    for port in available_ports:
        email = f"{sub_uuid}_port{port}"
        gateway = PanelGateway(server)
        try:
            if action == 'create':
                result = await gateway.add_client(
                    port=port,
                    client_id=client_id,
                    email=email,
                    tg_id=str(op.user_id),
                    sub_id=sub_uuid,
                    limit_ip=2,
                    expiry_days=op.days or 0,
                    enable=True,
                )
            elif action in ('enable', 'update'):
                result = await gateway.update_client_enable(
                    port=port,
                    client_id=client_id,
                    enable=True,
                    email=email,
                    tg_id=str(op.user_id),
                    sub_id=sub_uuid,
                    limit_ip=2,
                )
            elif action == 'disable':
                result = await gateway.update_client_enable(
                    port=port,
                    client_id=client_id,
                    enable=False,
                    email=email,
                    tg_id=str(op.user_id),
                    sub_id=sub_uuid,
                    limit_ip=2,
                )
            elif action == 'delete':
                # TODO: реализовать удаление ключа в PanelGateway
                result = True
            else:
                result = False

            if result:
                success_count += 1
        except Exception as e:
            await logger.log_error(
                f"Ошибка выполнения op_id={op.operation_id} action={action} "
                f"server={server.server_ip} port={port}", e
            )
        finally:
            await gateway.close()

    if success_count == 0:
        raise Exception(
            f"Не удалось выполнить ни одной операции на сервере {server.server_ip} "
            f"(портов: {len(available_ports)})"
        )


async def _process_batch() -> int:
    """
    Забирает пачку pending-операций, выполняет их, обновляет статусы.
    Возвращает количество обработанных операций.
    """
    async with DatabaseContextManager() as sm:
        operations = await sm.key_operations.claim_pending(limit=_BATCH_SIZE)
        if not operations:
            return 0

        await sm.session.commit()  # зафиксировать смену статуса на 'processing'

        processed = 0
        for op in operations:
            server = await sm.servers.get_server_by_id(op.server_id)
            if not server:
                async with DatabaseContextManager() as sm2:
                    await sm2.key_operations.mark_failed(
                        op.operation_id, f"Сервер server_id={op.server_id} не найден", 0
                    )
                    await sm2.session.commit()
                processed += 1
                continue

            try:
                await _execute_operation(op, server)
                async with DatabaseContextManager() as sm2:
                    await sm2.key_operations.mark_completed(op.operation_id)
                    await sm2.session.commit()
                await logger.info(
                    f"key_op completed: op_id={op.operation_id} action={op.action} "
                    f"server={server.server_ip}"
                )
            except Exception as e:
                retry_seconds = min(30 * (2 ** op.retry_count), 3600)
                async with DatabaseContextManager() as sm2:
                    await sm2.key_operations.mark_failed(op.operation_id, str(e), retry_seconds)
                    await sm2.session.commit()
                await logger.warning(
                    f"key_op failed: op_id={op.operation_id} action={op.action} "
                    f"server={server.server_ip} retry_in={retry_seconds}s"
                )
            processed += 1

        return processed


async def run_key_operations_worker():
    """
    Основной цикл воркера. Запускать как asyncio.create_task().
    """
    await logger.info("key_operations_worker: запуск")
    last_stale_reset = 0.0

    while True:
        try:
            now = asyncio.get_event_loop().time()

            # Периодически сбрасываем зависшие 'processing' операции
            if now - last_stale_reset >= _STALE_RESET_INTERVAL:
                async with DatabaseContextManager() as sm:
                    count = await sm.key_operations.reset_stale_processing(older_than_seconds=300)
                    if count:
                        await sm.session.commit()
                        await logger.warning(f"key_operations_worker: сброшено {count} зависших операций")
                last_stale_reset = now

            processed = await _process_batch()

            if processed == 0:
                await asyncio.sleep(_POLL_INTERVAL)

        except asyncio.CancelledError:
            await logger.info("key_operations_worker: остановлен")
            break
        except Exception as e:
            await logger.log_error("key_operations_worker: неожиданная ошибка", e)
            await asyncio.sleep(_POLL_INTERVAL)
