import redis.asyncio as aioredis

from src.interfaces.clients.redis.client import IRedisClient


class RedisClient(IRedisClient):
    __slots__ = ("_client", "_url")

    def __init__(self, url: str):
        self._url = url
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._client = await aioredis.from_url(self._url, decode_responses=True)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            await self.connect()
        return self._client

    async def setex(self, key: str, seconds: int, value: str) -> None:
        client = await self._get_client()
        await client.setex(key, seconds, value)

    async def get(self, key: str) -> str | None:
        client = await self._get_client()
        return await client.get(key)

    async def delete(self, *keys: str) -> int:
        client = await self._get_client()
        return await client.delete(*keys)

    async def lpush(self, key: str, *values: str) -> int:
        client = await self._get_client()
        return await client.lpush(key, *values)

    async def brpop(self, *keys: str, timeout: int = 0) -> tuple[str, str] | None:
        client = await self._get_client()
        result = await client.brpop(list(keys), timeout=timeout)
        if result is None:
            return None
        queue_name, value = result
        return str(queue_name), str(value)
