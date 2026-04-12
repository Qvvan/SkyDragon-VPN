from decimal import Decimal

from src.core.exceptions import NotFoundError, ValidationError
from src.interfaces.clients.payment.client import IPaymentGatewayClient
from src.interfaces.repositories.payment import IPaymentRepository
from src.interfaces.repositories.service_plan import IServicePlanRepository
from src.interfaces.services.token_codec import ITokenCodec


class PaymentService:
    __slots__ = ("_telegram_yookassa_return_url", "_service_repo", "_payment_repo", "_gateway", "_token_codec")

    def __init__(
        self,
        telegram_yookassa_return_url: str,
        service_repo: IServicePlanRepository,
        payment_repo: IPaymentRepository,
        gateway: IPaymentGatewayClient | None,
        token_codec: ITokenCodec,
    ) -> None:
        self._telegram_yookassa_return_url = telegram_yookassa_return_url
        self._service_repo = service_repo
        self._payment_repo = payment_repo
        self._gateway = gateway
        self._token_codec = token_codec

    async def create_payment_for_account(self, account_id: str, service_id: int) -> str:
        """Создаёт платёж за новую подписку (payment_type = subscription)."""
        if service_id <= 0:
            raise ValidationError("Invalid service_id")
        if self._gateway is None:
            raise ValidationError("Оплата не настроена")

        existing = await self._payment_repo.find_active_pending_for_account(account_id, service_id)
        if existing is not None and existing.confirmation_url:
            return existing.confirmation_url

        service = await self._service_repo.get_by_id(service_id)
        if service is None:
            raise NotFoundError("Услуга не найдена")

        result = await self._gateway.create_payment(
            amount=service.price,
            service_id=service_id,
            service_name=service.name,
            user_id=0,
            subscription_id=0,
            return_url=self._telegram_yookassa_return_url,
        )
        await self._payment_repo.create_pending_payment(
            payment_id=result.payment_id,
            confirmation_url=result.confirmation_url,
            payment_type="subscription",
            amount=Decimal(service.price),
            user_id=0,
            service_id=service_id,
            account_id=account_id,
        )
        return result.confirmation_url

    async def create_renewal_payment_for_account(
        self,
        account_id: str,
        subscription_id: str,
        service_id: int,
    ) -> str:
        """Создаёт платёж за продление подписки из веб-интерфейса (payment_type = renewal)."""
        if service_id <= 0:
            raise ValidationError("Invalid service_id")
        if self._gateway is None:
            raise ValidationError("Оплата не настроена")

        existing = await self._payment_repo.find_active_pending_for_subscription(subscription_id, service_id)
        if existing is not None and existing.confirmation_url:
            return existing.confirmation_url

        service = await self._service_repo.get_by_id(service_id)
        if service is None:
            raise NotFoundError("Услуга не найдена")

        result = await self._gateway.create_payment(
            amount=service.price,
            service_id=service_id,
            service_name=service.name,
            user_id=0,
            subscription_id=0,
            return_url=self._telegram_yookassa_return_url,
        )
        await self._payment_repo.create_pending_payment(
            payment_id=result.payment_id,
            confirmation_url=result.confirmation_url,
            payment_type="renewal",
            amount=Decimal(service.price),
            user_id=0,
            service_id=service_id,
            account_id=account_id,
            subscription_id=subscription_id,
        )
        return result.confirmation_url

    async def create_payment_for_renewal(self, encrypted_part: str, service_id: int) -> str:
        """Создаёт платёж за продление подписки (payment_type = renewal)."""
        if service_id <= 0:
            raise ValidationError("Invalid service_id")
        if self._gateway is None:
            raise ValidationError("Payment is not configured")

        try:
            user_id, subscription_id = self._token_codec.decrypt(encrypted_part)
        except Exception as exc:
            raise ValidationError("Invalid encryption") from exc

        existing = await self._payment_repo.find_active_pending_for_subscription(subscription_id, service_id)
        if existing is not None and existing.confirmation_url:
            return existing.confirmation_url

        service = await self._service_repo.get_by_id(service_id)
        if service is None:
            raise NotFoundError("Service not found")

        result = await self._gateway.create_payment(
            amount=service.price,
            service_id=service_id,
            service_name=service.name,
            user_id=user_id,
            subscription_id=subscription_id,
            return_url=self._telegram_yookassa_return_url,
        )
        await self._payment_repo.create_pending_payment(
            payment_id=result.payment_id,
            confirmation_url=result.confirmation_url,
            payment_type="renewal",
            amount=Decimal(service.price),
            user_id=user_id,
            service_id=service_id,
            subscription_id=str(subscription_id),
        )
        return result.confirmation_url

    async def list_payments_for_account(self, account_id: str) -> list:
        return await self._payment_repo.list_for_account(account_id)
