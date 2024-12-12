import random

from handlers.services.key_create import VlessKeyManager
from logger.logging_config import logger


async def get_active_server_and_key(user_id: int, username: str, session_methods):
    try:
        server_ips = await session_methods.servers.get_all_servers()
        available_servers = [server for server in server_ips if server.hidden == 0]
        random.shuffle(available_servers)

        for server in available_servers:
            try:
                server_ip = server.server_ip
                vless_manager = VlessKeyManager(server_ip)
                key, key_id = await vless_manager.manage_vless_key(
                    tg_id=str(user_id),
                    username=username,
                )
                return vless_manager, server_ip, key, key_id
            except Exception as e:
                await logger.log_error(f"Сервер {server.server_ip} не доступен", e)

        return None, None, None, None
    except Exception as e:
        await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
        return None, None, None, None
