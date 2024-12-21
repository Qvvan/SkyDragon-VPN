from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.context_manager import DatabaseContextManager
from handlers.services.card_service import create_payment
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import Payments
from state.state import Gift

router = Router()


class GiftCallback(CallbackData, prefix="gift"):
    action: str
    service_id: str
    receiver_username: str


@router.message(Command(commands="gift_sub"))
async def process_start_command(message: Message, state: FSMContext):
    await message.answer(
        text=(
            "🎁 *Введите @username пользователя, которому хотите подарить подписку* ✨\n\n"
            "🔄 Активная подписка будет продлена, а новая — активируется при входе пользователя! 🕒\n\n"
            "Сделайте этот день особенным! 😊"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="cancel"
                )
            ],
        ])
    )
    await state.set_state(Gift.waiting_username)


@router.callback_query(lambda c: c.data == 'gift_sub')
async def handle_know_more(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        text=(
            "🎁Введите @username пользователя, которому хотите подарить подписку ✨\n\n"
            "🔄 Активная подписка будет продлена, а новая — активируется при входе пользователя! 🕒\n\n"
            "Сделайте этот день особенным! 😊"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="cancel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="main_menu"
                )
            ],
        ])
    )

    await state.set_state(Gift.waiting_username)


@router.message(Gift.waiting_username)
async def handle_know_more(message: Message, state: FSMContext):
    username = message.text
    if not username.startswith('@') or len(username) == 1:
        await message.answer(
            text="Неверный формат @username",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Отмена",
                        callback_data="cancel"
                    )
                ],
            ])
        )
        return
    if username[1:] == message.from_user.username:
        await message.answer(
            text="Нельзя подарить подписку самому себе",
            parse_mode="Markdown"
        )
        return
    username = username[1:]
    await state.update_data(receiver_username=username)
    await message.answer(
        text=LEXICON_RU['gift'],
        reply_markup=await create_order_keyboards(username, "main_menu"),
    )
    await state.clear()


async def create_order_keyboards(receiver_username: str, back_target: str = None) -> InlineKeyboardMarkup:
    """Клавиатура для кнопок с услугами."""
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
                    receiver_username=receiver_username
                ).pack()

                buttons.append(InlineKeyboardButton(text=service_name, callback_data=callback_data))
            keyboard.row(*buttons)

            if back_target:
                keyboard.row(
                    InlineKeyboardButton(text='🔙 Назад', callback_data=back_target)
                )
            else:
                keyboard.row(
                    InlineKeyboardButton(text='Отмена', callback_data='cancel')
                )

            return keyboard.as_markup()
        except Exception as e:
            await logger.log_error(f'Произошла ошибка при формирование услуг', e)


@router.callback_query(GiftCallback.filter(F.action == 'gift'))
async def handle_know_more(callback_query: CallbackQuery, callback_data: GiftCallback):
    service_list = [
        "Краткосрочная мощь духа дракона, дарующая защиту на время одного полного круга луны.",
        "Щит древности, что бережёт вас в течение трёх смен времён года, словно хранитель древних тайн.",
        "Мистический амулет силы, надёжный на долгие месяцы, когда солнце и тьма сменяют друг друга.",
        "Легендарный защитник, символ вечной мощи, что оберегает вас весь круговорот времени, от зимы до лета."
    ]
    receiver_username = callback_data.receiver_username
    service_id = int(callback_data.service_id)
    async with DatabaseContextManager() as session_methods:
        try:
            service = await session_methods.services.get_service_by_id(service_id)
            payment_data = create_payment(
                amount=service.price,
                description=f"Оплата за услугу: {service.name}",
                return_url="https://t.me/SkyDragonVPNBot",
                service_id=service_id,
                service_type="gift",
                receiver_username=receiver_username,
                user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
            )

            payment_url = payment_data['confirmation']['confirmation_url']
            payment_id = payment_data['id']

            payment_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Оплатить",
                            url=payment_url
                        )
                    ],
                ])

            await callback_query.message.edit_text(
                text=(
                    f"<b>Подарок для @{receiver_username}!</b> 🎁\n\n"
                    f"<b>Вы дарите защиту {service.name}а на {service.duration_days} дней</b> 🕒\n\n"
                    f"📋 <b>Услуга:</b> {service_list[service_id - 1]}\n"
                    f"💰 <b>Цена:</b> {service.price} ₽\n\n"
                    f"Нажмите на кнопку ниже для оплаты. После оплаты @{receiver_username} сможет активировать подписку!"
                ),
                parse_mode="HTML",
                reply_markup=payment_kb,
            )
            await session_methods.payments.create_payments(
                Payments(
                    payment_id=payment_id,
                    user_id=callback_query.from_user.id,
                    service_id=service_id
                )
            )
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}'
                                   f'ID: {callback_query.from_user.id}\n'
                                   f'Ошибка при создании платежа', e)
            await callback_query.message.edit_text(text="Что-то пошло не так, обратитесь в техподдержку.")
