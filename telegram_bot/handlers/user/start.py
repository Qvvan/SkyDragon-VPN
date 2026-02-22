from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from keyboards.kb_inline import InlineKeyboards, BACK_BTN, MAIN_MENU_CB
from keyboards.set_menu import set_main_menu
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import ReferralStatus, Referrals, Users

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await set_main_menu(message.bot, message.from_user.id)
    await message.answer(
        text=LEXICON_RU['start'],
        reply_markup=await InlineKeyboards.get_menu_keyboard(),
        parse_mode="Markdown"
    )
    referrer_id = get_referrer_id(message)

    async with DatabaseContextManager() as session_methods:
        try:
            status_user = await session_methods.users.add_user(
                Users(
                    user_id=message.from_user.id,
                    username=message.from_user.username,
                )
            )
            await session_methods.session.commit()
            if status_user:
                await log_new_user(message)
                if referrer_id:
                    await handle_referral(referrer_id, message)
        except Exception as e:
            await logger.log_error(
                f'Пользователь: @{message.from_user.username}\n'
                f'ID: {message.from_user.id}\n'
                f'При команде /start произошла ошибка:', e
            )


async def handle_referral(referrer_id, message):
    async with DatabaseContextManager() as session_methods:
        try:
            try:
                await message.bot.send_message(
                    referrer_id,
                    f"🐲 Ваш друг {'@' + message.from_user.username if message.from_user.username else ''} "
                    f"присоединился к кругу! Как только друг оплатит подписку, Древние драконы даруют вам бонус силы 🎁",
                    reply_markup=await InlineKeyboards.get_invite_keyboard()
                )
            except:
                await logger.warning(f"Не удалось отправить уведомление пользователю с ID: {referrer_id}")
            await session_methods.referrals.add_referrer(
                referral=Referrals(
                    referrer_id=referrer_id,
                    referred_id=message.from_user.id,
                    invited_username=message.from_user.username,
                    bonus_issued=ReferralStatus.INVITED,
                )
            )
            # await extend_user_subscription(referrer_id, message.from_user.username, 5, session_methods)
            await session_methods.session.commit()
            try:
                await logger.log_info(
                    f"Его пригласил пользователь с ID: {referrer_id}",
                    await InlineKeyboards.get_user_info(referrer_id)
                )
            except:
                await logger.log_info(
                    f"Его пригласил пользователь с ID: {referrer_id}"
                )
        except Exception as e:
            await logger.log_error(f"Ошибка при начислении бонуса за приглашение: {referrer_id}", e)


def get_referrer_id(message):
    command_args = message.text.split()
    referrer_id = int(command_args[1]) if len(command_args) > 1 and command_args[1].isdigit() and int(
        command_args[1]) != message.from_user.id else None

    return referrer_id


async def log_new_user(message: Message):
    """Logs information about a new user."""
    keyboard = await InlineKeyboards.get_user_info(message.from_user.id)
    try:
        await logger.log_info(
            f"New user joined:\n"
            f"Username: @{message.from_user.username}\n"
            f"First name: {message.from_user.first_name}\n"
            f"Last name: {message.from_user.last_name}\n"
            f"ID: {message.from_user.id}",
            keyboard=keyboard
        )
    except:
        await logger.log_info(
            f"New user joined:\n"
            f"Username: @{message.from_user.username}\n"
            f"First name: {message.from_user.first_name}\n"
            f"Last name: {message.from_user.last_name}\n"
            f"ID: {message.from_user.id}",
        )


@router.callback_query(lambda c: c.data == 'back_to_start')
async def handle_know_more(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать больше'."""
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['start'],
        reply_markup=await InlineKeyboards.get_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == 'referal_subs')
async def handle_know_more(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать больше'."""
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['invite_info'],
        reply_markup=await InlineKeyboards.get_invite_keyboard(MAIN_MENU_CB)
    )


@router.callback_query(lambda c: c.data == 'dragon_legends')
async def handle_know_more(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Легенда о драконах'."""
    await callback.answer()

    await state.update_data(back_target='dragon_legends')

    await callback.message.edit_text(
        text=LEXICON_RU['legend'],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Оформить подписку", callback_data="subscribe")],
                [InlineKeyboardButton(text=BACK_BTN, callback_data=MAIN_MENU_CB)],
            ]
        )
    )


@router.callback_query(lambda c: c.data == 'trial_subs')
async def handle_know_more(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Узнать больше'."""
    await callback.answer()
    async with DatabaseContextManager() as session:
        try:
            user_id = callback.from_user.id
            user = await session.users.get_user(user_id=user_id)
            await state.update_data(callback_for_support='trial_subs')
            if not user.trial_used:
                await callback.message.edit_text(
                    text=LEXICON_RU['trial_offer'],
                    reply_markup=await InlineKeyboards.get_trial_subscription_keyboard()
                )
            else:
                await callback.message.edit_text(
                    text=LEXICON_RU['trial_subscription_used'],
                    reply_markup=InlineKeyboards.trial_used_keyboard()
                )
        except Exception as e:
            await logger.log_error(f"Error fetching user @{callback.from_user.username}\n"
                                   f"ID: {callback.from_user.id}", e)
