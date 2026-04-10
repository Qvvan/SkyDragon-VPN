from abc import ABC, abstractmethod

from src.domain.entities.subscription import Subscription


class ISubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_principal_and_subscription_id(self, principal_id: int, subscription_id: int) -> Subscription | None:
        """
        principal_id — либо telegram user_id из старых токенов, либо id аккаунта сайта.
        Доступ учитывает связку account_telegram_links и колонку subscriptions.account_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_auto_renewal(self, principal_id: int, subscription_id: int, enabled: bool) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_for_account_owner(self, account_id: int) -> list[Subscription]:
        """Все подписки владельца аккаунта: сайт + телеграм (в т.ч. до бэкфилла account_id)."""
        raise NotImplementedError
