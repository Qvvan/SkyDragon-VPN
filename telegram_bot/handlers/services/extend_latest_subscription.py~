from datetime import datetime, timedelta

from sqlalchemy.sql.functions import now

from handlers.services.active_servers import get_active_server_and_key
from handlers.services.create_subscription_service import SubscriptionService
from logger.logging_config import logger
from models.models import Subscriptions, NameApp


class NoAvailableServersError(Exception):
    pass


async def extend_user_subscription(user_id: int, days: int, session_methods):
    try:
        # Получаем все подписки пользователя
        subscriptions = await session_methods.subscription.get_subscription(user_id)

        # Если нет активных подписок, создаем новую подписку на заданное количество дней
        if not subscriptions:
            shadowsocks_manager, server_ip, key, key_id = await get_active_server_and_key(
                    user_id, 'Пробный период', session_methods
                    )

            if not server_ip or not key or not key_id:
                await logger.log_error(
                        message=f"Пользователь c ID: {user_id} попытался оформить пробную подписку, но ни один сервер не ответил",
                        error="Не удалось получить сессию ни по одному из серверов"
                        )
                raise NoAvailableServersError("нет доступных серверов")

            subscription = Subscriptions(
                user_id=user_id,
                service_id=0,
                key=key,
                key_id=key_id,
                server_ip=server_ip,
                name_app=NameApp.OUTLINE,
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

        if end_date and end_date > datetime.utcnow():
            new_end_date = end_date + timedelta(days=days)
        else:
            new_end_date = max(datetime.utcnow(), end_date or datetime.utcnow()) + timedelta(days=days)

        await session_methods.subscription.update_sub(subscription_id, end_date=new_end_date)

        return latest_subscription

    except Exception as e:
        await logger.log_error("Error extending or creating user subscription", e)
        raise "Ошибка при продлении или создании подписки."
