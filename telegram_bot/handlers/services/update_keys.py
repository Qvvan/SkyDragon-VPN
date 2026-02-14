from database.context_manager import DatabaseContextManager
from handlers.services.identifiers import encode_numbers, generate_deterministic_uuid
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger


async def update_keys(user_id: int, subscription_id: int, status: bool):
    """
    Обновляет статус включения/выключения ключей для подписки на всех активных серверах и портах

    Args:
        user_id: ID пользователя Telegram
        subscription_id: ID подписки
        status: True для включения, False для выключения
    """
    async with DatabaseContextManager() as session:
        try:
            sub_uuid = encode_numbers(user_id, subscription_id)
            client_id = generate_deterministic_uuid(user_id, subscription_id)
            
            # Получаем активные серверы (с заполненным available_ports)
            servers = await session.servers.get_active_servers_for_keys()
            
            success_count = 0
            total_attempts = 0

            for server in servers:
                # Определяем список портов для этого сервера
                available_ports = server.available_ports or [443]
                
                for port in available_ports:
                    total_attempts += 1
                    try:
                        gateway = PanelGateway(server)
                        
                        # Формируем уникальный email для каждого порта
                        email = f"{sub_uuid}_port{port}"
                        
                        result = await gateway.update_client_enable(
                            port=port,
                            client_id=client_id,
                            enable=status,
                            email=email,
                            tg_id=str(user_id),
                            sub_id=sub_uuid,
                            limit_ip=1,
                        )
                        
                        if result:
                            success_count += 1
                            await logger.info(
                                f"Статус ключа обновлен: user_id={user_id}, sub_id={subscription_id}, "
                                f"server={server.server_ip}, port={port}, enable={status}"
                            )
                        else:
                            await logger.warning(
                                f"Не удалось обновить статус ключа: user_id={user_id}, sub_id={subscription_id}, "
                                f"server={server.server_ip}, port={port}"
                            )

                        await gateway.close()

                    except Exception as e:
                        await logger.log_error(
                            f"Ошибка обновления ключа на сервер {server.server_ip}, порт {port}, "
                            f"subscription ID: {subscription_id}", e
                        )

            await logger.info(
                f"Обновление ключей завершено: user_id={user_id}, sub_id={subscription_id}, "
                f"успешно={success_count}/{total_attempts}, enable={status}"
            )

        except Exception as e:
            await logger.log_error(f"Ошибка при получении серверов из базы данных", e)

