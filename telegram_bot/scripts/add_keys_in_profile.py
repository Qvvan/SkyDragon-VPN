from database.context_manager import DatabaseContextManager
from handlers.services.key_create import VlessKeyManager, ShadowsocksKeyManager
from logger.logging_config import logger
from models.models import Keys, NameApp, Subscriptions


async def update_config_link():
    async with DatabaseContextManager() as session:
        subs = await session.subscription.get_subs()
        for sub in subs:
            if len(sub.key_ids) == 1:
                keys = await create_keys_in_profile(sub.user_id, sub)
                await session.subscription.update_sub(sub.subscription_id, key_ids=keys)
        await session.session.commit()


async def create_keys_in_profile(user_id: int, sub: Subscriptions):
    keys = sub.key_ids
    async with DatabaseContextManager() as session_methods:
        try:
            user = await session_methods.users.get_user(sub.user_id)
            username = user.username
            key_info = await session_methods.keys.get_key_by_id(keys[0])
            server_ips = await session_methods.servers.get_all_servers()
            for server in server_ips:
                try:
                    if key_info.server_ip == server.server_ip:
                        if key_info.name_app == NameApp.VLESS:
                            outline_manager = ShadowsocksKeyManager(server.server_ip)
                            outline_key, outline_key_id = await outline_manager.manage_shadowsocks_key(
                                tg_id=str(user_id),
                                username=username,
                                server_name=server.name
                            )
                            outline_key = await session_methods.keys.add_key(
                                Keys(
                                    key_id=outline_key_id,
                                    key=outline_key,
                                    server_ip=server.server_ip,
                                    name_app=NameApp.OUTLINE
                                ))

                            keys.append(outline_key.id)
                            continue
                        else:
                            vless_manager = VlessKeyManager(server.server_ip)
                            key, key_id = await vless_manager.manage_vless_key(
                                tg_id=str(user_id),
                                username=username,
                                server_name=server.name
                            )

                            vless_key = await session_methods.keys.add_key(
                                Keys(
                                    key_id=key_id,
                                    key=key,
                                    server_ip=server.server_ip,
                                    name_app=NameApp.VLESS
                                ))

                            keys.append(vless_key.id)
                            continue
                    vless_manager = VlessKeyManager(server.server_ip)
                    key, key_id = await vless_manager.manage_vless_key(
                        tg_id=str(user_id),
                        username=username,
                        server_name=server.name
                    )

                    vless_key = await session_methods.keys.add_key(
                        Keys(
                            key_id=key_id,
                            key=key,
                            server_ip=server.server_ip,
                            name_app=NameApp.VLESS
                        ))

                    keys.append(vless_key.id)

                    outline_manager = ShadowsocksKeyManager(server.server_ip)
                    outline_key, outline_key_id = await outline_manager.manage_shadowsocks_key(
                        tg_id=str(user_id),
                        username=username,
                        server_name=server.name
                    )
                    outline_key = await session_methods.keys.add_key(
                        Keys(
                            key_id=outline_key_id,
                            key=outline_key,
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
