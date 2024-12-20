from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, Message

from keyboards.kb_inline import InlineKeyboards, ServiceCallbackFactory
from logger.logging_config import logger


async def send_invoice(
        message: Message,
        price: int,
        description: str,
        service_name: str,
        service_id: int,
        duration_days: int,
        action: str,
        subscription_id: int = None,
        state: FSMContext = None,
        callback_data: ServiceCallbackFactory = None,
        ):
    try:
        prices = [LabeledPrice(label="XTR", amount=price)]
        show_stars_guide = await message.answer(
            text='✨ Вы можете приобрести звёзды у Telegram-бота @PremiumBot, просто введя команду /stars. ⭐'
        )
        await state.update_data(show_stars_guide=show_stars_guide.message_id)

        await message.answer_invoice(
                title=f"Защита {service_name}а на {duration_days} дней",
                description=description,
                prices=prices,
                payload=f"{service_id}:{duration_days}:{action}:{subscription_id}",
                currency="XTR",
                reply_markup=await InlineKeyboards.create_pay(callback_data,price),
                )
    except Exception as e:
        await logger.log_error(f"Ошибка при создании инвойса", e)
        await message.answer("Что-то пошло не так, обратитесь в техподдержку")
