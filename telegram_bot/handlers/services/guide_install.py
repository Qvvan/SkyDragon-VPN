from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory
from lexicon.lexicon_ru import guide_install
from logger.logging_config import logger

router = Router()


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'get_guide_install_app'))
async def back_to_device_selection(callback_query: CallbackQuery, state: FSMContext,
                                   callback_data: SubscriptionCallbackFactory):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.log_error(f"Не удалось удалить сообщение с ID {previous_message_id}", e)

    name_app = callback_data.name_app
    await callback_query.message.edit_text(
        text="Выбери своё устройство",
        reply_markup=await InlineKeyboards.get_menu_install_app(name_app)
    )
    await callback_query.answer()


@router.callback_query(SubscriptionCallbackFactory.filter())
async def get_install_android(callback_query: CallbackQuery, callback_data: SubscriptionCallbackFactory):
    name_device = callback_data.action
    name_app = callback_data.name_app
    await callback_query.message.edit_text(
        text=guide_install[name_app][name_device],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=SubscriptionCallbackFactory(action='get_guide_install_app', name_app=name_app).pack()
                )
            ]
        ]),
        parse_mode="Markdown"
    )
    await callback_query.answer()
