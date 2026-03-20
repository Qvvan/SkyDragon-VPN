from datetime import datetime, timezone
import asyncio

import requests

from config_data.config import INN
from handlers.services.get_session import get_valid_token
from logger.logging_config import logger

API_URL = "https://lknpd.nalog.ru/api/v1/income"

# Чтобы запросы к ФНС не зависали бесконечно и не "замораживали" бота,
# если они окажутся выполнены не в потоке.
REQUEST_TIMEOUT = (5, 20)  # (connect, read) seconds


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

    def _generate_receipt_sync():
        token_data = get_valid_token()
        token = token_data.get("token", None)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)

        if response.status_code != 200:
            return {"ok": False, "error": f"HTTP {response.status_code}", "details": response.text}

        data = response.json()
        receipt_uuid = data.get("approvedReceiptUuid")
        if not receipt_uuid:
            return {"ok": False, "error": "Missing approvedReceiptUuid", "details": data}

        return {"ok": True, "receipt_uuid": receipt_uuid}

    # requests синхронный -> переносим в thread, чтобы не блокировать event loop
    result = await asyncio.to_thread(_generate_receipt_sync)
    if result.get("ok"):
        receipt_uuid = result["receipt_uuid"]
        await logger.log_info(f"✅ Чек успешно создан! UUID: {receipt_uuid}")
        return receipt_uuid

    await logger.log_error(f"❌ Ошибка запроса ФНС: {result.get('error')}, {result.get('details')}", None)
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
