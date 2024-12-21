from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU

router = Router()


@router.message(Command(commands="main_menu"))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(back_target='main_menu')
    await message.answer(
            text=LEXICON_RU['main_menu'],
            reply_markup=await InlineKeyboards.main_menu(),
            parse_mode="Markdown"
            )


@router.callback_query(lambda c: c.data == 'main_menu')
async def handle_know_more(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(back_target='main_menu')
    await callback.message.edit_text(
            text=LEXICON_RU['main_menu'],
            reply_markup=await InlineKeyboards.main_menu(),
            parse_mode="Markdown"
            )