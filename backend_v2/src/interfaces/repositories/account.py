from abc import ABC, abstractmethod

from src.domain.entities.account import Account


class IAccountRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        email: str | None,
        phone: str | None,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> Account:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, account_id: int) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email_lower(self, email_lower: str) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def update_profile(
        self,
        *,
        account_id: int,
        first_name: str | None,
        last_name: str | None,
    ) -> Account:
        raise NotImplementedError
