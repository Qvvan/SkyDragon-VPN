from typing import Any

import asyncpg

from infrastructure.postgres.connection import PostgresConnectionPool
from interfaces.clients.db.query_executor import IQueryExecutor


def _row_to_dict(row: asyncpg.Record) -> dict[str, Any]:
    return dict(row)


class PostgresQueryExecutor(IQueryExecutor):
    __slots__ = ("_connection_pool",)

    def __init__(self, connection_pool: PostgresConnectionPool) -> None:
        self._connection_pool = connection_pool

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        async with self._connection_pool.get_connection() as connection:
            rows = await connection.fetch(query, *args)
            return [_row_to_dict(r) for r in rows]

    async def fetch_row(self, query: str, *args: Any) -> dict[str, Any] | None:
        async with self._connection_pool.get_connection() as connection:
            row = await connection.fetchrow(query, *args)
            return _row_to_dict(row) if row else None

    async def execute(self, query: str, *args: Any) -> str:
        async with self._connection_pool.get_connection() as connection:
            return await connection.execute(query, *args)
