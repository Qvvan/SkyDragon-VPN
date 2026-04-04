import asyncio
from typing import Any

from yookassa import Configuration, Payment

from core.config import YookassaConfig
from interfaces.clients.payment_gateway import IPaymentGateway


class YookassaPaymentGateway(IPaymentGateway):
    __slots__ = ("_cfg",)

    def __init__(self, config: YookassaConfig) -> None:
        self._cfg = config
        sid = (config.SHOP_ID or "").strip()
        secret = config.SECRET_KEY.get_secret_value().strip() if config.SECRET_KEY else ""
        if sid and secret:
            Configuration.account_id = sid
            Configuration.secret_key = secret

    def _configured(self) -> bool:
        return bool((self._cfg.SHOP_ID or "").strip() and self._cfg.SECRET_KEY.get_secret_value().strip())

    async def create_renewal_payment(
        self,
        *,
        amount_rub: int,
        service_id: int,
        service_name: str,
        user_id: int,
        subscription_id: int,
    ) -> tuple[str, str]:
        if not self._configured():
            raise RuntimeError("YooKassa не настроена")

        payload: dict[str, Any] = {
            "amount": {"value": f"{int(amount_rub)}.00", "currency": "RUB"},
            "capture": True,
            "save_payment_method": True,
            "description": f"Оплата за услугу: {service_name}",
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/SkyDragonVPNBot",
            },
            "metadata": {
                "service_id": service_id,
                "service_type": "old",
                "user_id": user_id,
                "username": "",
                "recipient_user_id": None,
                "subscription_id": subscription_id,
            },
        }

        def _sync() -> dict[str, Any]:
            return Payment.create(payload)

        payment = await asyncio.to_thread(_sync)
        payment_id = str(payment.id)
        confirmation_url = str(payment.confirmation.confirmation_url)
        return payment_id, confirmation_url
