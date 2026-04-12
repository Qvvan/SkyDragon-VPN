from abc import ABC, abstractmethod
from decimal import Decimal

from src.domain.entities.payment import Payment


class IPaymentRepository(ABC):
    @abstractmethod
    async def create_pending_payment(
        self,
        payment_id: str,
        confirmation_url: str,
        payment_type: str,
        amount: Decimal,
        user_id: int,
        service_id: int,
        account_id: str | None = None,
        subscription_id: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def find_active_pending_for_account(
        self,
        account_id: str,
        service_id: int,
        payment_type: str | None = None,
    ) -> Payment | None:
        """Возвращает активный pending-платёж (account + service, создан < 1 часа).
        Если передан payment_type — фильтрует ещё и по типу."""
        raise NotImplementedError

    @abstractmethod
    async def find_active_pending_for_subscription(
        self,
        subscription_id: str,
        service_id: int,
    ) -> Payment | None:
        """Возвращает активный pending-платёж (subscription + service, создан < 1 часа)."""
        raise NotImplementedError

    @abstractmethod
    async def list_for_account(self, account_id: str) -> list[Payment]:
        raise NotImplementedError
