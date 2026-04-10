from abc import ABC, abstractmethod


class IPaymentRepository(ABC):
    @abstractmethod
    async def create_pending_payment(self, payment_id: str, user_id: int, service_id: int) -> None:
        raise NotImplementedError
