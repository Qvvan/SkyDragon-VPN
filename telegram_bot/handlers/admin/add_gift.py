from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.extend_latest_subscription import extend_user_subscription
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import Users
from state.state import GiveSub

router = Router()


@router.message(Command(commands=['add_gift', 'grant_sub']), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await message.answer(
        text='Введите Telegram ID пользователя, которому хотите выдать подписку:',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(GiveSub.waiting_username)


@router.message(GiveSub.waiting_username)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        if user_id <= 0:
            raise ValueError

        await state.update_data(user_id=user_id)
        await message.answer(
            text='Введите количество дней подписки:',
            reply_markup=await InlineKeyboards.cancel()
        )
        await state.set_state(GiveSub.waiting_duration_days)
    except ValueError:
        await message.answer('Некорректный Telegram ID. Введите положительное число.')


@router.message(GiveSub.waiting_duration_days)
async def process_duration_days(message: types.Message, state: FSMContext):
    try:
        duration_days = int(message.text)
        if duration_days <= 0:
            raise ValueError

        data = await state.get_data()
        user_id = data.get('user_id')

        async with DatabaseContextManager() as session_methods:
            user = await session_methods.users.get_user(user_id)
            user_was_created = False
            if not user:
                user = Users(user_id=user_id, username=None)
                if await session_methods.users.add_user(user):
                    user_was_created = True

            subscription = await extend_user_subscription(user_id, user.username, duration_days, session_methods)
            await session_methods.subscription_history.create_history_entry(
                user_id=user_id,
                service_id=subscription.service_id,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                status="gift"
            )
            await session_methods.session.commit()

            try:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=LEXICON_RU['add_gift_success'].format(duration_days=duration_days),
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🐉 Мои подписки",
                                    callback_data="view_subs"
                                )
                            ],
                        ]
                    )
                )
            except Exception:
                await logger.warning(
                    f"Не удалось отправить уведомление пользователю с ID: {user_id}. "
                    "Вероятно, пользователь еще не запускал бота."
                )

            await logger.log_info(
                f"Администрация выдала подписку пользователю ID: {user_id}\n"
                f"Дней: {duration_days}\n"
                f"Профиль создан: {'да' if user_was_created else 'нет'}"
            )
            if user_was_created:
                await message.answer(
                    'Пользователь отсутствовал в БД, профиль создан. Подписка успешно выдана.'
                )
            else:
                await message.answer('Подписка успешно выдана.')

    except ValueError:
        await message.answer('Некорректное количество дней. Введите положительное число.')

    await state.clear()
