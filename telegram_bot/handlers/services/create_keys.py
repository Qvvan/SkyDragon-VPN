from database.context_manager import DatabaseContextManager
from handlers.services.key_create import VlessKeyManager, ShadowsocksKeyManager
from logger.logging_config import logger
from models.models import Keys, NameApp


async def create_keys(user_id: int, username: str):
    keys = []

    async with DatabaseContextManager() as session_methods:
        try:
            server_ips = await session_methods.servers.get_all_servers()
            for server in server_ips:
                try:
                    vless_manager = VlessKeyManager(server.server_ip)
                    key, key_id, email = await vless_manager.manage_vless_key(
                        tg_id=str(user_id),
                        username=username,
                        server_name=server.name
                    )

                    vless_key = await session_methods.keys.add_key(
                        Keys(
                            key_id=key_id,
                            key=key,
                            email=email,
                            server_ip=server.server_ip,
                            name_app=NameApp.VLESS
                        ))

                    keys.append(vless_key.id)

                    outline_manager = ShadowsocksKeyManager(server.server_ip)
                    outline_key, outline_key_id, email = await outline_manager.manage_shadowsocks_key(
                        tg_id=str(user_id),
                        username=username,
                        server_name=server.name
                    )
                    outline_key = await session_methods.keys.add_key(
                        Keys(
                            key_id=outline_key_id,
                            key=outline_key,
                            email=email,
                            server_ip=server.server_ip,
                            name_app=NameApp.OUTLINE
                        ))

                    keys.append(outline_key.id)
                except Exception as e:
                    await logger.log_error(f"Ошибка создания ключа на сервер {server.server_ip}", e)

            await session_methods.session.commit()
            return keys

        except Exception as e:
            await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
            return False
