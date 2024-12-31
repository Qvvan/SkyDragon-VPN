from typing import Union

from sqlalchemy.orm import selectinload
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from logger.logging_config import logger
from models.models import Users


class Result:
    """Базовый класс для результата операции."""


class Success(Result):
    """Класс для успешного результата, содержащий обновленного пользователя."""

    def __init__(self, user):
        self.user = user


class NotFoundError(Result):
    """Класс для результата, указывающего, что пользователь не найден."""

    def __init__(self, user_id: int, message: str = "User not found"):
        self.user_id = user_id
        self.message = message


class LogicError(Result):
    """Класс для логической ошибки, указывающей на некорректную логику."""

    def __init__(self, message: str = "Logic error in update operation"):
        self.message = message


class UserMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int):
        try:
            result = await self.session.execute(select(Users).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user
        except SQLAlchemyError as e:
            await logger.log_error(f"Error checking if user exists", e)
            return False

    async def add_user(self, user: Users):
        try:
            if not await self.get_user(user.user_id):
                self.session.add(user)
                return True
            return False
        except IntegrityError as e:
            await logger.log_error(f"Error adding user", e)
        except SQLAlchemyError as e:
            await logger.log_error(f"Error adding user", e)

    async def ban_user(self, user_id: int):
        try:
            if await self.get_user(user_id):
                stmt = update(Users).where(Users.user_id == user_id).values(ban=1)
                await self.session.execute(stmt)
                return True

            return False
        except Exception as e:
            await logger.log_error(f"Error banning user", e)

    async def unban_user(self, user_id: int):
        try:
            if await self.get_user(user_id):
                stmt = update(Users).where(Users.user_id == user_id).values(ban=0)
                await self.session.execute(stmt)
                return True

            return False
        except Exception as e:
            await logger.log_error(f"Error unbanning user", e)

    async def get_all_users(self):
        try:
            result = await self.session.execute(
                select(Users).options(selectinload(Users.trial_used), selectinload(Users.created_at))
            )
            users = result.scalars().all()
            return users
        except SQLAlchemyError as e:
            await logger.log_error("Error fetching all users", e)
            return []

    async def update_user(self, user_id: int, **kwargs) -> Union[Success, NotFoundError, LogicError]:
        try:
            user = await self.get_user(user_id)
            if not user:
                return NotFoundError(user_id)  # Пользователь не найден

            # Проверка логики: допустим, обновление не выполняется, если `kwargs` пустой
            if not kwargs:
                return LogicError("No fields provided for update")  # Логическая ошибка

            stmt = update(Users).where(Users.user_id == user_id).values(**kwargs)
            await self.session.execute(stmt)
            await self.session.commit()  # Сохраняем изменения

            # Получаем обновленного пользователя
            updated_user = await self.get_user(user_id)
            return Success(updated_user)
        except SQLAlchemyError as e:
            await logger.log_error("Database error during user update", e)
            return LogicError("Database error occurred")

    async def get_user_by_username(self, username: str):
        try:
            result = await self.session.execute(select(Users).filter_by(username=username))
            user = result.scalars().first()
            return user
        except SQLAlchemyError as e:
            await logger.log_error(f"Error checking if user exists", e)
            return False
