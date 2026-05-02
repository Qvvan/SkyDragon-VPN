from sqlalchemy import select, desc, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Gifts


class GiftsMethods:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_gifts(self, user_id: int = None):
        try:
            query = select(Gifts).order_by(desc(Gifts.gift_id))

            if user_id is not None:
                query = query.where(Gifts.recipient_user_id == user_id)

            result = await self.session.execute(query)
            gifts = result.scalars().all()
            return gifts
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получение подарков", e)
            return []

    async def add_gift(self, gift: Gifts) -> Gifts | None:
        try:
            self.session.add(gift)
            await self.session.flush()
            return gift
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка добавления подарка", e)
            return None

    async def update_gift(self, gift_id: int, **kwargs):
        try:
            stmt = update(Gifts).where(Gifts.gift_id == gift_id).values(**kwargs)
            await self.session.execute(stmt)
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка обновления подарка", e)
            return None

    async def get_gift_by_id(self, gift_id: int) -> Gifts | None:
        try:
            result = await self.session.execute(select(Gifts).filter_by(gift_id=gift_id))
            gift = result.scalars().first()
            return gift
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения подарка", e)
            return

    async def get_pending_gifts(self):
        try:
            result = await self.session.execute(select(Gifts).filter_by(status="pending"))
            gift = result.scalars().all()
            return gift
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения подарка", e)
            return []

    async def get_undelivered_gifts(self):
        """pending или старый awaiting_activation — к зачислению, когда получатель уже в users."""
        try:
            result = await self.session.execute(
                select(Gifts).where(Gifts.status.in_(["pending", "awaiting_activation"]))
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения подарков к доставке", e)
            return []

    async def get_pending_gifts_for_recipient(self, recipient_user_id: int):
        try:
            result = await self.session.execute(
                select(Gifts).where(
                    Gifts.recipient_user_id == recipient_user_id,
                    Gifts.status.in_(["pending", "awaiting_activation"]),
                )
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения подарков получателя", e)
            return []