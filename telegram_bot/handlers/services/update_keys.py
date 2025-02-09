from database.context_manager import DatabaseContextManager
from handlers.services.key_create import VlessKeyManager, ShadowsocksKeyManager
from logger.logging_config import logger
from models.models import NameApp


async def update_keys(subscription_id: int, status: bool):
    async with DatabaseContextManager() as session:
        sub = await session.subscription.get_subscription_by_id(subscription_id)
        keys = sub.key_ids
        for key_id in keys:
            try:
                key_info = await session.keys.get_key_by_id(key_id)
                if key_info:
                    if key_info.name_app == NameApp.VLESS:
                        vless_manager = VlessKeyManager(key_info.server_ip)
                        await vless_manager.update_key_enable(key_info.key_id, status)
                    elif key_info.name_app == NameApp.OUTLINE:
                        outline_manager = ShadowsocksKeyManager(key_info.server_ip)
                        await outline_manager.update_key_enable(key_info.key_id, status)
                    await session.keys.update_key(key_info.id, status='active' if status else 'disabled')
                else:
                    await logger.warning(f"При обновлении ключа: {key_id} не удалось найти ключ")
            except Exception as e:
                await logger.warning(f"При обновлении ключа: {key_id} что-то пошло не так: {e}")
        await session.session.commit()