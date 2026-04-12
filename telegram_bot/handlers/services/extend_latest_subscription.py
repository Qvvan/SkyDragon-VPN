from datetime import datetime, timedelta

from handlers.services.create_subscription_service import SubscriptionService
from logger.logging_config import logger
from models.models import Subscriptions, SubscriptionStatusEnum


class NoAvailableServersError(Exception):
    pass


async def extend_user_subscription(
    user_id: int,
    username: str,
    days: int,
    session_methods,
    service_id: int = 0,
) -> tuple[Subscriptions, bool]:
    """
    Продлевает самую позднюю подписку пользователя на `days` дней.
    Если подписок нет — создаёт новую.

    Возвращает: (subscription, is_new)
        is_new=True  → создана новая подписка (нужен action='create')
        is_new=False → продлена существующая (нужен action='enable')
    """
    try:
        subscriptions = await session_methods.subscription.get_subscription(user_id)

        if not subscriptions:
            subscription = Subscriptions(
                user_id=user_id,
                service_id=service_id,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=days)
            )
            created = await SubscriptionService.create_subscription(subscription, session_methods)
            if not created:
                raise Exception("Ошибка создания подписки")
            return created, True

        latest = max(subscriptions, key=lambda s: s.end_date or datetime.min)

        if latest.end_date and latest.end_date > datetime.utcnow():
            new_end_date = latest.end_date + timedelta(days=days)
        else:
            new_end_date = datetime.utcnow() + timedelta(days=days)

        await session_methods.subscription.update_sub(
            subscription_id=latest.subscription_id,
            end_date=new_end_date,
            status=SubscriptionStatusEnum.ACTIVE,
            reminder_sent=0,
        )
        # Возвращаем объект с обновлённым end_date (для отображения пользователю)
        latest.end_date = new_end_date
        return latest, False

    except Exception as e:
        await logger.log_error(f"Ошибка при продлении/создании подписки для user_id={user_id}", e)
        raise Exception("Ошибка при продлении или создании подписки.")
