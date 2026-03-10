import asyncio
from datetime import datetime, timezone

import requests

from config_data.config import INN
from handlers.services.get_session import get_valid_token
from logger.logging_config import logger

API_URL = "https://lknpd.nalog.ru/api/v1/income"


async def generate_receipt(service_name, amount, duration_days, quantity=1, payment_type="CASH"):
    """ Отправляет данные в API ФНС и получает UUID чека """

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Формируем JSON для запроса
    payload = {
        "operationTime": now,
        "requestTime": now,
        "paymentType": payment_type,
        "totalAmount": str(amount),
        "services": [
            {
                "name": service_name + " (" + str(duration_days) + " дней)",
                "amount": amount,
                "quantity": quantity
            }
        ],
        "client": {
            "contactPhone": None,
            "displayName": None,
            "inn": None,
            "incomeType": "FROM_INDIVIDUAL"
        },
        "ignoreMaxTotalIncomeRestriction": False
    }

    # Синхронные вызовы в потоке, чтобы не блокировать event loop
    token_data = await asyncio.to_thread(get_valid_token)
    TOKEN = token_data.get("token", None)

    HEADERS = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def _do_post():
        return requests.post(API_URL, headers=HEADERS, json=payload)

    response = await asyncio.to_thread(_do_post)

    if response.status_code == 200:
        data = response.json()
        receipt_uuid = data.get("approvedReceiptUuid")
        if receipt_uuid:
            await logger.log_info(f"✅ Чек успешно создан! UUID: {receipt_uuid}")
            return receipt_uuid
        else:
            await logger.log_error("❌ Ошибка: не удалось получить UUID чека", None)
    else:
        await logger.log_error(f"❌ Ошибка запроса: {response.status_code}, {response.text}", None)

    return None


async def get_receipt_link(receipt_uuid):
    """ Формирует ссылку на чек для клиента """
    if receipt_uuid:
        receipt_url = f"https://lknpd.nalog.ru/api/v1/receipt/{INN}/{receipt_uuid}/print"
        await logger.info(f"📄 Ссылка на чек: {receipt_url}")
        return receipt_url
    else:
        await logger.log_error(f"❌ Не удалось сформировать ссылку на чек с uuid: {receipt_uuid}", None)
        return None


# Пример использования
async def create_receipt(service_name: str, amount: int, duration_days: int):
    receipt_uuid = await generate_receipt(service_name, amount, duration_days)

    if receipt_uuid:
        return await get_receipt_link(receipt_uuid)
