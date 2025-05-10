from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from logger.logging_config import logger
from models.models import Subscriptions, Services, SubscriptionStatusEnum, Servers


class SubscriptionMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_subscription(self, user_id):
        try:
            # Внешнее соединение для серверов и услуг, чтобы не зависеть от наличия данных в связанных таблицах
            query = (
                select(
                    Subscriptions.start_date,
                    Subscriptions.end_date,
                    Subscriptions.config_link,
                    Subscriptions.key_ids,
                    Services.name,
                    Subscriptions.status,
                    Subscriptions.subscription_id,
                    Subscriptions.created_at,
                    Services.duration_days,
                    Subscriptions.auto_renewal,
                    Subscriptions.card_details_id,
                    Services.price,
                    Services.service_id,
                )
                .select_from(Subscriptions)
                .outerjoin(Services, Subscriptions.service_id == Services.service_id)
                .filter(Subscriptions.user_id == user_id)
            )

            result = await self.session.execute(query)
            subscription = result.mappings().all()

            if not subscription:
                return None

            return subscription
        except SQLAlchemyError as e:
            await logger.log_error(f"Error retrieving subscription", e)
            return None

    async def update_sub(self, subscription_id: int, **kwargs):
        """
        Универсальное обновление подписки в базе данных.
        subscription_id: int - ID подписки, которую необходимо обновить
        kwargs: dict - поля для обновления и их значения
        """
        try:
            result = await self.session.execute(
                select(Subscriptions).filter_by(subscription_id=subscription_id)
            )
            existing_sub = result.scalars().first()

            if existing_sub:
                kwargs['updated_at'] = datetime.utcnow()
                for field, value in kwargs.items():
                    setattr(existing_sub, field, value)

                self.session.add(existing_sub)

            return True

        except SQLAlchemyError as e:
            await logger.log_error(f"Error updating subscription {subscription_id}", e)
            raise

    async def create_sub(self, sub: Subscriptions) -> int:
        try:
            self.session.add(sub)
            await self.session.flush()
            return sub
        except SQLAlchemyError as e:
            await logger.log_error(f"Error creating subscription", e)
            return False

    async def get_subs(self) -> List[Subscriptions]:
        try:
            result = await self.session.execute(
                select(Subscriptions)
            )
            subs = result.scalars().all()

            return subs
        except SQLAlchemyError as e:
            await logger.log_error('Не удалось получить подписки', e)
            return []

    async def delete_sub(self, subscription_id: int):
        try:
            subscription = await self.session.get(Subscriptions, subscription_id)

            if subscription:
                await self.session.delete(subscription)
                return True
            return False

        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка при удалении подписки с ID {subscription_id}", e)
            raise

    async def get_active_subscribed_users(self):
        try:
            result = await self.session.execute(
                select(Subscriptions.user_id)
                .where(Subscriptions.status == SubscriptionStatusEnum.ACTIVE)
            )
            return result.scalars().all()
        except SQLAlchemyError as e:
            await logger.log_error("Error fetching active subscribed users", e)
            return []

    async def get_subscription_by_id(self, subscription_id: int):
        try:
            query = (
                select(
                    Subscriptions.start_date,
                    Subscriptions.end_date,
                    Subscriptions.config_link,
                    Subscriptions.key_ids,
                    Services.name,
                    Subscriptions.status,
                    Subscriptions.subscription_id,
                    Subscriptions.card_details_id,
                    Subscriptions.auto_renewal,
                    Subscriptions.created_at,
                    Services.duration_days,
                    Services.price,
                    Services.service_id,
                )
                .select_from(Subscriptions)
                .outerjoin(Services, Subscriptions.service_id == Services.service_id)
                .filter(Subscriptions.subscription_id == subscription_id)
            )

            result = await self.session.execute(query)
            subscription = result.mappings().first()

            return subscription
        except SQLAlchemyError as e:
            await logger.log_error(f"Error retrieving subscription", e)
            return None
