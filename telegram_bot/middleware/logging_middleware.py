from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import Update

from database.context_manager import DatabaseContextManager
from database.methods.users import LogicError
from handlers.services.extend_latest_subscription import extend_user_subscription
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
            await last_visit(user_id, username)
            # await gift_with_new_username(event, username, user_id, 'message')

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
            await last_visit(user_id, username)
            # await gift_with_new_username(event, username, user_id, 'callback')

        return await handler(event, data)


async def last_visit(user_id: int, username: str = None):
    async with DatabaseContextManager() as session_methods:
        try:
            result = await session_methods.users.update_user(user_id, last_visit=datetime.utcnow(), username=username)
            await session_methods.session.commit()
            if isinstance(result, LogicError):
                await logger.log_error("Error updating last visit", result)
        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error("Error updating last visit", e)


async def gift_with_new_username(event, username, user_id, status: str):
    async with DatabaseContextManager() as session_methods:
        if status == 'callback':
            event = event.message
        try:
            gifts = await session_methods.gifts.get_gift_by_username(username)
            for gift in gifts:
                if gift.status == "used":
                    continue
                giver = await session_methods.users.get_user(gift.giver_id)
                service = await session_methods.services.get_service_by_id(gift.service_id)
                await extend_user_subscription(user_id, username, service.duration_days,
                                               session_methods)
                await session_methods.gifts.update_gift(gift_id=gift.gift_id, status="used",
                                                        activated_at=datetime.utcnow())
                await event.answer(
                    text=f"🎁 Вам подарок! 🎉\n\n"
                         f"Ваш друг {'@' + giver.username if giver.username else 'Неизвестный пользователь'} решил сделать вам приятный сюрприз! ✨\n\n"
                         f"💪 Защита {service.name}а на {service.duration_days} дней 🛡️\n\n"
                         f"🌐 Подписка уже активирована, для большей информации зайдите в /profile 🔒",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🐉 Мои подписки",
                                callback_data="view_subs"
                            )
                        ],
                    ])
                )
                await session_methods.session.commit()
        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error(
                f'Пользователь: @{username}\n'
                f'ID: {user_id}\n'
                f'При оформление подарка произошла ошибка:', e
            )
