from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory
from lexicon.lexicon_ru import guide_install
from logger.logging_config import logger

router = Router()


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'get_guide_install_app'))
async def back_to_device_selection(
        callback_query: CallbackQuery, state: FSMContext,
        callback_data: SubscriptionCallbackFactory
        ):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    show_slow_internet_id = data.get("show_slow_internet")
    if show_slow_internet_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, show_slow_internet_id)
            await state.update_data(show_slow_internet_id=None)
        except Exception as e:
            await logger.error(f"Не удалось удалить сообщение с ID {show_slow_internet_id}", e)

    if previous_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.error(f"Не удалось удалить сообщение с ID {previous_message_id}", e)
    name_app = callback_data.name_app
    subscription_id = callback_data.subscription_id
    await callback_query.message.edit_text(
            text="Выбери своё устройство",
            reply_markup=await InlineKeyboards.get_menu_install_app(name_app, subscription_id)
            )
    await callback_query.answer()


@router.callback_query(SubscriptionCallbackFactory.filter())
async def get_install_android(callback_query: CallbackQuery, callback_data: SubscriptionCallbackFactory, state: FSMContext):
    await callback_query.answer()
    name_device = callback_data.action
    name_app = callback_data.name_app
    subscription_id = callback_data.subscription_id
    async with DatabaseContextManager() as session_methods:
        try:
            subsciption = await session_methods.subscription.get_subscription_by_id(subscription_id)
            user_key = subsciption.key
            show_guide_message = await callback_query.message.edit_text(
                    text=guide_install[name_app][name_device].format(key=user_key),
                    reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                            text="🔙 Назад",
                                            callback_data=SubscriptionCallbackFactory(
                                                    action='get_guide_install_app',
                                                    subscription_id=subscription_id,
                                                    name_app=name_app
                                                    ).pack()
                                            )
                                    ]
                                ]
                            ),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                    )
            show_slow_internet = await callback_query.message.answer(
                text="Если у вас плохо грузит VPN, попробуйте сменить локацию 👇.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🐉 Мои подписки",
                                callback_data="view_subs"
                            )
                        ],
                ])
            )
            await state.update_data(show_guide_message=show_guide_message.message_id)
            await state.update_data(show_slow_internet=show_slow_internet.message_id)
        except Exception as e:
            await logger.log_error(f"Не удалось получить подписку при показе инструкции {callback_query.from_user.id}", e)
