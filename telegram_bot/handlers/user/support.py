from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU

router = Router()


@router.message(Command(commands='help'))
async def get_support(message: Message):
    await message.answer(
        text=LEXICON_RU['help_message'],
        reply_markup=await InlineKeyboards.get_support(),
    )


@router.callback_query(lambda c: c.data == 'help_wizards_callback')
async def callback_get_support(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    back_target = data.get('back_target', 'main_menu')
    await callback.message.edit_text(
        text=LEXICON_RU['help_message'],
        reply_markup=await InlineKeyboards.get_support(back_target),
    )


@router.callback_query(lambda c: c.data == 'faq')
async def handle_back_to_support_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['faq_intro'],
        reply_markup=await InlineKeyboards.get_faq_keyboard()
    )


@router.callback_query(lambda c: c.data == 'back_to_support_menu')
async def handle_back_to_support_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['help_message'],
        reply_markup=await InlineKeyboards.get_support()
    )


@router.callback_query(lambda c: c.data == 'support_callback')
async def handle_subscribe(callback: CallbackQuery):
    """Обработчик кнопки 'Оформить подписку' в главном меню."""
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['help_message'],
        reply_markup=await InlineKeyboards.get_support()
    )


@router.callback_query(lambda c: c.data == 'faq_change_territory')
async def handle_change_territory(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU["faq_change_territory"],
        reply_markup=await InlineKeyboards.get_back_to_faq_keyboard('faq_change_territory')
    )


@router.callback_query(lambda c: c.data == 'faq_payment')
async def handle_payment(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU["faq_payment"],
        reply_markup=await InlineKeyboards.get_back_to_faq_keyboard('faq_payment')
    )


@router.callback_query(lambda c: c.data == 'faq_slow_internet')
async def handle_slow_internet(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU["faq_slow_internet"],
        reply_markup=await InlineKeyboards.get_back_to_faq_keyboard('faq_slow_internet')
    )


@router.callback_query(lambda c: c.data == 'faq_install_amulet')
async def handle_install_amulet(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU["faq_install_amulet"],
        reply_markup=await InlineKeyboards.get_back_to_faq_keyboard('faq_install_amulet')
    )
