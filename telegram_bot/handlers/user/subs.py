from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory, StatusPay, AutoRenewalCallbackFactory
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

router = Router()


# Обработчик callback для показа подписок
@router.callback_query(lambda callback: callback.data == "view_subs")
async def get_user_subs_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    show_slow_internet_id = data.get("show_slow_internet")
    show_guide_message_id = data.get("show_guide_message")

    # Функция для удаления сообщения с обработкой исключений
    async def delete_message_safe(message_id):
        try:
            await callback.bot.delete_message(callback.message.chat.id, message_id)
        except Exception as e:
            # Если сообщение не найдено, логируем ошибку
            await logger.info(f"Не удалось удалить сообщение с ID {message_id}")

    # Удаление сообщений
    if show_slow_internet_id:
        await delete_message_safe(show_slow_internet_id)
        await state.update_data(show_slow_internet_id=None)

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
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
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
                                ],
                            ])
                        )
                    except:
                        await message.answer(
                            text=LEXICON_RU['subscription_not_found'],
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="🔥 Оформить подписку",
                                        callback_data="subscribe"
                                    )
                                ],
                            ])
                        )
                return

            buttons = []
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
                end_date = subscription.end_date
                key = subscription.key
                status = subscription.status
                name_app = subscription.name_app
                server_name = subscription.server_name
                server_ip = subscription.server_ip
                auto_renewal = False

                detailed_info = (
                    f"<b>🐉 Статус подписки:</b> {'🐲 Дракон на страже' if status == 'активная' else '💀 Покровительство завершено'}\n"
                    f"<b>🌍 Локация VPN:</b> {server_name}\n"
                    f"<b>📅 Окончание подписки:</b> {end_date.strftime('%d-%m-%Y')}\n"
                    f"<b>🔄 Автопродление:</b> {'✅' if auto_renewal else '❌'}\n"
                    f"<b>🐲🔑 Ключ:</b>\n"
                    f"<pre>{key}</pre>"
                )
                await state.update_data(back_target=f"view_details_{subscription_id}")
                # Клавиатура для управления подпиской
                await callback.message.edit_text(
                    text=detailed_info,
                    parse_mode="HTML",
                    reply_markup=await InlineKeyboards.menu_subs(subscription_id, name_app, server_ip)
                )
        except Exception as e:
            await logger.log_error("Ошибка при получении подробностей подписки\n"
                                   f"ID: {callback.from_user.id}\n", e)


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'extend_subscription'))
async def extend_subscription(callback: CallbackQuery, callback_data: SubscriptionCallbackFactory, state: FSMContext):
    subscription_id = callback_data.subscription_id
    back = callback_data.back
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
        reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.OLD, back),
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
                text="✔️ Включить" if not is_auto_renewal_enabled else "❌ Отключить",
                callback_data=AutoRenewalCallbackFactory(
                    action="off_or_on",
                    auto_renewal_enabled=not is_auto_renewal_enabled).pack()
            ),
            InlineKeyboardButton(
                text='🔙 Назад',
                callback_data=f'view_details_{subscription_id}'
            )
        ]
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(AutoRenewalCallbackFactory.filter(F.action == 'off_or_on'))
async def toggle_auto_renewal(callback: CallbackQuery, callback_data: AutoRenewalCallbackFactory):
    await callback.answer("Пока что эта функция не реализована.", show_alert=True, cache_time=5)
