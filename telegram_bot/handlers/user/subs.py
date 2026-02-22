from datetime import datetime

import pytz
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link
from keyboards.kb_inline import InlineKeyboards, BACK_BTN, SubscriptionCallbackFactory, StatusPay, AutoRenewalCallbackFactory
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

router = Router()

moscow_tz = pytz.timezone("Europe/Moscow")


@router.callback_query(lambda callback: callback.data == "view_subs")
async def get_user_subs_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    show_guide_message_id = data.get("show_guide_message")

    async def delete_message_safe(message_id):
        try:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        except Exception as e:
            await logger.info(f"Не удалось удалить сообщение с ID {message_id}")

    if show_guide_message_id:
        await delete_message_safe(show_guide_message_id)
        await state.update_data(show_guide_message_id=None)

    if previous_message_id:
        await delete_message_safe(previous_message_id)
        await state.update_data(text_dragons_overview_id=None)

    await show_user_subscriptions(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        message=callback.message,
        state=state
    )
    await callback.answer()


@router.message(Command(commands="profile"))
async def get_user_subs_command(message: Message, state: FSMContext):
    await show_user_subscriptions(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message,
        state=state
    )


async def show_user_subscriptions(user_id, username, message, state: FSMContext):
    async with (DatabaseContextManager() as session):
        try:
            # Получаем данные о подписках пользователя
            subscription_data = await session.subscription.get_subscription(user_id)

            await state.update_data(back_target='view_subs')
            await state.update_data(callback_for_support='view_subs')
            user = await session.users.get_user(user_id=user_id)
            if subscription_data is None:
                if not user.trial_used:
                    await message.answer(
                        text=LEXICON_RU['trial_offer'],
                        reply_markup=await InlineKeyboards.get_trial_subscription_keyboard()
                    )
                else:
                    try:
                        await message.edit_text(
                            text=LEXICON_RU['subscription_not_found'],
                            reply_markup=InlineKeyboards.no_subscription_keyboard()
                        )
                    except Exception:
                        await message.answer(
                            text=LEXICON_RU['subscription_not_found'],
                            reply_markup=InlineKeyboards.no_subscription_keyboard()
                        )
                return

            buttons = []

            if len(subscription_data) == 1:
                detailed_info = await format_subscription_details(subscription_data[0])

                try:
                    await message.edit_text(
                        text=detailed_info,
                        parse_mode="HTML",
                        reply_markup=await InlineKeyboards.menu_subs(
                            subscription_id=subscription_data[0].subscription_id,
                            auto_renewal=subscription_data[0].auto_renewal,
                            back_button="main_menu"
                        )
                    )
                except:
                    await message.answer(
                        text=detailed_info,
                        parse_mode="HTML",
                        reply_markup=await InlineKeyboards.menu_subs(
                            subscription_id=subscription_data[0].subscription_id,
                            auto_renewal=subscription_data[0].auto_renewal,
                            back_button="main_menu"
                        )
                    )
                return

            for index, data in enumerate(subscription_data):
                end_date = data.end_date.date()
                days_left = (end_date - datetime.now().date()).days

                if days_left >= 0:
                    button_text = f"Ваша подписка({days_left} дн.)"
                else:
                    button_text = "Подписка закончилась"
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📜 {button_text}",
                        callback_data=f"view_details_{data.subscription_id}"
                    )
                ])

                # Сохраняем ID подписки в состоянии
                await state.update_data(subscription_id=data.subscription_id)

            if not user.trial_used:
                buttons.append([
                    InlineKeyboardButton(
                        text="🐲 Пробный период",
                        callback_data="trial_subs"
                    )
                ])
            buttons.append([
                InlineKeyboardButton(
                    text="💰 История платежей",
                    callback_data="history_payments"
                )
            ])
            buttons.append([
                InlineKeyboardButton(
                    text="🌌 Главное меню",
                    callback_data="main_menu"
                )
            ])

            try:
                await message.edit_text(
                    text='<b>Нажми на подписку, чтобы узнать о ней подробнее</b>',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                    parse_mode="HTML")
            except:
                await message.answer(
                    text='<b>Нажми на подписку, чтобы узнать о ней подробнее</b>',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                    parse_mode="HTML")

        except Exception as e:
            await logger.log_error(f'Пользователь: @{username}\n'
                                   f'ID: {user_id}\n'
                                   f'Ошибка при получении подписок', e)


@router.callback_query(lambda c: c.data.startswith("view_details_"))
async def show_subscription_details(callback: CallbackQuery, state: FSMContext):
    subscription_id = int(callback.data.split("_")[2])

    await callback.answer()
    async with DatabaseContextManager() as session:
        try:
            subscription = await session.subscription.get_subscription_by_id(subscription_id)
            if subscription:
                detailed_info = await format_subscription_details(subscription)

                await state.update_data(back_target=f"view_details_{subscription_id}")
                await callback.message.edit_text(
                    text=detailed_info,
                    parse_mode="HTML",
                    reply_markup=await InlineKeyboards.menu_subs(subscription_id, subscription.auto_renewal)
                )
        except Exception as e:
            await logger.log_error("Ошибка при получении подробностей подписки\n"
                                   f"ID: {callback.from_user.id}\n", e)


async def format_subscription_details(subscription):
    """Форматирует данные подписки в текстовое представление."""
    created_at_msk = subscription.created_at.replace(tzinfo=pytz.utc).astimezone(moscow_tz)
    end_date_msk = subscription.end_date.replace(tzinfo=pytz.utc).astimezone(moscow_tz)

    # Определение оставшегося времени
    now_msk = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(moscow_tz)
    remaining_days = (end_date_msk.date() - now_msk.date()).days

    # Формируем блок про истечение подписки
    if subscription.status == 'активная':
        subscription_status = (
            "<b>📆 Подписка истекает</b>\n"
            f"├ <code>{end_date_msk.strftime('%d %B %Y, %H:%M:%S')} MSK</code>\n"
            f"└ <b>Осталось:</b> <code>{remaining_days} {'день' if remaining_days == 1 else 'дня' if 1 < remaining_days < 5 else 'дней'}</code>\n\n"
        )
    else:
        subscription_status = (
            "<b>📆 Подписка истекла</b>\n"
            f"└ <code>{end_date_msk.strftime('%d %B %Y, %H:%M:%S')} MSK</code>\n\n"
        )
    config_link = await create_config_link(subscription.user_id, subscription.subscription_id)

    return (
        "<b>📊 Информация о подписке</b>\n"
        f"├ <b>Создана:</b> <code>{created_at_msk.strftime('%d %B %Y, %H:%M:%S')} MSK</code>\n"
        f"└ <b>Статус:</b> {'✅ <code>Активна</code>' if subscription.status == 'активная' else '❌ <code>Неактивна, истекла</code>'}\n\n"
        f"{subscription_status}"
        "<b>🏷 Автопродление</b>\n"
        f"└ {'✅ <code>Включено</code>' if subscription.auto_renewal else '❌ <code>Выключено</code>'}\n\n"
        "<b>🔗 Ссылка активации</b>\n"
        f"<code>{config_link if config_link else '⚠️ Информация недоступна'}</code>"
    )


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'extend_subscription'))
async def extend_subscription(callback: CallbackQuery, callback_data: SubscriptionCallbackFactory, state: FSMContext):
    subscription_id = callback_data.subscription_id
    back = callback_data.back
    status_pay = callback_data.status_pay

    async with DatabaseContextManager() as session:
        sub = await session.subscription.get_subscription_by_id(subscription_id)
        if not sub and status_pay == StatusPay.OLD:
            await callback.answer(
                text="Подписка, которую вы хотите продлить, не найдена🙏",
                show_alert=True,
                cache_time=5
            )
            return
    await callback.answer()

    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.info(f"Не удалось удалить сообщение с ID {previous_message_id}: {e}")

    await state.update_data(subscription_id=subscription_id)
    await state.update_data(status_pay=StatusPay.OLD)

    await callback.message.edit_text(
        text=LEXICON_RU['createorder'],
        reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.OLD, back, subscription_id),
    )


@router.callback_query(AutoRenewalCallbackFactory.filter(F.action == 'auto_renewal'))
async def toggle_auto_renewal(callback: CallbackQuery, callback_data: AutoRenewalCallbackFactory):
    # Проверяем текущее состояние автопродления
    is_auto_renewal_enabled = callback_data.auto_renewal_enabled
    subscription_id = callback_data.subscription_id

    text = (
        f"🔔 Автопродление подписки: {'✅ Включено' if is_auto_renewal_enabled else '❌ Отключено'}\n\n"
        "Вы можете изменить статус автопродления, нажав на соответствующую кнопку ниже."
    )

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Включить" if not is_auto_renewal_enabled else "❌ Отключить",
                callback_data=AutoRenewalCallbackFactory(
                    action="off_or_on",
                    subscription_id=subscription_id,
                    auto_renewal_enabled=not is_auto_renewal_enabled).pack()
            ),
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f'view_details_{subscription_id}'
            )
        ]
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(AutoRenewalCallbackFactory.filter(F.action == 'off_or_on'))
async def toggle_auto_renewal(callback: CallbackQuery, callback_data: AutoRenewalCallbackFactory):
    is_auto_renewal_enabled = callback_data.auto_renewal_enabled
    subscription_id = callback_data.subscription_id

    async with DatabaseContextManager() as session_methods:
        if is_auto_renewal_enabled:
            await session_methods.subscription.update_sub(subscription_id, auto_renewal=is_auto_renewal_enabled)
        else:
            await session_methods.subscription.update_sub(subscription_id, auto_renewal=is_auto_renewal_enabled,
                                                          card_details_id=None)
        await session_methods.session.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Включить" if not is_auto_renewal_enabled else "❌ Отключить",
                callback_data=AutoRenewalCallbackFactory(
                    action="off_or_on",
                    subscription_id=subscription_id,
                    auto_renewal_enabled=not is_auto_renewal_enabled).pack()
            ),
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f'view_details_{subscription_id}'
            )
        ]
    ])

    await callback.message.edit_text(
        text=f"🔔 Автопродление подписки: {'✅ Включено' if is_auto_renewal_enabled else '❌ Отключено'}\n\n"
             "Вы можете изменить статус автопродления, нажав на соответствующую кнопку ниже.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
