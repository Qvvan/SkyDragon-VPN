from abc import ABC, abstractmethod

from src.domain.entities.subscription import Subscription


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_user_and_subscription_id(self, user_id: int, subscription_id: int) -> Subscription | None:
        raise NotImplementedError

    @abstractmethod
    async def set_auto_renewal(self, user_id: int, subscription_id: int, enabled: bool) -> bool:
        raise NotImplementedError
