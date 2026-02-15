from datetime import datetime, timezone

from database.context_manager import DatabaseContextManager
from handlers.services.identifiers import encode_numbers, generate_deterministic_uuid
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger


async def create_keys(user_id: int, username: str, sub_id: int, expiry_days: int = 0):
    """
    Создает ключи для подписки на всех активных серверах и всех портах из available_ports

    Args:
        user_id: ID пользователя Telegram
        username: Имя пользователя (для логирования)
        sub_id: ID подписки
        expiry_days: Количество дней до истечения (0 = без ограничений)

    Returns:
        True если хотя бы один ключ создан успешно
    """
    async with DatabaseContextManager() as session_methods:
        try:
            sub_uuid = encode_numbers(user_id, sub_id)
            client_id = generate_deterministic_uuid(user_id, sub_id)
            
            # Получаем активные серверы (с заполненным available_ports)
            servers = await session_methods.servers.get_active_servers_for_keys()
            
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
                        
                        result = await gateway.add_client(
                            port=port,
                            client_id=client_id,
                            email=email,
                            tg_id=str(user_id),
                            sub_id=sub_uuid,
                            limit_ip=2,
                            expiry_days=expiry_days,
                            enable=True,
                        )
                        
                        if result:
                            success_count += 1
                            await logger.info(
                                f"Ключ создан: user_id={user_id}, sub_id={sub_id}, "
                                f"server={server.server_ip}, port={port}"
                            )
                        else:
                            await logger.warning(
                                f"Не удалось создать ключ: user_id={user_id}, sub_id={sub_id}, "
                                f"server={server.server_ip}, port={port}"
                            )

                        await gateway.close()

                    except Exception as e:
                        await logger.log_error(
                            f"Ошибка создания ключа на сервер {server.server_ip}, порт {port}", e
                        )

            await logger.info(
                f"Создание ключей завершено: user_id={user_id}, sub_id={sub_id}, "
                f"успешно={success_count}/{total_attempts}"
            )

            return success_count > 0

        except Exception as e:
            await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
            return False