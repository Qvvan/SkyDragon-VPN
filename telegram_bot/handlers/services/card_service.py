import asyncio
import json
from datetime import timedelta, datetime

from yookassa import Configuration, Payment

from config_data.config import SHOP_ID, SHOP_API_TOKEN
from database.context_manager import DatabaseContextManager
from handlers.services.subscription_service_with_card import SubscriptionsServiceCard
from logger.logging_config import logger

Configuration.account_id = SHOP_ID
Configuration.secret_key = SHOP_API_TOKEN


def create_payment(amount, description, return_url, service_id, service_type, user_id, username,
                   subscription_id: int = None):
    payment = Payment.create(
        {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "save_payment_method": False,
            "description": description,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "metadata": {
                "service_id": service_id,
                "service_type": service_type,
                "user_id": user_id,
                "username": username,
                "subscription_id": subscription_id
            }
        }
    )
    return json.loads(payment.json())


async def check_payment_status(payment_id):
    payment_info = Payment.find_one(payment_id)
    return payment_info


async def payment_status_checker(bot):
    while True:
        async with DatabaseContextManager() as session_methods:
            try:
                unpaid_payments = await session_methods.payments.get_unpaid_payments()

                for payment in unpaid_payments:
                    payment_time_limit = payment.created_at + timedelta(hours=1)
                    if datetime.utcnow() > payment_time_limit:
                        await session_methods.payments.delete_payment(payment.payment_id)
                        await session_methods.session.commit()
                        continue

                    payment_response = await check_payment_status(payment.payment_id)
                    if payment_response.status == 'succeeded':
                        user_id = payment.user_id
                        await session_methods.payments.update_payment_status(payment.payment_id, 'succeeded')
                        await bot.send_message(chat_id=user_id, text="Платеж успешно прошел!")
                        await session_methods.session.commit()

                        await successful_payment(bot, payment_response)
            except Exception as e:
                await logger.log_error(f"Ошибка проверки статуса платежа", e)

        await asyncio.sleep(3)


async def successful_payment(bot, payment_response):
    metadata = payment_response.metadata
    service_id = int(metadata.get("service_id"))
    service_type = metadata.get("service_type")
    user_id = int(metadata.get("user_id"))
    username = metadata.get("username")
    subscription_id = metadata.get("subscription_id")

    if subscription_id is not None:
        subscription_id = int(subscription_id)
    else:
        subscription_id = -99999
    if service_type == 'new':
        await SubscriptionsServiceCard.process_new_subscription(bot, user_id, username, service_id)
    elif service_type == 'old':
        await SubscriptionsServiceCard.extend_sub_successful_payment(bot, user_id, username, subscription_id,
                                                                     service_id)