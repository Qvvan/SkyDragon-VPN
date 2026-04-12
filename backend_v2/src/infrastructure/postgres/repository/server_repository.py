import asyncpg

from src.domain.entities.server import ServerNode
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.server import IServerRepository


class PostgresServerRepository(IServerRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def list_visible(self) -> list[ServerNode]:
        query = """
            SELECT
                server_id,
                server_ip,
                name,
                "limit",
                hidden,
                available_ports,
                panel_port,
                url_secret,
                sub_port,
                created_at
            FROM servers
            WHERE hidden = 0
            ORDER BY name ASC
        """
        rows = await self._query_executor.fetch(query)
        return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> ServerNode:
        return ServerNode(
            server_id=row["server_id"],
            server_ip=row["server_ip"],
            name=row["name"],
            limit=row["limit"],
            hidden=row["hidden"] or 0,
            available_ports=row["available_ports"],
            panel_port=row["panel_port"],
            url_secret=row["url_secret"],
            sub_port=row["sub_port"],
            created_at=row["created_at"],
        )
