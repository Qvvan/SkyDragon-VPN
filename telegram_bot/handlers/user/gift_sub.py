import asyncio

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, \
    KeyboardButtonRequestUsers, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from handlers.services.card_service import create_payment
from keyboards.kb_inline import InlineKeyboards, BACK_BTN, MAIN_MENU_BTN, MAIN_MENU_CB
from logger.logging_config import logger
from models.models import Payments
from utils.gift_checker import activate_gift_handler

router = Router()

activation_locks = {}


class GiftCallback(CallbackData, prefix="gift"):
    action: str
    service_id: str
    sender_user_id: int
    recipient_user_id: int


@router.message(Command(commands="gift_sub"))
async def process_start_command(message: Message, state: FSMContext):
    select_user_button = KeyboardButton(
        text="🎁 Выбрать получателя подарка",
        request_users=KeyboardButtonRequestUsers(
            request_id=1,  # Уникальный ID запроса
            user_is_bot=False,  # Только обычные пользователи, не боты
            max_quantity=1,  # Максимальное количество пользователей для выбора
            request_name=True,  # Запрашиваем имя пользователя
            request_username=True,  # Запрашиваем username
            request_photo=False  # Не запрашиваем фото профиля
        )
    )

    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[select_user_button]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await message.answer(
        "🎁Нажми на кнопку ниже, чтобы выбрать получателя подарка ✨\n\n"
        "🔄 Активная подписка будет продлена, а новая — активируется при входе пользователя! 🕒",
        reply_markup=keyboard
    )


@router.message(F.users_shared)
async def handle_users_shared(message: Message):
    users_shared = message.users_shared

    # Проверяем ID запроса
    if users_shared.request_id == 1:
        # Получаем информацию о выбранном пользователе
        selected_user = users_shared.users[0]  # Берем первого (у нас max_quantity=1)

        recipient_user_id = selected_user.user_id
        sender_user_id = message.from_user.id
        first_name = selected_user.first_name or "Неизвестно"
        username = selected_user.username or "Не указан"

        # Одно сообщение: текст + клавиатура с услугами (убираем reply-клавиатуру тем же сообщением нельзя)
        await message.answer(
            "✅ Получатель подарка выбран!\n\n"
            f"👤 Имя: {first_name}\n"
            f"🔗 Username: @{username if username != 'Не указан' else 'Не указан'}\n\n"
            "Теперь выберите подарочную подписку:",
            reply_markup=await create_order_keyboards(sender_user_id=sender_user_id,
                                                      recipient_user_id=recipient_user_id)
        )


def _gift_reply_keyboard():
    select_user_button = KeyboardButton(
        text="🎁 Выбрать получателя подарка",
        request_users=KeyboardButtonRequestUsers(
            request_id=1,
            user_is_bot=False,
            max_quantity=1,
            request_name=True,
            request_username=True,
            request_photo=False
        )
    )
    return ReplyKeyboardMarkup(
        keyboard=[[select_user_button]],
        resize_keyboard=True,
        one_time_keyboard=False
    )


GIFT_TEXT = (
    "🎁 **Подарить подписку**\n\n"
    "Нажмите кнопку **«Выбрать получателя подарка»** под полем ввода.\n\n"
    "🔄 Активная подписка будет продлена, а новая активируется при входе пользователя.\n\n"
    "Сделайте этот день особенным! 😊"
)


@router.callback_query(lambda c: c.data == 'gift_sub')
async def handle_know_more(callback: CallbackQuery):
    await callback.answer()
    reply_kb = _gift_reply_keyboard()
    await callback.message.delete()
    await callback.message.answer(
        "👇 Нажмите кнопку ниже, чтобы выбрать получателя:",
        reply_markup=reply_kb
    )
    await callback.message.answer(
        GIFT_TEXT,
        reply_markup=InlineKeyboards.row_main_menu(),
        parse_mode="Markdown"
    )



async def create_order_keyboards(sender_user_id: int, recipient_user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для кнопок с услугами + Назад и Главное меню."""
    async with DatabaseContextManager() as session_methods:
        try:
            keyboard = InlineKeyboardBuilder()
            services = await session_methods.services.get_services()
            buttons: list[InlineKeyboardButton] = []

            for service in services:
                service_id = str(service.service_id)
                service_name = service.name

                callback_data = GiftCallback(
                    action="gift",
                    service_id=service_id,
                    sender_user_id=sender_user_id,
                    recipient_user_id=recipient_user_id
                ).pack()

                buttons.append(InlineKeyboardButton(text=service_name, callback_data=callback_data))
            keyboard.row(*buttons)
            keyboard.row(InlineKeyboardButton(text=BACK_BTN, callback_data="gift_sub"))
            keyboard.row(InlineKeyboardButton(text=MAIN_MENU_BTN, callback_data=MAIN_MENU_CB))

            return keyboard.as_markup()
        except Exception as e:
            await logger.log_error(f'Произошла ошибка при формирование услуг', e)


@router.callback_query(GiftCallback.filter(F.action == 'gift'))
async def handle_gift_payment(callback_query: CallbackQuery, callback_data: GiftCallback):
    service_id = int(callback_data.service_id)
    sender_user_id = callback_data.sender_user_id
    recipient_user_id = callback_data.recipient_user_id

    async with DatabaseContextManager() as session_methods:
        try:
            await callback_query.answer()
            service = await session_methods.services.get_service_by_id(service_id)
            payment_data = await create_payment(
                amount=service.price,
                description=f"Подарочная подписка: {service.name}",
                return_url="https://t.me/SkyDragonVPNBot",
                service_id=service_id,
                service_type="gift",
                user_id=sender_user_id,
                recipient_user_id=recipient_user_id,
                username=callback_query.from_user.username,
            )

            payment_url = payment_data['confirmation']['confirmation_url']
            payment_id = payment_data['id']

            payment_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💳 Оплатить подарок",
                            url=payment_url
                        )
                    ],
                    [InlineKeyboardButton(text=BACK_BTN, callback_data="gift_sub")],
                    [InlineKeyboardButton(text=MAIN_MENU_BTN, callback_data=MAIN_MENU_CB)],
                ])

            await callback_query.message.edit_text(
                text=(
                    f"🎁 <b>Подарочная подписка {service.name}</b>\n\n"
                    f"⏳ <b>Длительность:</b> {service.duration_days} дней\n"
                    f"💰 <b>Цена:</b> {service.price} ₽\n\n"
                ),
                parse_mode="HTML",
                reply_markup=payment_kb,
            )

            await session_methods.payments.create_payments(
                Payments(
                    payment_id=payment_id,
                    user_id=callback_query.from_user.id,
                    recipient_user_id=recipient_user_id,
                    service_id=service_id,
                    payment_type='gift',
                )
            )
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}'
                                   f'ID: {callback_query.from_user.id}\n'
                                   f'Ошибка при создании платежа для подарка', e)
            await callback_query.message.edit_text(
                text="Что-то пошло не так, обратитесь в техподдержку.",
                reply_markup=InlineKeyboards.row_main_menu()
            )


@router.callback_query(F.data.startswith("activate_gift_"))
async def handle_gift_activation(callback_query: CallbackQuery):
    """Обработчик активации подарков с блокировкой"""
    try:
        # Извлекаем ID подарка из callback_data
        gift_id = int(callback_query.data.split("_")[-1])
        user_id = callback_query.from_user.id

        # Создаем уникальный ключ для блокировки
        lock_key = f"gift_{gift_id}_{user_id}"

        # Проверяем, не активируется ли уже этот подарок
        if lock_key in activation_locks:
            await callback_query.answer("⏳ Подарок уже активируется, подождите...", show_alert=True)
            return

        # Устанавливаем блокировку
        activation_locks[lock_key] = True

        try:
            # Получаем бота из callback_query
            bot = callback_query.bot

            # Вызываем функцию активации подарка
            await activate_gift_handler(bot, callback_query, gift_id)

        finally:
            # Убираем блокировку в любом случае
            activation_locks.pop(lock_key, None)

    except (ValueError, IndexError) as e:
        await callback_query.answer("❌ Некорректный формат данных", show_alert=True)
    except Exception as e:
        # Убираем блокировку в случае ошибки
        lock_key = f"gift_{callback_query.data.split('_')[-1]}_{callback_query.from_user.id}"
        activation_locks.pop(lock_key, None)
        await callback_query.answer("❌ Произошла ошибка", show_alert=True)
