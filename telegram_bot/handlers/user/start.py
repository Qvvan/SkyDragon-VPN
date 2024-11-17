from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import ReferralStatus, Referrals, Users

router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(
            text=LEXICON_RU['start'],
            reply_markup=await InlineKeyboards.get_menu_keyboard(),
            parse_mode="Markdown"
            )
    command_args = message.text.split()
    referrer_id = int(command_args[1]) if len(command_args) > 1 and command_args[1].isdigit() else None

    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👥 Сколько союзников", callback_data="show_referrals")
                    ]
                ]
            )

    async with DatabaseContextManager() as session_methods:
        try:
            status_user = await session_methods.users.add_user(
                    Users(
                            user_id=message.from_user.id,
                            username=message.from_user.username,
                            )
                    )
            if status_user:
                await logger.log_info(
                        f"К нам присоединился:\n"
                        f"Имя: @{message.from_user.username}\n"
                        f"id: {message.from_user.id}"
                        )
                if referrer_id and referrer_id != message.from_user.id:
                    await message.bot.send_message(
                            referrer_id,
                            f"🐲 Ваш союзник @{message.from_user.username} присоединился к кругу! Древние драконы даруют вам бонус силы 🎁",
                            reply_markup=keyboard
                            )
                    await logger.log_info(
                            f"Его пригласил пользователь с ID: {referrer_id}"
                            )
                    try:
                        await session_methods.referrals.add_referrer(
                                referral=Referrals(
                                        referrer_id=referrer_id,
                                        referred_id=message.from_user.id,
                                        invited_username=message.from_user.username,
                                        bonus_issued=ReferralStatus.INVITED,
                                        )
                                )
                        await extend_user_subscription(referrer_id, 7, session_methods)
                    except Exception as e:
                        await logger.log_error(f"Ошибка при начислении бонуса за приглашение: {referrer_id}", e)
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(
                    f'Пользователь: @{message.from_user.username}\n'
                    f'При команде /start произошла ошибка:', e
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
                                    text="🔥 Оформить защиту дракона",
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
async def handle_know_more(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать больше'."""
    await callback.answer()
    async with DatabaseContextManager() as session:
        try:
            user_id = callback.from_user.id
            user = await session.users.get_user(user_ib=user_id)
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
                                                text="🐉 Мои драконы",
                                                callback_data="view_subs"
                                                )
                                        ],
                                    [
                                        InlineKeyboardButton(
                                            text="🧙‍♂️ Поддержка",
                                            callback_data="help_wizards_callback"
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
            await logger.log_error(f"Error fetching user @{callback.from_user.username}", e)


