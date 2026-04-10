from src.core.config import Config
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

    async def create_payment_for_renewal(self, encrypted_part: str, service_id: int) -> str:
        if service_id <= 0:
            raise ValidationError("Invalid service_id")
        if self._gateway is None:
            raise ValidationError("Payment is not configured")

        try:
            user_id, subscription_id = self._token_codec.decrypt(encrypted_part)
        except Exception as exc:
            raise ValidationError("Invalid encryption") from exc

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
        await self._payment_repo.create_pending_payment(result.payment_id, user_id, service_id)
        return result.confirmation_url
