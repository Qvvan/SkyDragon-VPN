from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.types import Update, ReplyKeyboardRemove

from database.context_manager import DatabaseContextManager
from database.methods.users import LogicError
from logger.logging_config import logger


class MessageLoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and not event.from_user.is_bot:
            user_id = event.chat.id
            username = event.chat.username
            await logger.info(f"Пользователь {username} (ID: {user_id}) отправил сообщение: {event.text}")
            await last_visit(user_id)

        return await handler(event, data)


class CallbackLoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, CallbackQuery) and not event.from_user.is_bot:
            user_id = event.from_user.id
            username = event.from_user.username
            button_text = event.data
            await logger.info(f"Пользователь {username} (ID: {user_id}) нажал кнопку: {button_text}")
            await last_visit(user_id)

        return await handler(event, data)


async def last_visit(user_id: int):
    async with DatabaseContextManager() as session:
        try:
            result = await session.users.update_user(user_id, last_visit=datetime.utcnow())
            if isinstance(result, LogicError):
                await logger.log_error("Error updating last visit", result)
        except Exception as e:
            await session.session.rollback()
            await logger.log_error("Error updating last visit", e)