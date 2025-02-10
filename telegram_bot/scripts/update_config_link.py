from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link


async def update_config_link():
    async with DatabaseContextManager() as session:
        subs = await session.subscription.get_subs()
        for sub in subs:
            if "https" not in sub.config_link:
                new_config_link = await create_config_link(sub.user_id, sub.subscription_id)
                await session.subscription.update_sub(sub.subscription_id, config_link=new_config_link)
        await session.session.commit()
