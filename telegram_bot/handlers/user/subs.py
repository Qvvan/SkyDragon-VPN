from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory, StatusPay
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

router = Router()


# Обработчик callback для показа подписок
@router.callback_query(lambda callback: callback.data == "view_subs")
async def get_user_subs_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.log_error(f"Не удалось удалить сообщение с ID {previous_message_id}: {e}")

    await show_user_subscriptions(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        message=callback.message,
        state=state
    )
    await callback.answer()


@router.message(Command(commands="my_dragons"))
async def get_user_subs_command(message: Message, state: FSMContext):
    await show_user_subscriptions(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message=message,
        state=state
    )


async def show_user_subscriptions(user_id, username, message, state: FSMContext):
    # Отправляем начальное приветственное сообщение

    async with DatabaseContextManager() as session:
        try:
            # Получаем данные о подписках пользователя
            subscription_data = await session.subscription.get_subscription(user_id)

            await state.update_data(back_target='view_subs')

            # Проверка: если подписок нет
            if subscription_data is None:
                user = await session.users.get_user(user_id=user_id)
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
                                        text="🔥 Оформить защиту дракона",
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
                                        text="🔥 Оформить защиту дракона",
                                        callback_data="subscribe"
                                    )
                                ],
                            ])
                        )
                return

            # Создаём кнопки для каждой подписки
            buttons = []
            for data in subscription_data:
                end_date = data.end_date.date()
                days_left = (end_date - datetime.now().date()).days

                # Текст на кнопке: либо оставшиеся дни, либо "Дракон спит"
                button_text = f"Ваша подписка({days_left} дн.)" if days_left >= 0 else "Дракон спит"

                buttons.append([
                    InlineKeyboardButton(
                        text=f"📜 {button_text}",
                        callback_data=f"view_details_{data.subscription_id}"
                    )
                ])

                # Сохраняем ID подписки в состоянии
                await state.update_data(subscription_id=data.subscription_id)

            buttons.append([
                InlineKeyboardButton(
                    text="🔥 Оформить защиту дракона",
                    callback_data="subscribe"
                )
            ])
            buttons.append([
                InlineKeyboardButton(
                    text="🌌 К началу пути",
                    callback_data="back_to_start"
                )
            ])

            try:
                await message.edit_text(
                    text=LEXICON_RU['intro_text'],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                    parse_mode="HTML")
            except:
                await message.answer(
                    text=LEXICON_RU['intro_text'],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                    parse_mode="HTML")

        except Exception as e:
            await logger.log_error(f'Пользователь: @{username}\nОшибка при получении подписок', e)


@router.callback_query(lambda c: c.data.startswith("view_details_"))
async def show_subscription_details(callback: CallbackQuery, state: FSMContext):
    subscription_id = int(callback.data.split("_")[2])
    await callback.message.delete()

    # Отправляем новое сообщение text_dragons_overview и сохраняем его ID
    text_dragons_overview = await callback.message.answer(
        text=LEXICON_RU['text_dragons_overview']
    )
    await state.update_data(text_dragons_overview_id=text_dragons_overview.message_id)

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

                detailed_info = (
                    f"<b>🐉 Статус защиты:</b> {'🐲 Дракон на страже' if status == 'активная' else '💀 Покровительство завершено'}\n"
                    f"<b>🧿 Амулет:</b> {name_app}\n"
                    f"<b>🌍 Местоположение цитадели:</b> {server_name}\n"
                    f"<b>📅 Завершение покровительства:</b> {end_date.strftime('%d-%m-%Y')}\n"
                    f"<b>🐲🔑 Имя дракона:</b>\n"
                    f"<pre>{key}</pre>"
                )

                # Клавиатура для управления подпиской
                await callback.message.answer(
                    text=detailed_info,
                    parse_mode="HTML",
                    reply_markup=await InlineKeyboards.menu_subs(subscription_id, name_app, server_ip)
                )
        except Exception as e:
            await logger.log_error("Ошибка при получении подробностей подписки", e)


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'extend_subscription'))
async def extend_subscription(callback: CallbackQuery, callback_data: SubscriptionCallbackFactory, state: FSMContext):
    subscription_id = callback_data.subscription_id
    await callback.answer()

    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.log_error(f"Не удалось удалить сообщение с ID {previous_message_id}: {e}")

    await state.update_data(subscription_id=subscription_id)
    await state.update_data(status_pay=StatusPay.OLD)

    await callback.message.edit_text(
        text=LEXICON_RU['createorder'],
        reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.OLD, f'view_details_{subscription_id}'),
    )
