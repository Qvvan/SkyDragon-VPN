from abc import ABC, abstractmethod

from src.domain.entities.subscription import Subscription


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_principal_and_subscription_id(self, principal_id: str, subscription_id: str) -> Subscription | None:
        """
        principal_id — account UUID from site auth.
        Subscription ownership is checked via account_id and account_telegram_links.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_auto_renewal(self, principal_id: str, subscription_id: str, enabled: bool) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_for_account_owner(self, account_id: str) -> list[Subscription]:
        """All subscriptions owned by the account: direct + linked telegram."""
        raise NotImplementedError

    @abstractmethod
    async def has_used_trial(self, account_id: str) -> bool:
        """Returns True if the account has any trial subscription."""
        raise NotImplementedError

    @abstractmethod
    async def create_for_account(
        self,
        *,
        account_id: str,
        telegram_user_id: int,
        service_id: int,
        duration_days: int,
    ) -> Subscription:
        """Creates subscription directly (without payment). telegram_user_id=0 if telegram not linked."""
        raise NotImplementedError
