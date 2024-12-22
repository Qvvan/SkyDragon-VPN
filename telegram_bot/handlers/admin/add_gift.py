from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.extend_latest_subscription import extend_user_subscription
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from state.state import GiveSub

router = Router()



# Команда для добавления подписки
@router.message(Command(commands='add_gift'), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await message.answer(
        text='Напишите user_id, кому хотите подарить подписку',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(GiveSub.waiting_username)


@router.message(GiveSub.waiting_username)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)  # Проверяем, что введён user_id - число
        await state.update_data(user_id=user_id)  # Сохраняем user_id в состоянии
        await message.answer(
            text='Введите количество дней подписки:',
            reply_markup=await InlineKeyboards.cancel()
        )
        await state.set_state(GiveSub.waiting_duration_days)
    except ValueError:
        await message.answer('Некорректный user_id. Попробуйте снова.')


@router.message(GiveSub.waiting_duration_days)
async def process_duration_days(message: types.Message, state: FSMContext):
    try:
        duration_days = int(message.text)
        data = await state.get_data()
        user_id = data.get('user_id')

        async with DatabaseContextManager() as session_methods:
            user = await session_methods.users.get_user(user_id)
            if not user:
                await message.answer('Пользователь не найден. Попробуйте снова.')
            else:
                await extend_user_subscription(user_id, user.username, duration_days, session_methods)
                await message.bot.send_message(chat_id=user_id, text=LEXICON_RU['add_gift_success'].format(duration_days=duration_days),
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
                await session_methods.session.commit()
                await message.answer('Подписка успешно подарена')

    except ValueError:
        await message.answer('Некорректное количество дней. Попробуйте снова.')

    await state.clear()