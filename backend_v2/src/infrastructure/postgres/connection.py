from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg

from src.core.logger import AppLogger
from src.interfaces.clients.db.connection import IDBConnector


class PostgresConnectionPool(IDBConnector):
    __slots__ = ("_logger", "_pool", "dsn", "echo", "max_overflow", "pool_size")

    def __init__(
            self,
            *,
            host: str,
            port: int,
            database: str,
            user: str,
            password: str,
            echo: bool = False,
            pool_size: int = 5,
            max_overflow: int = 10,
            app_logger: AppLogger,
    ):
        self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._logger = app_logger
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Создает пул соединений с БД"""

        async def init_connection(connection):
            await connection.set_type_codec(
                'uuid',
                encoder=str,
                decoder=str,
                schema='pg_catalog'
            )

        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.pool_size // 2,
            max_size=self.pool_size + self.max_overflow,
            command_timeout=10,
            statement_cache_size=1024,
            init=init_connection,
            server_settings = {"timezone": "Europe/Moscow"}
        )
        if self.echo:
            self._logger.info(
                f"Database pool created with {self.pool_size} connections",
            )

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self._pool:
            await self.connect()

        async with self._pool.acquire() as connection:
            yield connection

    async def close(self) -> None:
        """Закрытие пула соединений"""
        if self._pool:
            await self._pool.close()
            self._pool = None
