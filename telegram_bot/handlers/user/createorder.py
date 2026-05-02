from datetime import datetime
from typing import Optional, Tuple

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import TELEGRAM_YOOKASSA_RETURN_URL
from database.context_manager import DatabaseContextManager
from handlers.services.card_service import create_payment
from keyboards.kb_inline import (
    InlineKeyboards,
    BACK_BTN,
    MAIN_MENU_BTN,
    MAIN_MENU_CB,
    ServiceCallbackFactory,
    StatusPay,
    StarsPayCallbackFactory,
    DefaultCallback,
)
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import Payments
from utils.service_ui_label import service_keyboard_label

router = Router()

_MULTI_SUB_EXTEND_TEXT = (
    "У вас несколько подписок. Откройте «Мои подписки», выберите нужную и нажмите «Продлить»."
)


def _keyboard_multi_sub_extend() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐉 Мои подписки", callback_data="view_subs")],
            [InlineKeyboardButton(text=MAIN_MENU_BTN, callback_data=MAIN_MENU_CB)],
        ]
    )


async def resolve_payment_context(
    session_methods,
    user_id: int,
    status_pay: StatusPay,
    subscription_id: Optional[int],
) -> Tuple[StatusPay, Optional[int]]:
    """Нет подписок — новая; есть — продление (совместимость: callback «new» при наличии подписок)."""
    subs = await session_methods.subscription.get_subscription(user_id)
    if not subs:
        return StatusPay.NEW, None
    latest = max(subs, key=lambda s: s["end_date"] or datetime.min)
    latest_id = int(latest["subscription_id"])
    if status_pay == StatusPay.NEW:
        return StatusPay.OLD, latest_id
    if subscription_id is not None:
        sub_row = await session_methods.subscription.get_subscription_by_id(int(subscription_id))
        if sub_row and int(sub_row["user_id"]) == user_id:
            return StatusPay.OLD, int(subscription_id)
    return StatusPay.OLD, latest_id


@router.message(Command(commands='new'))
async def create_order(message: Message, state: FSMContext):
    async with DatabaseContextManager() as session_methods:
        await state.update_data(back_target='subscribe')
        try:
            subs = await session_methods.subscription.get_subscription(message.from_user.id)
            if subs:
                if len(subs) == 1:
                    sid = int(subs[0]["subscription_id"])
                    await state.update_data(status_pay=StatusPay.OLD.value, subscription_id=sid)
                    await message.answer(
                        text=LEXICON_RU['createorder'],
                        reply_markup=await InlineKeyboards.create_order_keyboards(
                            StatusPay.OLD, back_target='subscribe', subscription_id=sid
                        ),
                        parse_mode="HTML",
                    )
                else:
                    await state.update_data(status_pay=None, subscription_id=None)
                    await message.answer(
                        text=_MULTI_SUB_EXTEND_TEXT,
                        reply_markup=_keyboard_multi_sub_extend(),
                    )
            else:
                await state.update_data(status_pay=StatusPay.NEW.value, subscription_id=None)
                await message.answer(
                    text=LEXICON_RU['createorder'],
                    reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.NEW),
                    parse_mode="HTML",
                )
        except Exception as e:
            await logger.log_error(f"Error creating order", e)


@router.callback_query(lambda c: c.data == 'subscribe')
async def handle_subscribe(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Оформить подписку' в главном меню."""
    await callback.answer()

    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subscription(callback.from_user.id)
            if subs:
                if len(subs) == 1:
                    sid = int(subs[0]["subscription_id"])
                    await state.update_data(status_pay=StatusPay.OLD.value, subscription_id=sid)
                    await callback.message.edit_text(
                        text=LEXICON_RU['createorder'],
                        reply_markup=await InlineKeyboards.create_order_keyboards(
                            StatusPay.OLD, back_target="main_menu", subscription_id=sid
                        ),
                        parse_mode="HTML",
                    )
                else:
                    await state.update_data(status_pay=None, subscription_id=None)
                    await callback.message.edit_text(
                        text=_MULTI_SUB_EXTEND_TEXT,
                        reply_markup=_keyboard_multi_sub_extend(),
                    )
            else:
                await state.update_data(status_pay=StatusPay.NEW.value, subscription_id=None)
                await callback.message.edit_text(
                    text=LEXICON_RU['createorder'],
                    reply_markup=await InlineKeyboards.create_order_keyboards(
                        StatusPay.NEW, back_target="main_menu"
                    ),
                    parse_mode="HTML",
                )
        except Exception as e:
            await logger.log_error(f"Error creating order", e)


@router.callback_query(DefaultCallback.filter(F.action == "create_order"))
async def handle_default_create_order(
    callback: CallbackQuery, callback_data: DefaultCallback, state: FSMContext
):
    """Старые кнопки «оформить новую»: при наличии подписок — продление, иначе новая."""
    await callback.answer()
    back_target = callback_data.back

    async with DatabaseContextManager() as session_methods:
        subs = await session_methods.subscription.get_subscription(callback.from_user.id)
        if subs:
            if len(subs) == 1:
                sid = int(subs[0]["subscription_id"])
                await state.update_data(status_pay=StatusPay.OLD.value, subscription_id=sid)
                await callback.message.edit_text(
                    text=LEXICON_RU['createorder'],
                    reply_markup=await InlineKeyboards.create_order_keyboards(
                        StatusPay.OLD, back_target=back_target, subscription_id=sid
                    ),
                    parse_mode="HTML",
                )
            else:
                await state.update_data(status_pay=None, subscription_id=None)
                await callback.message.edit_text(
                    text=_MULTI_SUB_EXTEND_TEXT,
                    reply_markup=_keyboard_multi_sub_extend(),
                )
            return

    await state.update_data(status_pay=StatusPay.NEW.value, subscription_id=None)
    await callback.message.edit_text(
        text=LEXICON_RU['createorder'],
        reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.NEW, back_target=back_target),
        parse_mode="HTML",
    )


@router.callback_query(ServiceCallbackFactory.filter())
async def handle_service_callback(
    callback_query: CallbackQuery, callback_data: ServiceCallbackFactory, state: FSMContext
):
    user_data = await state.get_data()
    back_target = user_data.get('back_target')

    try:
        status_pay = StatusPay(callback_data.status_pay)
    except ValueError:
        status_pay = StatusPay.NEW

    async with DatabaseContextManager() as session_methods:
        eff_status, eff_sub_id = await resolve_payment_context(
            session_methods,
            callback_query.from_user.id,
            status_pay,
            callback_data.subscription_id,
        )

    resolved_cb = ServiceCallbackFactory(
        service_id=callback_data.service_id,
        status_pay=eff_status.value,
        subscription_id=eff_sub_id,
    )
    await state.update_data(status_pay=eff_status.value, subscription_id=eff_sub_id)

    try:
        await callback_query.message.edit_text(
            "Выберите способ оплаты",
            reply_markup=await InlineKeyboards.payment_method(
                resolved_cb, eff_sub_id, back_target
            ),
        )
    except Exception:
        await callback_query.message.delete()
        await callback_query.message.answer(
            "Выберите способ оплаты",
            reply_markup=await InlineKeyboards.payment_method(
                resolved_cb, eff_sub_id, back_target
            ),
        )


@router.callback_query(lambda c: c.data == 'back_to_services')
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()

    show_stars_guide = user_data.get("show_stars_guide")
    if show_stars_guide:
        try:
            await callback.bot.delete_message(callback.message.chat.id, show_stars_guide)
            await state.update_data(show_slow_internet_id=None)
        except Exception:
            await logger.info(f"Не удалось удалить сообщение с ID {show_stars_guide}")

    status_pay_value = user_data.get('status_pay') or StatusPay.NEW.value

    try:
        status_pay = StatusPay(status_pay_value)
    except ValueError:
        status_pay = StatusPay.NEW

    back_target = user_data.get('back_target', 'main_menu')
    sub_id = user_data.get('subscription_id')
    try:
        await callback.message.edit_text(
            text=LEXICON_RU['createorder'],
            reply_markup=await InlineKeyboards.create_order_keyboards(
                status_pay, back_target=back_target, subscription_id=sub_id
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        await logger.log_error(f"Ошибка при редактировании сообщения", e)


@router.callback_query(StarsPayCallbackFactory.filter(F.action == 'card_pay'))
async def stars_pay(callback_query: CallbackQuery, callback_data: StarsPayCallbackFactory):
    await callback_query.answer()

    service_id = int(callback_data.service_id)
    try:
        status_pay = StatusPay(callback_data.status_pay)
    except ValueError:
        status_pay = StatusPay.NEW

    try:
        raw_sub_id = callback_data.subscription_id
        subscription_id = int(raw_sub_id) if raw_sub_id is not None else None
    except (TypeError, ValueError):
        subscription_id = None

    async with DatabaseContextManager() as session_methods:
        try:
            status_pay, subscription_id = await resolve_payment_context(
                session_methods,
                callback_query.from_user.id,
                status_pay,
                subscription_id,
            )

            if status_pay == StatusPay.OLD:
                sub = await session_methods.subscription.get_subscription_by_id(subscription_id)
                if sub is None:
                    try:
                        await callback_query.message.edit_text(
                            text="Подписка, которую вы хотите продлить, не найдена🙏",
                            reply_markup=InlineKeyboards.row_main_menu(),
                        )
                    except Exception:
                        await callback_query.message.answer(
                            text="Подписка, которую вы хотите продлить, не найдена🙏",
                            reply_markup=InlineKeyboards.row_main_menu(),
                        )
                    return

            service = await session_methods.services.get_service_by_id(service_id)
            payment_data = await create_payment(
                amount=service.price,
                description=f"Оплата за услугу: {service.name}",
                return_url=TELEGRAM_YOOKASSA_RETURN_URL,
                service_id=service_id,
                service_type=status_pay.value,
                user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                subscription_id=subscription_id,
            )

            payment_url = payment_data['confirmation']['confirmation_url']
            payment_id = payment_data['id']

            payment_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Оплатить",
                            url=payment_url,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=BACK_BTN,
                            callback_data=ServiceCallbackFactory(
                                service_id=str(service_id),
                                status_pay=status_pay.value,
                                subscription_id=subscription_id,
                            ).pack(),
                        )
                    ],
                ]
            )

            offer_line = service_keyboard_label(service.duration_days, service.price)
            await callback_query.message.edit_text(
                text=f"{offer_line}\n\nОплата ниже.",
                reply_markup=payment_kb,
            )
            await session_methods.payments.create_payments(
                Payments(
                    payment_id=payment_id,
                    user_id=callback_query.from_user.id,
                    service_id=service_id,
                )
            )
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(
                f'Пользователь: @{callback_query.from_user.username}'
                f'ID: {callback_query.from_user.id}\n'
                f'Ошибка при создании платежа',
                e,
            )
            await callback_query.message.edit_text(
                text="Что-то пошло не так, обратитесь в техподдержку.",
                reply_markup=InlineKeyboards.row_main_menu(),
            )


@router.callback_query(lambda c: c.data == 'empty')
async def handle_empty_callback(callback: CallbackQuery):
    await callback.answer("Soon...", show_alert=True, cache_time=3)
