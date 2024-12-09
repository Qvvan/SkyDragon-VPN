from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import ADMIN_IDS
from filters.admin import IsAdmin
from keyboards.kb_inline import InlineKeyboards
from state.state import GetUser

router = Router()


@router.message(Command(commands='get_user'), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await message.answer(
        text='Отправьте ID пользователя',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(GetUser.waiting_user_id)


@router.message(GetUser.waiting_user_id)
async def user_info(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        user_id = int(message.text)

        try:
            user = await message.bot.get_chat(user_id)
        except TelegramBadRequest:
            await message.reply("Ошибка: Пользователь с таким ID не найден!")
            return

        await message.reply(
            text=f"Пользователь 👇",
            reply_markup=await InlineKeyboards.get_user_info(user_id)
        )
    except ValueError:
        await message.reply("Пожалуйста, введите корректное числовое значение user_id.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")
