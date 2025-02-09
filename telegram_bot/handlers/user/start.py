from datetime import datetime

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from keyboards.kb_inline import InlineKeyboards
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
                gifts = await session_methods.gifts.get_gift_by_username(message.from_user.username)
                if gifts:
                    await get_new_gift(gifts, message)
                await log_new_user(message)
                if referrer_id:
                    await handle_referral(referrer_id, message)
        except Exception as e:
            await logger.log_error(
                f'Пользователь: @{message.from_user.username}\n'
                f'ID: {message.from_user.id}\n'
                f'При команде /start произошла ошибка:', e
            )


async def get_new_gift(gifts, message):
    async with DatabaseContextManager() as session_methods:
        try:
            for gift in gifts:
                if gift.status == "used":
                    continue
                giver = await session_methods.users.get_user(gift.giver_id)
                service = await session_methods.services.get_service_by_id(gift.service_id)
                await extend_user_subscription(message.from_user.id, message.from_user.username, service.duration_days,
                                               session_methods)
                await session_methods.gifts.update_gift(gift_id=gift.gift_id, status="used",
                                                        activated_at=datetime.utcnow())
                await message.answer(
                    text="У вас есть новый подарок! 🎁\n\n"
                         f"От {'@' + giver.username if giver.username else 'Неизвестного пользователя'}:\n"
                         f"{service.name} на {service.duration_days} дней",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🐉 Мои подписки",
                                callback_data="view_subs"
                            )
                        ],
                    ])
                )
                await session_methods.session.commit()
        except Exception as e:
            await session_methods.session.rollback()
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
                    f"🐲 Ваш друг {'@' + message.from_user.username if message.from_user.username else ''} присоединился к кругу! Древние драконы даруют вам бонус силы 🎁",
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
            await extend_user_subscription(referrer_id, message.from_user.username, 5, session_methods)
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
        reply_markup=await InlineKeyboards.get_invite_keyboard('back_to_start')
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
                [
                    InlineKeyboardButton(
                        text="🔥 Оформить подписку",
                        callback_data="subscribe"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="back_to_start"
                    )
                ]
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
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🐉 Мои подписки",
                                    callback_data="view_subs"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="🔙 Назад",
                                    callback_data="back_to_start"
                                )
                            ]
                        ]
                    )
                )
        except Exception as e:
            await logger.log_error(f"Error fetching user @{callback.from_user.username}\n"
                                   f"ID: {callback.from_user.id}", e)
