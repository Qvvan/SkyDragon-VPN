from sqlalchemy import select, desc, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Payments


class PaymentsMethods:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_payments(self):
        try:
            result = await self.session.execute(
                select(Payments).order_by(desc(Payments.payment_id))
            )
            payments = result.scalars().all()
            return payments
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения списка платежей", e)
            return []

    async def get_payment_by_id(self, payment_id: str):
        try:
            result = await self.session.execute(
                select(Payments).filter(Payments.payment_id == payment_id)
            )
            payment = result.scalar_one_or_none()
            return payment
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения платежа по ID", e)
            return None

    async def create_payments(self, payment: Payments):
        try:
            self.session.add(payment)
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка создания платежа", e)
            return False

    async def get_unpaid_payments(self):
        try:
            result = await self.session.execute(
                select(Payments).filter(Payments.status == 'pending')
            )
            payments = result.scalars().all()
            return payments
        except SQLAlchemyError as e:
            await logger.log_error(f"Error getting unpaid payments", e)
            return []

    async def update_payment_status(self, payment_id: str, status: str):
        try:
            stmt = update(Payments).where(Payments.payment_id == payment_id).values(status=status)
            await self.session.execute(stmt)
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Error updating payment status", e)
            return False

    async def delete_payment(self, payment_id: str):
        try:
            payment = await self.session.get(Payments, payment_id)
            if payment:
                await self.session.delete(payment)
                return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Error deleting payment", e)
            return False
