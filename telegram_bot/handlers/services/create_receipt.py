from datetime import datetime, timezone
from config_data.config import INN
from database.context_manager import DatabaseContextManager
from logger.logging_config import logger
import requests

# Твои данные
TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ7XCJhdXRoVHlwZVwiOlwiU01TXCIsXCJmaWRcIjoxMDAwNzI4MTA4NzIsXCJsb2dpblwiOlwiNzk2NDAzMDk3OTVcIixcImlkXCI6MjM0ODk1OTYsXCJkZXZpY2VJZFwiOlwiQXNWTU5VdjU4aWJSNzZaSHAxV05WXCIsXCJvcGVyYXRvcklkXCI6bnVsbCxcImNzdWRVc2VybmFtZVwiOm51bGwsXCJzZWdtZW50c1wiOltdLFwiZmlyc3RTZWdtZW50XCI6bnVsbH0iLCJleHAiOjE3Mzg0MTE4NDV9.gdgaQ_irVxNaBTGZBNaqqMp-n7MsO64WN6QLeIY_cKr3S8RcVnMnfr9jiOGqo2r3SuPaToZZfIi6GGfxblKUUA"
# URL API ФНС
API_URL = "https://lknpd.nalog.ru/api/v1/income"

# Заголовки для запроса
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


async def generate_receipt(service_name, amount, duration_days, quantity=1, payment_type="CASH"):
    """ Отправляет данные в API ФНС и получает UUID чека """

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Формируем JSON для запроса
    payload = {
        "operationTime": now,
        "requestTime": now,
        "paymentType": payment_type,  # "CASH" (наличные) или "TRANSFER" (перевод на карту)
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

    # Отправляем запрос
    response = requests.post(API_URL, headers=HEADERS, json=payload)

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
