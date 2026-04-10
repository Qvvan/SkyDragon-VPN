import asyncio
import uuid

from src.domain.entities.payment import PaymentCreateResult
from src.interfaces.clients.payment.client import IPaymentGatewayClient

try:
    from yookassa import Configuration, Payment
except Exception:  # pragma: no cover
    Configuration = None
    Payment = None


class YooKassaPaymentGatewayClient(IPaymentGatewayClient):
    __slots__ = ("_account_id", "_secret_key")

    def __init__(self, account_id: str, secret_key: str) -> None:
        self._account_id = account_id
        self._secret_key = secret_key

    async def create_payment(
        self,
        amount: int,
        service_id: int,
        service_name: str,
        user_id: int,
        subscription_id: int,
        return_url: str,
    ) -> PaymentCreateResult:
        if not Configuration or not Payment:
            raise RuntimeError("YooKassa SDK is not available")
        Configuration.account_id = self._account_id
        Configuration.secret_key = self._secret_key
        payload = {
            "amount": {"value": amount, "currency": "RUB"},
            "capture": True,
            "save_payment_method": True,
            "description": f"Оплата за услугу: {service_name}",
            "confirmation": {"type": "redirect", "return_url": return_url},
            "metadata": {
                "service_id": service_id,
                "service_type": "old",
                "user_id": user_id,
                "username": "",
                "recipient_user_id": None,
                "subscription_id": subscription_id,
            },
        }
        payment = await asyncio.to_thread(Payment.create, payload, str(uuid.uuid4()))
        return PaymentCreateResult(payment_id=str(payment.id), confirmation_url=str(payment.confirmation.confirmation_url))
