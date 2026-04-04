from domain.entities.server import Server
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.server_repository import IServerRepository


class PostgresServerRepository(IServerRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def list_visible(self) -> list[Server]:
        q = """
            SELECT
                server_ip,
                name,
                "limit",
                hidden,
                created_at,
                panel_port,
                url_secret,
                sub_port,
                available_ports
            FROM servers
            WHERE COALESCE(hidden, 0) = 0
            ORDER BY server_ip
        """
        rows = await self._qe.fetch(q)
        return [self._row_to_server(r) for r in rows]

    @staticmethod
    def _row_to_server(row: dict) -> Server:
        return Server(
            server_ip=row["server_ip"],
            name=row["name"],
            limit=row.get("limit"),
            hidden=row.get("hidden"),
            created_at=row.get("created_at"),
            panel_port=row.get("panel_port"),
            url_secret=row.get("url_secret"),
            sub_port=row.get("sub_port"),
            available_ports=row.get("available_ports"),
        )
