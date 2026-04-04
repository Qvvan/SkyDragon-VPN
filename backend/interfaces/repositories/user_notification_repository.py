from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class IUserNotificationRepository(ABC):
    @abstractmethod
    async def insert(
        self,
        *,
        user_id: int,
        notification_type: str,
        subscription_id: int | None = None,
        message: str | None = None,
        additional_data: dict[str, Any] | None = None,
        status: str = "active",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> int:
        """RETURNING id (нужен DEFAULT/sequence на колонке id в БД)."""
        raise NotImplementedError

    @abstractmethod
    async def get_last_by_subscription_and_type(
        self,
        subscription_id: int,
        notification_type: str,
    ) -> dict[str, Any] | None:
        """Сырой row как dict (удобно до появления отдельного read-метода)."""
        raise NotImplementedError

    @abstractmethod
    async def get_last_by_user_and_type(
        self,
        user_id: int,
        notification_type: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def update_fields(
        self,
        notification_id: int,
        *,
        status: str | None = None,
        message: str | None = None,
        additional_data: dict[str, Any] | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self, *, user_id: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def delete_before(self, cutoff: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, notification_id: int) -> bool:
        raise NotImplementedError
