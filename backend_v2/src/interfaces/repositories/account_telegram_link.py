from abc import ABC, abstractmethod


class IAccountTelegramLinkRepository(ABC):
    @abstractmethod
    async def get_account_id_by_telegram(self, telegram_user_id: int) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def get_telegram_id_by_account(self, account_id: str) -> int | None:
        raise NotImplementedError

    @abstractmethod
    async def insert_link(self, telegram_user_id: int, account_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def backfill_subscriptions_account_id(self, account_id: str, telegram_user_id: int) -> None:
        raise NotImplementedError
