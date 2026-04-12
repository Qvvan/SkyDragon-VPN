from cryptography.fernet import Fernet, InvalidToken

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.exc import IntegrityError

from config_data import config
from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards, BACK_BTN, MAIN_MENU_CB
from keyboards.set_menu import set_main_menu
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import ReferralStatus, Referrals, Users

router = Router()

_fernet = Fernet(config.CRYPTO_KEY.encode())

_LINK_TOKEN_TTL = 900  # 15 минут — должно совпадать с backend_v2


@router.message(CommandStart())
async def process_start_command(message: Message):
    await set_main_menu(message.bot, message.from_user.id)

    start_param = _get_start_param(message)

    if start_param and not start_param.isdigit():
        if _is_our_token(start_param):
            await _handle_account_link(message, start_param)
        else:
            await message.answer(
                text=LEXICON_RU['start'],
                reply_markup=await InlineKeyboards.get_menu_keyboard(),
                parse_mode="Markdown"
            )
        return

    await message.answer(
        text=LEXICON_RU['start'],
        reply_markup=await InlineKeyboards.get_menu_keyboard(),
        parse_mode="Markdown"
    )

    referrer_id = int(start_param) if start_param else None
    if referrer_id == message.from_user.id:
        referrer_id = None

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


def _get_start_param(message: Message) -> str | None:
    parts = message.text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else None


def _is_our_token(value: str) -> bool:
    """Структурная валидация: можем ли мы вообще расшифровать этот токен нашим ключом (без TTL)."""
    try:
        _fernet.decrypt(value.encode(), ttl=None)
        return True
    except (InvalidToken, Exception):
        return False


async def _handle_account_link(message: Message, token: str) -> None:
    # Теперь проверяем с TTL — если токен протух, говорим об этом
    try:
        data = _fernet.decrypt(token.encode(), ttl=_LINK_TOKEN_TTL)
        account_id = int(data.decode())
    except InvalidToken:
        await message.answer(
            "❌ Ссылка устарела. Запросите новую на сайте в разделе профиля."
        )
        return

    async with DatabaseContextManager() as db:
        try:
            account = await db.account_links.get_account_by_id(account_id)
            if not account:
                await message.answer("❌ Аккаунт не найден.")
                return

            if await db.account_links.get_link_by_telegram(message.from_user.id):
                await message.answer("⚠️ Этот Telegram уже привязан к другому аккаунту.")
                return

            if await db.account_links.get_link_by_account(account_id):
                await message.answer("⚠️ К этому аккаунту уже привязан другой Telegram.")
                return

            await db.account_links.insert_link(message.from_user.id, account_id)
            await db.account_links.backfill_subscriptions(account_id, message.from_user.id)
            await db.session.commit()

            await message.answer(
                f"✅ Аккаунт <b>{account.login}</b> успешно привязан к Telegram!\n\n"
                "Теперь вы можете управлять подпиской прямо здесь.",
                reply_markup=await InlineKeyboards.get_menu_keyboard(),
            )
        except IntegrityError:
            await db.session.rollback()
            await message.answer("⚠️ Этот аккаунт или Telegram уже привязан.")
        except Exception as e:
            await logger.log_error(f"Ошибка при привязке аккаунта (tg={message.from_user.id})", e)
            await message.answer("❌ Не удалось привязать аккаунт. Попробуйте позже.")


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
            await session_methods.session.commit()
            try:
                await logger.log_info(
                    f"Его пригласил пользователь с ID: {referrer_id}",
                    await InlineKeyboards.get_user_info(referrer_id)
                )
            except:
                await logger.log_info(f"Его пригласил пользователь с ID: {referrer_id}")
        except Exception as e:
            await logger.log_error(f"Ошибка при начислении бонуса за приглашение: {referrer_id}", e)


async def log_new_user(message: Message):
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
async def handle_back_to_start(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['start'],
        reply_markup=await InlineKeyboards.get_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == 'referal_subs')
async def handle_referal_subs(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        text=LEXICON_RU['invite_info'],
        reply_markup=await InlineKeyboards.get_invite_keyboard(MAIN_MENU_CB)
    )


@router.callback_query(lambda c: c.data == 'dragon_legends')
async def handle_dragon_legends(callback: CallbackQuery, state: FSMContext):
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
async def handle_trial_subs(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    async with DatabaseContextManager() as session:
        try:
            user = await session.users.get_user(user_id=callback.from_user.id)
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
            await logger.log_error(
                f"Error fetching user @{callback.from_user.username}\nID: {callback.from_user.id}", e
            )
