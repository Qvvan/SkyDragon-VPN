from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.guide_install import back_to_device_selection
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

router = Router()


@router.callback_query(lambda callback: callback.data == "activate_trial")
async def process_trial_subscription_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text=callback.message.text,
        reply_markup=None
    )
    async with DatabaseContextManager() as session_methods:
        try:
            user = await session_methods.users.get_user(user_id=callback.from_user.id)
            if not user.trial_used:
                await callback.answer(
                    text="Активируем пробную подписку...",
                )
                subscription = await extend_user_subscription(
                    user_id=user.user_id,
                    username=callback.from_user.username,
                    days=5,
                    session_methods=session_methods,
                )
                if subscription:
                    await back_to_device_selection(
                        callback_query=callback,
                        state=state,
                        callback_data=SubscriptionCallbackFactory(
                            action='get_guide_install_app',
                            subscription_id=subscription.subscription_id,
                        )
                    )
                    await logger.log_info(
                        f"Пользователь @{callback.from_user.username}\n"
                        f"ID: {callback.from_user.id}\n"
                        f"Активировал(а) пробную подписку")
                    await session_methods.users.update_user(user_id=callback.from_user.id, trial_used=True)
                    await session_methods.session.commit()
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
