from abc import ABC, abstractmethod
from typing import Any


class IQueryExecutor(ABC):
    @abstractmethod
    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_row(self, query: str, *args: Any) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, query: str, *args: Any) -> str:
        raise NotImplementedError
