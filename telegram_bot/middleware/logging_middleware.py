from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.types import Update, ReplyKeyboardRemove

from logger.logging_config import logger
from middleware.trottling import ThrottlingMiddleware


class MessageLoggingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any]
    ) -> Any:
        throttling_middleware: ThrottlingMiddleware = data.get("throttling_middleware")

        if isinstance(event, Message) and not event.from_user.is_bot:
            user_id = event.chat.id
            username = event.chat.username
            await logger.info(f"Пользователь {username} (ID: {user_id}) отправил сообщение: {event.text}")

            sent_message = await event.answer("Пробуждение... 🔄", reply_markup=ReplyKeyboardRemove())
            await sent_message.delete()

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

        return await handler(event, data)
