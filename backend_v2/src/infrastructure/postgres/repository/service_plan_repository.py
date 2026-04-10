import asyncpg

from src.domain.entities.service_plan import ServicePlan
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.service_plan import IServicePlanRepository


class PostgresServicePlanRepository(IServicePlanRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def list_for_renewal(self) -> list[ServicePlan]:
        query = """
            SELECT service_id, name, duration_days, price
            FROM services
            WHERE service_id > 0
            ORDER BY duration_days ASC
        """
        rows = await self._query_executor.fetch(query)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_id(self, service_id: int) -> ServicePlan | None:
        query = """
            SELECT service_id, name, duration_days, price
            FROM services
            WHERE service_id = $1
            LIMIT 1
        """
        row = await self._query_executor.fetch_row(query, service_id)
        return self._row_to_entity(row) if row else None

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> ServicePlan:
        return ServicePlan(
            service_id=row["service_id"],
            name=row["name"],
            duration_days=row["duration_days"],
            price=row["price"],
        )
