from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger


async def delete_keys(subscription_id: int):
    async with DatabaseContextManager() as session:
        sub = await session.subscription.get_subscription_by_id(subscription_id)
        keys = sub.key_ids
        for key_id in keys:
            try:
                key_info = await session.keys.get_key_by_id(key_id)
                if key_info:
                    await BaseKeyManager(server_ip=key_info.server_ip).delete_key(key_info.key_id)
                    await session.keys.delete_key(key_info.id)
                else:
                    await logger.warning(f"При удаление ключа: {key_id} не удалось найти ключ")
            except Exception as e:
                await logger.warning(f"При удаление ключа: {key_id} что-то пошло не так: {e}")
        await session.session.commit()