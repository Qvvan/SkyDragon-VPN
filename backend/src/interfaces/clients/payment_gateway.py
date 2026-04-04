from abc import ABC, abstractmethod


class IPaymentGateway(ABC):
    @abstractmethod
    async def create_renewal_payment(
        self,
        *,
        amount_rub: int,
        service_id: int,
        service_name: str,
        user_id: int,
        subscription_id: int,
    ) -> tuple[str, str]:
        """Возвращает (payment_id, confirmation_url)."""
        raise NotImplementedError
