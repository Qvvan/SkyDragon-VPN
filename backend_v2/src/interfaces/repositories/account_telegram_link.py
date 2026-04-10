from abc import ABC, abstractmethod
from datetime import datetime


class IAccountTelegramLinkRepository(ABC):
    @abstractmethod
    async def get_account_id_by_telegram(self, telegram_user_id: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    async def get_telegram_id_by_account(self, account_id: int) -> int | None:
        raise NotImplementedError

    @abstractmethod
    async def replace_link_code(self, account_id: int, code: str, expires_at: datetime) -> None:
        """Удаляет предыдущие коды аккаунта и сохраняет новый (до подтверждения ботом)."""
        raise NotImplementedError

    @abstractmethod
    async def peek_valid_link_code(self, code: str) -> int | None:
        """Проверяет код без удаления (перед проверкой конфликтов привязки)."""
        raise NotImplementedError

    @abstractmethod
    async def take_valid_link_code(self, code: str) -> int | None:
        """Атомарно удаляет валидный код и возвращает account_id."""
        raise NotImplementedError

    @abstractmethod
    async def insert_link(self, telegram_user_id: int, account_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def backfill_subscriptions_account_id(self, account_id: int, telegram_user_id: int) -> None:
        raise NotImplementedError
