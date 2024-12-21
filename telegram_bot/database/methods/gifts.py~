from sqlalchemy import select, desc, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Gifts


class GiftsMethods:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_gifts(self):
        try:
            result = await self.session.execute(select(Gifts).order_by(desc(Gifts.gift_id)))
            gifts = result.scalars().all()
            return gifts
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получение подарков", e)
            return

    async def add_gift(self, gift: Gifts):
        try:
            self.session.add(gift)
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка добавления подарка", e)
            return

    async def update_gift(self, gift_id: int, **kwargs):
        try:
            stmt = update(Gifts).where(Gifts.gift_id == gift_id).values(**kwargs)
            await self.session.execute(stmt)
            return True
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка обновления подарка", e)
            return

    async def get_gift_by_username(self, username: str):
        try:
            result = await self.session.execute(select(Gifts).filter_by(username=username))
            gift = result.scalars().all()
            return gift
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получения подарка", e)
            return
