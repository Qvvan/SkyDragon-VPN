from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import ReferralStatus

router = Router()


@router.message(Command(commands='friends'))
async def get_invite_link(message: Message):
    await message.answer(text=LEXICON_RU['invite_info'], reply_markup=await InlineKeyboards.get_invite_keyboard())


@router.callback_query(lambda c: c.data == "back_to_call_allies")
async def show_referrals(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    back_target = data.get('back_target')
    await callback.message.edit_text(text=LEXICON_RU['invite_info'],
                                     reply_markup=await InlineKeyboards.get_invite_keyboard(back_target))


@router.callback_query(lambda c: c.data == "show_referrals")
async def show_referrals(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with DatabaseContextManager() as session_methods:
        try:
            list_referrals = await session_methods.referrals.get_list_referrers(user_id)
            if not list_referrals:
                await callback.message.edit_text(
                    text=LEXICON_RU['no_invites'],
                    reply_markup=InlineKeyboards.referrals_empty_keyboard()
                )
                await callback.answer()
                return

            referral_details = []
            for referral in list_referrals:
                invited_username = referral.invited_username or "Неизвестно"
                comparison_date = date(2024, 12, 13)
                if referral.bonus_issued == ReferralStatus.INVITED:
                    referral_details.append(f"👤 @{invited_username} - Приглашён")
                elif referral.bonus_issued == ReferralStatus.SUBSCRIBED:
                    days = 15 if referral.created_at.date() > comparison_date else 30
                    referral_details.append(f"👤 @{invited_username} - Бонус: {days} дней")

            referral_text = "\n".join(referral_details)
            await callback.message.edit_text(
                text=f"🐲 Ваши доступные бонусы:\n\n{referral_text}",
                reply_markup=InlineKeyboards.referrals_list_keyboard()
            )
            await callback.answer()
        except Exception as e:
            await logger.log_error("Error fetching referrals", e)


@router.callback_query(lambda c: c.data == "get_invite_link")
async def send_invite_link(callback: CallbackQuery):
    user_id = callback.from_user.id
    referral_link = f"https://t.me/SkyDragonVPNBot?start={user_id}"
    invite_text = LEXICON_RU['invite'].format(referral_link=referral_link)

    await callback.message.edit_text(
        text=invite_text,
        reply_markup=InlineKeyboards.invite_link_keyboard()
    )
    await callback.answer()
