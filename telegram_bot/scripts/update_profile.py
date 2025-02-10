from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger


async def update_profile():
    async with DatabaseContextManager() as session:
        keys = await session.keys.get_all_keys()
        user_keys = {}
        for key in keys:
            key_info = await BaseKeyManager(server_ip=key.server_ip).get_inbound_by_id(key.key_id)
            remark = key_info.get("obj", {}).get("remark", '')
            tg_id = remark.split("TgId:")[1].strip().split()[0]
            try:
                tg_id = int(tg_id)
            except:
                await logger.warning(f"У данного ключа нет айдишника: {key.key_id} {key.server_ip}")
                continue
            if tg_id in user_keys:
                user_keys[tg_id].append(key.id)
            else:
                user_keys[tg_id] = [key.id]
            print(user_keys)
        for user_id, key_list in user_keys.items():
            try:
                sub = await session.subscription.get_subscription(user_id)
                if len(sub) > 1:
                    await logger.warning(
                        f"У данного пользователя несколько подписок {user_id}, ключи закинули в первую")
                await session.subscription.update_sub(sub[0].subscription_id, key_ids=key_list)
            except Exception as e:
                await logger.log_error("Что-то пошло не так", e)
        await session.session.commit()
