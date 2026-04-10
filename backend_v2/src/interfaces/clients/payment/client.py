from abc import ABC, abstractmethod

from src.domain.entities.payment import PaymentCreateResult


class IPaymentGatewayClient(ABC):
    @abstractmethod
    async def create_payment(
        self,
        amount: int,
        service_id: int,
        service_name: str,
        user_id: int,
        subscription_id: int,
        return_url: str,
    ) -> PaymentCreateResult:
        raise NotImplementedError
