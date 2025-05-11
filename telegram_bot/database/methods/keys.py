from typing import List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Keys


class KeysMethods:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_key(self, key: Keys):
        try:
            self.session.add(key)
            await self.session.flush()
            return key
        except SQLAlchemyError as e:
            await logger.log_error(f"Error creating key", e)
            return False

    async def get_key_by_key_id(self, key_id: int):
        try:
            result = await self.session.execute(select(Keys).where(Keys.key_id == key_id))
            key = result.scalars().first()
            return key
        except SQLAlchemyError as e:
            await logger.log_error(f"Error getting key by ID", e)
            return False

    async def get_key_by_id(self, id: int) -> Keys:
        try:
            result = await self.session.execute(select(Keys).where(Keys.id == id))
            key = result.scalars().first()
            return key
        except SQLAlchemyError as e:
            await logger.log_error(f"Error getting key by ID", e)

    async def get_all_keys(self) -> List[Keys]:
        try:
            result = await self.session.execute(select(Keys))
            keys = result.scalars().all()
            return keys
        except SQLAlchemyError as e:
            await logger.log_error(f"Error getting all keys", e)
            return False

    async def delete_key(self, id: int):
        try:
            result = await self.session.execute(select(Keys).where(Keys.id == id))
            key = result.scalars().first()

            if key:
                await self.session.delete(key)
                return True
            return False

        except SQLAlchemyError as e:
            await logger.log_error(f"Error deleting key", e)
            return False

    async def update_key(self, id: int, **kwargs):
        try:
            result = await self.session.execute(select(Keys).where(Keys.id == id))
            key = result.scalars().first()

            if key:
                for field, value in kwargs.items():
                    setattr(key, field, value)

                self.session.add(key)

            return key

        except SQLAlchemyError as e:
            await logger.log_error(f"Error updating key", e)