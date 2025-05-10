from datetime import datetime, timedelta
from sqlalchemy import select, desc, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Notification


class NotificationMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_notification(self, user_id: int, notification_type: str, subscription_id=None,
                                  message=None, additional_data=None, status="active", created_at=None):
        """Создает новое уведомление"""
        try:
            if created_at is None:
                created_at = datetime.now()

            notification = Notification(
                user_id=user_id,
                subscription_id=subscription_id,
                notification_type=notification_type,
                message=message,
                additional_data=additional_data,
                status=status,
                created_at=created_at,
                updated_at=created_at
            )
            self.session.add(notification)
            await self.session.commit()
            return notification
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка создания уведомления", e)
            return None

    async def get_notification_by_subscription(self, subscription_id: int, notification_type: str):
        """Получает последнее уведомление для конкретной подписки и типа"""
        try:
            result = await self.session.execute(
                select(Notification)
                .filter(
                    Notification.subscription_id == subscription_id,
                    Notification.notification_type == notification_type
                )
                .order_by(desc(Notification.created_at))
                .limit(1)
            )
            notification = result.scalar_one_or_none()
            return notification
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения уведомления по подписке", e)
            return None

    async def get_last_notification(self, user_id: int, notification_type: str):
        """Получает последнее уведомление для пользователя и типа"""
        try:
            result = await self.session.execute(
                select(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.notification_type == notification_type
                )
                .order_by(desc(Notification.created_at))
                .limit(1)
            )
            notification = result.scalar_one_or_none()
            return notification
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения последнего уведомления", e)
            return None

    async def update_notification(self, notification_id: int, status=None, message=None,
                                  additional_data=None, updated_at=None):
        """Обновляет существующее уведомление"""
        try:
            if updated_at is None:
                updated_at = datetime.now()

            values = {"updated_at": updated_at}
            if status:
                values["status"] = status
            if message:
                values["message"] = message
            if additional_data:
                values["additional_data"] = additional_data

            stmt = update(Notification).where(Notification.id == notification_id).values(**values)
            await self.session.execute(stmt)
            await self.session.commit()

            # Получаем обновленное уведомление
            result = await self.session.execute(
                select(Notification).filter(Notification.id == notification_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка обновления уведомления", e)
            return None

    async def mark_as_resolved(self, notification_id: int):
        """Отмечает уведомление как разрешенное"""
        try:
            return await self.update_notification(notification_id, status="resolved")
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка пометки уведомления как разрешенное", e)
            return None

    async def get_active_notifications(self, user_id=None):
        """Получает все активные уведомления (опционально фильтрует по пользователю)"""
        try:
            query = select(Notification).filter(Notification.status == "active")

            if user_id:
                query = query.filter(Notification.user_id == user_id)

            query = query.order_by(desc(Notification.created_at))

            result = await self.session.execute(query)
            notifications = result.scalars().all()
            return notifications
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения активных уведомлений", e)
            return []

    async def delete_old_notifications(self, days=30):
        """Удаляет старые уведомления"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            stmt = delete(Notification).where(Notification.created_at < cutoff_date)
            await self.session.execute(stmt)
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка удаления старых уведомлений", e)
            return False

    async def delete_notification(self, notification_id: int):
        """Удаляет уведомление по id"""
        try:
            result = await self.session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()

            if notification:
                await self.session.delete(notification)
                await self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка удаления уведомления", e)
            return False