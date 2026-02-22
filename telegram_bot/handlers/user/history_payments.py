from aiogram import Router
from aiogram.types import CallbackQuery

from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import InlineKeyboards
from logger.logging_config import logger

router = Router()


@router.callback_query(lambda c: c.data == 'history_payments')
async def handle_know_more(callback: CallbackQuery):
    await callback.answer()
    async with DatabaseContextManager() as session:
        try:
            payments = await session.payments.get_payments_by_user_id(callback.from_user.id)
            answer = f"Все ваши платежи: {len(payments)}\n\n"
            for payment in payments:
                if payment.status == 'succeeded':
                    service = await session.services.get_service_by_id(payment.service_id)
                    answer += (
                        f"{payment.created_at.strftime('%d-%m-%Y %H:%M')} | {service.name}, {service.duration_days} дн., {service.price} руб.\n"
                        f"{payment.receipt_link if payment.receipt_link else '🚫 Нет чека'}\n\n"
                    )

        except Exception as e:
            await logger.log_error(f"Произошла ошибка при получении истории платежей ID: {callback.from_user.id}", e)
            return

    await callback.message.edit_text(
        text=answer,
        reply_markup=InlineKeyboards.history_payments_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
