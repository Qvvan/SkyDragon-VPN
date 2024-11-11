from datetime import datetime, timedelta

from logger.logging_config import logger
from models.models import Subscriptions, NameApp, StatusSubscriptionHistory


class SubscriptionService:

    @staticmethod
    async def create_subscription(
            user_id: int,
            service_id: int,
            durations_days: int,
            key: str,
            key_id,
            server_ip: str,
            session_methods
    ) -> bool:
        try:

            subscription_data = {
                "user_id": user_id,
                "service_id": service_id,
                "key": key,
                "key_id": key_id,
                "server_ip": server_ip,
                "name_app": NameApp.OUTLINE,
                "start_date": datetime.now(),
                "end_date": datetime.now() + timedelta(days=durations_days)
            }

            subscription = Subscriptions(**subscription_data)

            created_subscription = await session_methods.subscription.create_sub(subscription)

            if created_subscription:
                status = StatusSubscriptionHistory.NEW_SUBSCRIPTION
                await session_methods.subscription_history.create_history_entry(
                    user_id=subscription_data["user_id"],
                    service_id=subscription_data["service_id"],
                    start_date=subscription_data["start_date"],
                    end_date=subscription_data["end_date"],
                    status=status
                )
                return True

            return False
        except Exception as e:
            await logger.log_error(f"Пользователь с ID: {user_id}\n"
                                   f"Ошибка при создании подписки", e)
            return False
