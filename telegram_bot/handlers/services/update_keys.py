from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger


async def update_keys(subscription_id: int, status: bool):
    async with DatabaseContextManager() as session:
        sub = await session.subscription.get_subscription_by_id(subscription_id)
        keys = sub.key_ids
        for key_id in keys:
            try:
                key_info = await session.keys.get_key_by_id(key_id)
                if key_info:
                    base = BaseKeyManager(key_info.server_ip)
                    print("key_id", key_info.key_id)
                    await base.update_client_status(key_info.key_id, key_info.email, sub.user_id, status)
            except Exception as e:
                await logger.warning(f"При обновлении ключа: {key_id} что-то пошло не так: {e}")
        await session.session.commit()
