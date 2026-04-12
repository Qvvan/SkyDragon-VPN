import asyncpg

from src.domain.entities.service_plan import ServicePlan
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.service_plan import IServicePlanRepository

_SELECT = """
    SELECT service_id, name, description, duration_days,
           price, original_price, is_trial, is_active, is_featured,
           sort_order, badge, created_at, updated_at
    FROM services
"""


class PostgresServicePlanRepository(IServicePlanRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def list_active(self) -> list[ServicePlan]:
        query = f"{_SELECT} WHERE is_active = TRUE AND is_trial = FALSE ORDER BY sort_order ASC"
        rows = await self._query_executor.fetch(query)
        return [self._row_to_entity(row) for row in rows]

    async def get_by_id(self, service_id: int) -> ServicePlan | None:
        query = f"{_SELECT} WHERE service_id = $1 LIMIT 1"
        row = await self._query_executor.fetch_row(query, service_id)
        return self._row_to_entity(row) if row else None

    async def get_trial(self) -> ServicePlan | None:
        query = f"{_SELECT} WHERE is_trial = TRUE AND is_active = TRUE LIMIT 1"
        row = await self._query_executor.fetch_row(query)
        return self._row_to_entity(row) if row else None

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> ServicePlan:
        return ServicePlan(
            service_id=row["service_id"],
            name=row["name"],
            description=row["description"],
            duration_days=row["duration_days"],
            price=int(row["price"]),
            original_price=int(row["original_price"]) if row["original_price"] is not None else None,
            is_trial=row["is_trial"],
            is_active=row["is_active"],
            is_featured=row["is_featured"],
            sort_order=row["sort_order"],
            badge=row["badge"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
