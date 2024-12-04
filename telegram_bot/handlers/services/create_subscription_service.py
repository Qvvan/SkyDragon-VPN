from datetime import datetime, timedelta
from typing import Optional

from logger.logging_config import logger
from models.models import NameApp, StatusSubscriptionHistory, Subscriptions


class SubscriptionService:

    @staticmethod
    async def create_subscription(subscription: Subscriptions, session_methods) -> Optional[Subscriptions]:
        """
        Создает подписку и добавляет запись в историю подписок.

        :param subscription: Готовый объект подписки.
        :param session_methods: Методы сессии для работы с базой данных.
        :return: Успешность операции.
        """
        try:
            subscription_id = await session_methods.subscription.create_sub(subscription)
            if not subscription_id:
                return None

            await session_methods.subscription_history.create_history_entry(
                user_id=subscription.user_id,
                service_id=subscription.service_id,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                status=StatusSubscriptionHistory.NEW_SUBSCRIPTION
            )

            return subscription_id

        except Exception as e:
            await logger.log_error(
                f"Ошибка при создании подписки для пользователя ID: {subscription.user_id}", e
            )
            return None
