from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.gift import Gift


class IGiftRepository(ABC):
    @abstractmethod
    async def list_ordered(
        self,
        *,
        recipient_user_id: int | None = None,
        limit: int = 500,
    ) -> list[Gift]:
        raise NotImplementedError

    @abstractmethod
    async def list_pending(self) -> list[Gift]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, gift_id: int) -> Gift | None:
        raise NotImplementedError

    @abstractmethod
    async def insert(
        self,
        *,
        giver_id: int,
        recipient_user_id: int,
        service_id: int | None,
        status: str = "pending",
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def update_fields(self, gift_id: int, **fields: str | int | datetime | None) -> None:
        """Допустимые ключи: status, activated_at, service_id."""
        raise NotImplementedError
