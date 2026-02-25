import asyncio
import json
from datetime import timedelta, datetime

import requests
from yookassa import Configuration, Payment

from config_data.config import SHOP_ID, SHOP_API_TOKEN
from database.context_manager import DatabaseContextManager
from handlers.services.create_receipt import create_receipt
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.subscription_service_with_card import SubscriptionsServiceCard
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger

Configuration.account_id = SHOP_ID
Configuration.secret_key = SHOP_API_TOKEN


async def auto_renewal_payment(amount, description, payment_method_id, user_id, username, subscription_id, service_id):
    try:
        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "payment_method_id": payment_method_id,
            "description": description,
            "metadata": {
                "service_id": service_id,
                "service_type": "old",
                "user_id": user_id,
                "username": username,
                "subscription_id": subscription_id
            }
        })
        return json.loads(payment.json())
    except Exception as e:
        return None


async def create_payment(amount, description, return_url, service_id, service_type, user_id, username,
                   subscription_id: int = None, recipient_user_id: int = None):
    payment = Payment.create(
        {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "save_payment_method": True,
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
                "recipient_user_id": recipient_user_id,
                "subscription_id": subscription_id
            }
        }
    )
    return json.loads(payment.json())


async def check_payment_status(payment_id):
    """
    Запрос статуса в YooKassa. При таймауте/недоступности API возвращает None.
    У библиотеки yookassa баг: при ReadTimeout raw_response бывает None → AttributeError.
    """
    try:
        payment_info = Payment.find_one(payment_id)
        return payment_info
    except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout,
            requests.exceptions.ConnectionError) as e:
        await logger.info(
            f"check_payment_status: таймаут/сеть для платежа {payment_id}, повтор позже: {type(e).__name__}"
        )
        return None
    except AttributeError as e:
        # Баг yookassa: при таймауте в __handle_error обращается к raw_response.status_code при raw_response is None
        if "status_code" in str(e) or "NoneType" in str(e):
            await logger.info(
                f"check_payment_status: API недоступен для платежа {payment_id} (таймаут), повтор позже"
            )
            return None
        raise


async def payment_status_checker(bot):
    while True:
        try:
            async with DatabaseContextManager() as session_methods:
                try:
                    unpaid_payments = await session_methods.payments.get_unpaid_payments()

                    for payment in unpaid_payments:
                        try:
                            payment_response = await check_payment_status(payment.payment_id)
                            if payment_response is None:
                                continue
                            if payment_response.status == 'succeeded':
                                user_id = payment.user_id
                                try:
                                    service = await session_methods.services.get_service_by_id(payment.service_id)
                                    receipt_link = await create_receipt(service.name, service.price, service.duration_days)
                                except Exception as e:
                                    receipt_link = None
                                await session_methods.payments.update_payment_status(
                                    payment_id=payment.payment_id,
                                    status='succeeded',
                                    receipt_link=receipt_link
                                )
                                await bot.send_message(chat_id=user_id, text="Платеж успешно прошел!")

                                await successful_payment(bot, payment_response)

                            payment_time_limit = payment.created_at + timedelta(hours=1)
                            if datetime.utcnow() > payment_time_limit:
                                await session_methods.payments.delete_payment(payment.payment_id)
                                continue
                        except Exception as e:
                            await logger.log_error("Ошибка проверки статуса платежа", e)
                    await session_methods.session.commit()
                except Exception as e:
                    await logger.log_error(f"Ошибка проверки статуса платежа", e)
        except Exception as e:
            await logger.log_error(f"Критическая ошибка в payment_status_checker", e)

        await asyncio.sleep(3)


async def successful_payment(bot, payment_response):
    metadata = payment_response.metadata
    service_id = int(metadata.get("service_id"))
    service_type = metadata.get("service_type")
    user_id = int(metadata.get("user_id"))
    username = metadata.get("username", None)
    subscription_id = metadata.get("subscription_id")

    if subscription_id is not None:
        subscription_id = int(subscription_id)
    else:
        subscription_id = -99999
    if service_type == 'new':
        await SubscriptionsServiceCard.process_new_subscription(bot, user_id, username, service_id, payment_response)
    elif service_type == 'old':
        await SubscriptionsServiceCard.extend_sub_successful_payment(bot, user_id, username, subscription_id,
                                                                     service_id, payment_response)
    elif service_type == 'gift':
        recipient_user_id = int(metadata.get("recipient_user_id"))
        await logger.log_info(f"Пользователь: @{username}\nID: {user_id}\n"
                              f"Подарил другу подписку с ID: {recipient_user_id}")
        async with DatabaseContextManager() as session_methods:
            try:
                user = await session_methods.users.get_user(recipient_user_id)
                if not user:
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['gift_thank_you'].format(gift_days=30))
                    await extend_user_subscription(user_id, username, 30, session_methods)
                else:
                    await extend_user_subscription(user_id, username, 10, session_methods)
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['gift_thank_you'].format(gift_days=10))
                await session_methods.session.commit()
            except Exception as e:
                await session_methods.session.rollback()
                await logger.log_error(f"Пользователь: @{username}\nID: {user_id}\nError during transaction processing",
                                       e)
        await SubscriptionsServiceCard.gift_for_friend(user_id, username, recipient_user_id, service_id)
