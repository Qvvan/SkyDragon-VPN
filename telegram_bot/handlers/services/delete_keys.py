from database.context_manager import DatabaseContextManager
from handlers.services.identifiers import generate_deterministic_uuid, encode_numbers
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger


async def delete_keys(user_id: int, subscription_id: int) -> None:
    """
    Удаляет ключи/клиентов в 3x-ui на всех активных серверах и портах для указанной подписки.

    Важно: ключи создаются детерминированно через (user_id, subscription_id), поэтому для удаления
    можно восстановить client_id тем же методом.
    """
    async with DatabaseContextManager() as session:
        # sub_uuid используется только для логирования (client_id восстанавливается из него же).
        sub_uuid = encode_numbers(user_id, subscription_id)
        client_id = generate_deterministic_uuid(user_id, subscription_id)

        servers = await session.servers.get_active_servers_for_keys()

        total_attempts = 0
        success_count = 0

        for server in servers:
            available_ports = server.available_ports or [443]

            for port in available_ports:
                total_attempts += 1
                try:
                    gateway = PanelGateway(server)
                    ok = await gateway.delete_client(port=port, client_id=client_id)
                    if ok:
                        success_count += 1
                    await gateway.close()
                except Exception as e:
                    await logger.log_error(
                        f"Ошибка удаления ключа: user_id={user_id}, sub_id={subscription_id} "
                        f"(sub_uuid={sub_uuid}), server={server.server_ip}, port={port}",
                        e,
                    )

        await logger.info(
            f"Удаление ключей завершено: user_id={user_id}, sub_id={subscription_id}, "
            f"успешно={success_count}/{total_attempts}"
        )

