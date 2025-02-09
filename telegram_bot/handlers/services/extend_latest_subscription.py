from datetime import datetime, timedelta

from handlers.services.create_config_link import create_config_link
from handlers.services.create_keys import create_keys
from handlers.services.create_subscription_service import SubscriptionService
from logger.logging_config import logger
from models.models import Subscriptions, SubscriptionStatusEnum


class NoAvailableServersError(Exception):
    pass


async def extend_user_subscription(user_id: int, username: str, days: int, session_methods):
    try:
        subscriptions = await session_methods.subscription.get_subscription(user_id)

        if not subscriptions:
            keys = await create_keys(user_id, username)
            config_link = await create_config_link(user_id)

            subscription = Subscriptions(
                user_id=user_id,
                service_id=0,
                config_link=config_link,
                key_ids=keys,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days)
            )
            subscription_created = await SubscriptionService.create_subscription(
                subscription,
                session_methods
            )
            if not subscription_created:
                raise Exception("Ошибка создания подписки")
            return subscription

        latest_subscription = max(subscriptions, key=lambda sub: sub.end_date or datetime.min)
        subscription_id = latest_subscription.subscription_id
        end_date = latest_subscription.end_date
        status_update_keys = True

        if end_date and end_date > datetime.utcnow():
            new_end_date = end_date + timedelta(days=days)
            status_update_keys = False
        else:
            new_end_date = max(datetime.utcnow(), end_date or datetime.utcnow()) + timedelta(days=days)

        await session_methods.subscription.update_sub(
            subscription_id=subscription_id,
            end_date=new_end_date,
            status=SubscriptionStatusEnum.ACTIVE,
            reminder_sent=0
        )
        if status_update_keys:
            # TODO Сделать обновление ключей
            pass
        return latest_subscription

    except Exception as e:
        await logger.log_error(f"Error extending or creating user subscription, ID {user_id}", e)
        raise Exception("Ошибка при продлении или создании подписки.")
