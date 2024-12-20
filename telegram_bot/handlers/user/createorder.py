from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.card_service import create_payment
from handlers.services.invoice_helper import send_invoice
from keyboards.kb_inline import InlineKeyboards, ServiceCallbackFactory, StatusPay, StarsPayCallbackFactory
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import Payments

router = Router()


@router.message(Command(commands='new'))
async def create_order(message: Message, state: FSMContext):
    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subscription(message.from_user.id)
            await state.update_data(status_pay=StatusPay.NEW)
            if subs:
                await message.answer(
                    text="Мы заметили, что у вас уже есть подписка, может вы хотите продлить ее?",
                    reply_markup=await InlineKeyboards.create_or_extend()
                )
            else:
                await message.answer(
                    text=LEXICON_RU['createorder'],
                    reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.NEW),
                    parse_mode="HTML"
                )
        except Exception as e:
            await logger.log_error(f"Error creating order", e)


@router.callback_query(lambda c: c.data == 'subscribe')
async def handle_subscribe(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Оформить подписку' в главном меню."""
    await callback.answer()

    data = await state.get_data()
    back_target = data.get('back_target')
    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subscription(callback.from_user.id)
            if subs:
                await callback.message.edit_text(
                    text="Мы заметили, что у вас уже есть подписка, может вы хотите продлить ее?",
                    reply_markup=await InlineKeyboards.create_or_extend()
                )
            else:
                await callback.message.edit_text(
                    text=LEXICON_RU['createorder'],
                    reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.NEW, back_target=back_target),
                    parse_mode="HTML"
                )
        except Exception as e:
            await logger.log_error(f"Error creating order", e)


@router.callback_query(lambda c: c.data == 'create_order')
async def handle_subscribe(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    back_target = data.get('back_target')

    await callback.message.edit_text(
        text=LEXICON_RU['createorder'],
        reply_markup=await InlineKeyboards.create_order_keyboards(StatusPay.NEW, back_target=back_target),
        parse_mode="HTML"
    )


@router.callback_query(ServiceCallbackFactory.filter())
async def handle_service_callback(callback_query: CallbackQuery, callback_data: ServiceCallbackFactory):
    try:
        await callback_query.message.edit_text("Выберите способ оплаты",
                                               reply_markup=await InlineKeyboards.payment_method(callback_data))
    except:
        await callback_query.message.delete()
        await callback_query.message.answer("Выберите способ оплаты",
                                            reply_markup=await InlineKeyboards.payment_method(callback_data))


@router.callback_query(lambda c: c.data == 'back_to_services')
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_data = await state.get_data()

    show_stars_guide = user_data.get("show_stars_guide")
    if show_stars_guide:
        try:
            await callback.bot.delete_message(callback.message.chat.id, show_stars_guide)
            await state.update_data(show_slow_internet_id=None)
        except Exception as e:
            await logger.error(f"Не удалось удалить сообщение с ID {show_stars_guide}", e)

    status_pay_value = user_data.get('status_pay', StatusPay.NEW.value)

    try:
        status_pay = StatusPay(status_pay_value)
    except ValueError:
        status_pay = StatusPay.NEW

    await callback.message.answer(
        text=LEXICON_RU['createorder'],
        reply_markup=await InlineKeyboards.create_order_keyboards(status_pay),
        parse_mode="HTML"
    )
    await callback.message.delete()


@router.callback_query(StarsPayCallbackFactory.filter(F.action == 'stars_pay'))
async def stars_pay(callback_query: CallbackQuery, callback_data: ServiceCallbackFactory,
                    state: FSMContext):
    service_id = int(callback_data.service_id)
    status_pay = StatusPay(callback_data.status_pay)
    await callback_query.message.delete()
    async with DatabaseContextManager() as session_methods:
        try:
            service = await session_methods.services.get_service_by_id(service_id)
            service_list = ["Краткосрочная мощь духа дракона, дарующая защиту на время одного полного круга луны.",
                            "Щит древности, что бережёт вас в течение трёх смен времён года, словно хранитель древних тайн.",
                            "Мистический амулет силы, надёжный на долгие месяцы, когда солнце и тьма сменяют друг друга.",
                            "Легендарный защитник, символ вечной мощи, что оберегает вас весь круговорот времени, от зимы до лета."
                            ]
            await send_invoice(
                message=callback_query.message,
                price=int(service.price / 2),
                description=service_list[service_id - 1],
                service_name=service.name,
                service_id=service_id,
                duration_days=service.duration_days,
                action=status_pay.value,
                state=state,
                callback_data=callback_data
            )
        except Exception as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}'
                                   f'ID: {callback_query.from_user.id}\n'
                                   f'При формирование кнопки оплаты произошла ошибка', e)
            await callback_query.message.edit_text(text="Что-то пошло не так, обратитесь в техподдержку")


@router.callback_query(StarsPayCallbackFactory.filter(F.action == 'card_pay'))
async def stars_pay(callback_query: CallbackQuery, callback_data: StarsPayCallbackFactory, state: FSMContext):
    service_list = [
        "Краткосрочная мощь духа дракона, дарующая защиту на время одного полного круга луны.",
        "Щит древности, что бережёт вас в течение трёх смен времён года, словно хранитель древних тайн.",
        "Мистический амулет силы, надёжный на долгие месяцы, когда солнце и тьма сменяют друг друга.",
        "Легендарный защитник, символ вечной мощи, что оберегает вас весь круговорот времени, от зимы до лета."
    ]

    service_id = int(callback_data.service_id)
    status_pay = StatusPay(callback_data.status_pay)
    user_data = await state.get_data()
    subscription_id = int(user_data.get('subscription_id')) if user_data.get('subscription_id') else None
    async with DatabaseContextManager() as session_methods:
        try:
            service = await session_methods.services.get_service_by_id(service_id)
            payment_data = create_payment(
                amount=service.price,
                description=f"Оплата за услугу: {service.name}",
                return_url="https://t.me/SkyDragonVPNBot",
                service_id=service_id,
                service_type=status_pay.value,
                user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                subscription_id=subscription_id
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
                    ]
                ])

            await callback_query.message.edit_text(
                text=(
                    f"*Защита {service.name}а на {service.duration_days} дней* 🕒\n\n"
                    f"📋 *Услуга*: {service_list[service_id - 1]}\n"
                    f"💰 *Цена*: `{service.price} ₽`\n\n"
                    f"Нажмите на кнопку ниже для оплаты:"
                ),
                reply_markup=payment_kb,
                parse_mode="Markdown"
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


@router.callback_query(lambda c: c.data == 'empty')
async def back_to_services(callback: CallbackQuery):
    await callback.answer("Soon...", show_alert=True, cache_time=3)
