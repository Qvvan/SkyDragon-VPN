from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.subscription_history import SubscriptionHistory


class ISubscriptionHistoryRepository(ABC):
    @abstractmethod
    async def insert(
        self,
        *,
        user_id: int,
        service_id: int,
        start_date: datetime,
        end_date: datetime,
        status: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> int:
        """Возвращает subscription_id (PK истории)."""
        raise NotImplementedError
