from abc import ABC, abstractmethod

from src.domain.entities.account import Account


class IAccountRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        login: str,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> Account:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, account_id: str) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_login(self, login: str) -> Account | None:
        raise NotImplementedError

    @abstractmethod
    async def update_profile(
        self,
        *,
        account_id: str,
        first_name: str | None,
        last_name: str | None,
    ) -> Account:
        raise NotImplementedError
