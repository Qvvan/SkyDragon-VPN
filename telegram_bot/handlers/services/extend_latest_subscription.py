from datetime import datetime, timedelta

from handlers.services.active_servers import get_active_server_and_key
from handlers.services.create_subscription_service import SubscriptionService
from logger.logging_config import logger


class NoAvailableServersError(Exception):
    pass


async def extend_user_subscription(user_id: int, days: int, session_methods):
    """
    Продлевает текущую подписку пользователя или создает новую, если подписка отсутствует.

    Args:
        user_id (int): ID пользователя.
        days (int): Количество дней для продления или создания подписки.
        session_methods (DatabaseContextManager): Контекст базы данных для транзакции.

    Returns:
        str: Сообщение об успешном продлении или создании подписки.
    """
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

            end_date = datetime.utcnow() + timedelta(days=days)
            subscription_created = await SubscriptionService.create_subscription(
                user_id=user_id,
                service_id=0,
                durations_days=days,
                key=key,
                key_id=key_id,
                server_ip=server_ip,
                session_methods=session_methods
            )
            if not subscription_created:
                raise Exception("Ошибка создания подписки")

            await session_methods.session.commit()
            return f"Создана новая подписка на {days} дней, до {end_date.strftime('%Y-%m-%d %H:%M:%S')}"

        latest_subscription = max(subscriptions, key=lambda sub: sub.end_date or datetime.min)
        subscription_id = latest_subscription.subscription_id
        end_date = latest_subscription.end_date

        if end_date and end_date > datetime.utcnow():
            new_end_date = end_date + timedelta(days=days)
        else:
            new_end_date = max(datetime.utcnow(), end_date or datetime.utcnow()) + timedelta(days=days)

        await session_methods.subscription.update_sub(subscription_id, end_date=new_end_date)

        return f"Подписка продлена до {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}"

    except Exception as e:
        await logger.log_error("Error extending or creating user subscription", e)
        return "Ошибка при продлении или создании подписки."
