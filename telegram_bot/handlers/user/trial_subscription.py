from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.user.subs import show_user_subscriptions
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

router = Router()


@router.callback_query(lambda callback: callback.data == "activate_trial")
async def process_trial_subscription_callback(callback: CallbackQuery, state: FSMContext):
    async with DatabaseContextManager() as session_methods:
        try:
            user = await session_methods.users.get_user(user_id=callback.from_user.id)
            if not user.trial_used:
                await extend_user_subscription(user.user_id, 7, session_methods)
                await session_methods.users.update_user(user_id=callback.from_user.id, trial_used=True)
                await session_methods.session.commit()
                await callback.answer(
                    text=LEXICON_RU['trial_activated'], show_alert=True, cache_time=3
                )
                await show_user_subscriptions(
                    user_id=callback.from_user.id,
                    username=callback.from_user.username,
                    message=callback.message,
                    state=state
                )
            else:
                await callback.message.edit_text(
                    text=LEXICON_RU['trial_subscription_used'],
                    reply_markup=await InlineKeyboards.get_subscriptions_keyboard()
                )
        except Exception as error:
            await session_methods.session.rollback()
            await logger.log_error(
                f"Ошибка при создании пробной подписки для пользователя с ID: {callback.from_user.id}", error)
            await callback.message.answer(text=LEXICON_RU['error'])
