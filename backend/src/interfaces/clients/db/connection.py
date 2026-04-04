from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from typing import Any


class IDBConnector(ABC):
    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_connection(self) -> AbstractAsyncContextManager[Any]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
