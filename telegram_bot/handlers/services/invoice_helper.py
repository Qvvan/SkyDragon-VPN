from aiogram.types import LabeledPrice, Message

from keyboards.kb_inline import InlineKeyboards
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
        ):
    try:
        prices = [LabeledPrice(label="XTR", amount=price)]
        await message.answer_invoice(
                title=f"Защита {service_name}а на {duration_days} дней",
                description=description + '\n\n1 звезда ~ 2.09 рубля',
                prices=prices,
                payload=f"{service_id}:{duration_days}:{action}:{subscription_id}",
                currency="XTR",
                reply_markup=await InlineKeyboards.create_pay(price),
                )
    except Exception as e:
        await logger.log_error(f"Ошибка при создании инвойса", e)
        await message.answer("Что-то пошло не так, обратитесь в техподдержку")
