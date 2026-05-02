import asyncio
from datetime import datetime
from html import escape

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.key_operations_background import create_keys_background, update_keys_background
from keyboards.kb_inline import InlineKeyboards, MAIN_MENU_BTN, MAIN_MENU_CB
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from utils.admin_activity_log import admin_activity_message


def _recipient_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐉 Мои подписки", callback_data="view_subs")],
            [InlineKeyboardButton(text=MAIN_MENU_BTN, callback_data=MAIN_MENU_CB)],
        ]
    )


async def _fulfill_gift_delivery(
    bot: Bot,
    gift,
    session_methods,
    *,
    recipient_message: Message | None = None,
) -> bool:
    """
    Зачисляет подписку по подарку, помечает used, коммитит, шлёт уведомления.
    recipient_message: если передан (старая кнопка «Активировать»), редактируем его вместо нового сообщения.
    Возвращает True, если зачисление выполнено этим вызовом.
    """
    gift_cur = await session_methods.gifts.get_gift_by_id(gift.gift_id)
    if not gift_cur or gift_cur.status not in ("pending", "awaiting_activation"):
        return False

    recipient = await session_methods.users.get_user(gift_cur.recipient_user_id)
    if not recipient:
        return False

    service = await session_methods.services.get_service_by_id(gift_cur.service_id)
    if not service:
        await logger.log_error(
            f"Подарок gift_id={gift_cur.gift_id}: услуга service_id={gift_cur.service_id} не найдена",
            Exception("missing service"),
        )
        return False

    sender_user = await session_methods.users.get_user(gift_cur.giver_id)
    subs = await session_methods.subscription.get_subscription(gift_cur.recipient_user_id)
    had_subs = bool(subs)

    try:
        extended = await extend_user_subscription(
            gift_cur.recipient_user_id,
            recipient.username or "",
            service.duration_days,
            session_methods,
        )
    except Exception as e:
        await session_methods.session.rollback()
        await logger.log_error(f"Подарок gift_id={gift_cur.gift_id}: ошибка зачисления", e)
        return False

    sub_id = getattr(extended, "subscription_id", None)

    gift_final = await session_methods.gifts.get_gift_by_id(gift_cur.gift_id)
    if not gift_final or gift_final.status not in ("pending", "awaiting_activation"):
        await session_methods.session.rollback()
        return False

    await session_methods.gifts.update_gift(
        gift_id=gift_cur.gift_id,
        status="used",
        activated_at=datetime.utcnow(),
    )
    await session_methods.session.commit()

    if sub_id:
        if had_subs:
            asyncio.create_task(
                update_keys_background(gift_cur.recipient_user_id, sub_id, True)
            )
        else:
            asyncio.create_task(
                create_keys_background(
                    gift_cur.recipient_user_id,
                    recipient.username or "",
                    sub_id,
                    0,
                )
            )

    giver_label = (
        f"@{escape(sender_user.username)}"
        if sender_user and sender_user.username
        else (escape(str(sender_user.user_id)) if sender_user else "друг")
    )
    days = int(service.duration_days)
    body = LEXICON_RU["gift_recipient_auto"].format(giver=giver_label, days=days)

    try:
        if recipient_message:
            await recipient_message.edit_text(
                body,
                reply_markup=_recipient_keyboard(),
                parse_mode="HTML",
            )
        else:
            await bot.send_message(
                chat_id=gift_cur.recipient_user_id,
                text=body,
                reply_markup=_recipient_keyboard(),
                parse_mode="HTML",
            )
    except Exception as e:
        await logger.warning(f"Не удалось отправить текст получателю подарка {gift_cur.gift_id}: {e}")

    if sender_user:
        try:
            await bot.send_message(
                chat_id=gift_cur.giver_id,
                text=LEXICON_RU["gift_sender_delivered"].format(days=days),
                parse_mode="HTML",
                reply_markup=InlineKeyboards.row_main_menu(),
            )
        except Exception as e:
            await logger.warning(f"Не удалось уведомить дарителя {gift_cur.giver_id}: {e}")

    await logger.log_info(
        admin_activity_message(
            "Подарок: автоматически зачислен получателю",
            user_id=gift_cur.recipient_user_id,
            username=recipient.username,
            service=service,
            subscription_id=sub_id,
            payment_response=None,
            extra=(
                f"gift_id: {gift_cur.gift_id}\n"
                f"даритель user_id: {gift_cur.giver_id}\n"
                f"даритель username: @{sender_user.username if sender_user and sender_user.username else '—'}"
            ),
        )
    )
    return True


async def try_deliver_gift(bot: Bot, gift_id: int, *, recipient_message: Message | None = None) -> bool:
    async with DatabaseContextManager() as session_methods:
        gift = await session_methods.gifts.get_gift_by_id(gift_id)
        if not gift:
            return False
        return await _fulfill_gift_delivery(bot, gift, session_methods, recipient_message=recipient_message)


async def deliver_pending_gifts_for_user(bot: Bot, user_id: int, username: str | None) -> None:
    """После /start: зачислить подарки, ожидавшие появления пользователя в БД."""
    async with DatabaseContextManager() as session_methods:
        pending = await session_methods.gifts.get_pending_gifts_for_recipient(user_id)
        gift_ids = [g.gift_id for g in pending]

    for gid in gift_ids:
        await try_deliver_gift(bot, gid)


async def gift_checker(bot: Bot):
    async with DatabaseContextManager() as session_methods:
        try:
            gifts = await session_methods.gifts.get_undelivered_gifts()
            gift_ids = [g.gift_id for g in gifts]
        except Exception as e:
            await logger.log_error(f"Ошибка при получении списка подарков", e)
            return

    for gid in gift_ids:
        try:
            await try_deliver_gift(bot, gid)
        except Exception as e:
            await logger.log_error(f"Ошибка при доставке подарка gift_id={gid}", e)


async def activate_gift_handler(bot: Bot, callback_query: CallbackQuery, gift_id: int):
    """Старые кнопки «Активировать»: зачисляем, если ещё не зачислено."""
    async with DatabaseContextManager() as session_methods:
        gift = await session_methods.gifts.get_gift_by_id(gift_id)
        if not gift:
            await callback_query.answer("Подарок не найден", show_alert=True)
            return
        if callback_query.from_user.id != gift.recipient_user_id:
            await callback_query.answer("Это не ваш подарок", show_alert=True)
            return
        if gift.status == "used":
            await callback_query.answer()
            try:
                await callback_query.message.edit_text(
                    LEXICON_RU["gift_already_credited"],
                    reply_markup=InlineKeyboards.row_main_menu(),
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

    await callback_query.answer()
    ok = await try_deliver_gift(bot, gift_id, recipient_message=callback_query.message)
    if not ok:
        async with DatabaseContextManager() as sm:
            g2 = await sm.gifts.get_gift_by_id(gift_id)
            if g2 and g2.status == "used":
                try:
                    await callback_query.message.edit_text(
                        LEXICON_RU["gift_already_credited"],
                        reply_markup=InlineKeyboards.row_main_menu(),
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
                return
        try:
            await callback_query.message.edit_text(
                "Не удалось зачислить подарок. Напишите в поддержку /help",
                reply_markup=InlineKeyboards.row_main_menu(),
            )
        except Exception:
            pass


async def run_gift_checker(bot: Bot):
    while True:
        try:
            await gift_checker(bot)
        except Exception as e:
            await logger.log_error("Ошибка в цикле run_gift_checker", e)

        await asyncio.sleep(5)
