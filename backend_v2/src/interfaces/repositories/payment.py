from abc import ABC, abstractmethod

from src.domain.entities.payment import Payment


class IPaymentRepository(ABC):
    @abstractmethod
    async def create_pending_payment(
        self,
        payment_id: str,
        user_id: int,
        service_id: int,
        account_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_account(self, account_id: str) -> list[Payment]:
        raise NotImplementedError
