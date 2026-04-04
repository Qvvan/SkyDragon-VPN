from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import quote_plus

import asyncpg

from core.logger import AppLogger
from interfaces.clients.db.connection import IDBConnector


def normalize_postgres_dsn(raw: str) -> str:
    u = raw.strip().replace("postgresql+asyncpg://", "postgresql://")
    u = u.replace("postgres://", "postgresql://")
    return u


class PostgresConnectionPool(IDBConnector):
    __slots__ = ("_dsn", "_logger", "_pool", "echo", "max_overflow", "pool_size")

    def __init__(
        self,
        *,
        dsn: str | None = None,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        app_logger: AppLogger,
    ) -> None:
        if dsn and dsn.strip():
            self._dsn = normalize_postgres_dsn(dsn)
        elif host and database and user is not None and password is not None:
            self._dsn = (
                f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
                f"@{host}:{port or 5432}/{database}"
            )
        else:
            raise ValueError("Нужен dsn или набор host/database/user/password")
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._logger = app_logger
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        async def init_connection(connection: asyncpg.Connection) -> None:
            await connection.set_type_codec(
                "uuid",
                encoder=str,
                decoder=str,
                schema="pg_catalog",
            )

        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=max(1, self.pool_size // 2),
            max_size=self.pool_size + self.max_overflow,
            command_timeout=10,
            statement_cache_size=1024,
            init=init_connection,
            server_settings={"timezone": "Europe/Moscow"},
        )
        if self.echo:
            self._logger.info("Database pool created (asyncpg)", pool_max=self.pool_size + self.max_overflow)

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self._pool:
            await self.connect()
        assert self._pool is not None
        async with self._pool.acquire() as connection:
            yield connection

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
