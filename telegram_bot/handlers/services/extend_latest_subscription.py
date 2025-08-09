from datetime import datetime, timedelta

from handlers.services.create_keys import create_keys
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.update_keys import update_keys
from logger.logging_config import logger
from models.models import Subscriptions, SubscriptionStatusEnum


class NoAvailableServersError(Exception):
    pass


async def extend_user_subscription(user_id: int, username: str, days: int, session_methods):
    try:
        subscriptions = await session_methods.subscription.get_subscription(user_id)

        if not subscriptions:
            subscription = Subscriptions(
                user_id=user_id,
                service_id=0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days)
            )
            subscription_created = await SubscriptionService.create_subscription(
                subscription,
                session_methods
            )

            if not subscription_created:
                raise Exception("Ошибка создания подписки")

            await create_keys(user_id, username, sub_id=subscription_created.subscription_id)

            return subscription

        latest_subscription = max(subscriptions, key=lambda sub: sub.end_date or datetime.min)
        subscription_id = latest_subscription.subscription_id
        end_date = latest_subscription.end_date

        if end_date and end_date > datetime.utcnow():
            new_end_date = end_date + timedelta(days=days)
        else:
            new_end_date = max(datetime.utcnow(), end_date or datetime.utcnow()) + timedelta(days=days)

        await session_methods.subscription.update_sub(
            subscription_id=subscription_id,
            end_date=new_end_date,
            status=SubscriptionStatusEnum.ACTIVE,
            reminder_sent=0
        )
        await update_keys(user_id, subscription_id, True)
        return latest_subscription

    except Exception as e:
        await logger.log_error(f"Error extending or creating user subscription, ID {user_id}", e)
        raise Exception("Ошибка при продлении или создании подписки.")
