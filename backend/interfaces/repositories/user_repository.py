from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def insert(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_fields(self, user_id: int, **fields: Any) -> None:
        """Только ключи из allowlist: username, ban, trial_used, reminder_trial_sub, last_visit."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, *, limit: int = 5000, offset: int = 0) -> list[User]:
        raise NotImplementedError
