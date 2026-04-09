from abc import ABC, abstractmethod


class IRedisClient(ABC):
    """Интерфейс Redis клиента."""

    @abstractmethod
    async def setex(self, key: str, seconds: int, value: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *keys: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def lpush(self, key: str, *values: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def brpop(self, *keys: str, timeout: int = 0) -> tuple[str, str] | None:
        raise NotImplementedError

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
