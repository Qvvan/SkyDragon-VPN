from abc import ABC, abstractmethod
from typing import Any

import asyncpg


class IQueryExecutor(ABC):

    @abstractmethod
    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_row(self, query: str, *args: Any) -> asyncpg.Record | None:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, query: str, *args: Any) -> str:
        raise NotImplementedError
