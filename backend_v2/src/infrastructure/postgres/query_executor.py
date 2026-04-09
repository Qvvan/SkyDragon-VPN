from typing import Any

import asyncpg

from src.infrastructure.postgres.connection import PostgresConnectionPool
from src.interfaces.clients.db.query_executor import IQueryExecutor


class PostgresQueryExecutor(IQueryExecutor):
    __slots__ = ("_connection_pool",)

    def __init__(self, connection_pool: PostgresConnectionPool):
        self._connection_pool = connection_pool

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        async with self._connection_pool.get_connection() as connection:
            return await connection.fetch(query, *args)

    async def fetch_row(self, query: str, *args: Any) -> asyncpg.Record | None:
        async with self._connection_pool.get_connection() as connection:
            return await connection.fetchrow(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        async with self._connection_pool.get_connection() as connection:
            return await connection.execute(query, *args)
