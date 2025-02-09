from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory
from lexicon.lexicon_ru import guide_install, LEXICON_RU
from logger.logging_config import logger

router = Router()


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'get_guide_install_app'))
async def back_to_device_selection(
        callback_query: CallbackQuery, state: FSMContext,
        callback_data: SubscriptionCallbackFactory
):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")

    # Функция для безопасного удаления сообщений
    async def delete_message_safe(message_id):
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, message_id)
        except Exception as e:
            # Логирование ошибки, если сообщение не найдено
            await logger.info(f"Не удалось удалить сообщение с ID {message_id}")

    if previous_message_id:
        await delete_message_safe(previous_message_id)
        await state.update_data(text_dragons_overview_id=None)

    subscription_id = callback_data.subscription_id
    await callback_query.message.edit_text(
        text="Выбери своё устройство",
        reply_markup=await InlineKeyboards.get_menu_install_app(subscription_id)
    )
    await callback_query.answer()


@router.callback_query(SubscriptionCallbackFactory.filter())
async def get_install_android(callback_query: CallbackQuery, callback_data: SubscriptionCallbackFactory,
                              state: FSMContext):
    name_device = callback_data.action
    subscription_id = callback_data.subscription_id
    async with DatabaseContextManager() as session_methods:
        try:
            subscription = await session_methods.subscription.get_subscription_by_id(subscription_id)
            if not subscription:
                await callback_query.answer(LEXICON_RU["not_found_subscription"], show_alert=True, cache_time=5)
                return

            await callback_query.answer()
            config_link = subscription.config_link
            show_guide_message = await callback_query.message.edit_text(
                text=guide_install[name_device].format(key=config_link),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data=SubscriptionCallbackFactory(
                                    action='get_guide_install_app',
                                    subscription_id=subscription_id,
                                ).pack()
                            )
                        ]
                    ]
                ),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            await state.update_data(show_guide_message=show_guide_message.message_id)
        except Exception as e:
            await logger.log_error(f"Не удалось получить подписку при показе инструкции {callback_query.from_user.id}",
                                   e)
