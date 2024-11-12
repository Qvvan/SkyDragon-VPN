import random

from handlers.services.get_session_cookies import get_session_cookie
from handlers.services.key_create import ShadowsocksKeyManager
from logger.logging_config import logger


async def get_active_server_and_key(user_id: int, username: str, session_methods):
    try:
        server_ips = await session_methods.servers.get_all_servers()
        available_servers = [server for server in server_ips if server.hidden == 0]
        random.shuffle(available_servers)

        for server in available_servers:
            try:
                session_cookie = await get_session_cookie(server.server_ip)
                if session_cookie:
                    server_ip = server.server_ip
                    shadowsocks_manager = ShadowsocksKeyManager(server_ip, session_cookie)
                    key, key_id = await shadowsocks_manager.manage_shadowsocks_key(
                        tg_id=str(user_id),
                        username=username,
                    )
                    return shadowsocks_manager, server_ip, key, key_id
            except Exception as e:
                await logger.log_error(f"Сервер {server.server_ip} не доступен", e)

        return None, None, None, None
    except Exception as e:
        await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
        return None, None, None, None
