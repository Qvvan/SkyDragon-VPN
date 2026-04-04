from datetime import datetime

from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.subscription_history_repository import ISubscriptionHistoryRepository


class PostgresSubscriptionHistoryRepository(ISubscriptionHistoryRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def insert(
        self,
        *,
        user_id: int,
        service_id: int,
        start_date: datetime,
        end_date: datetime,
        status: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> int:
        q = """
            INSERT INTO subscriptions_history
                (user_id, service_id, start_date, end_date, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING subscription_id
        """
        row = await self._qe.fetch_row(
            q, user_id, service_id, start_date, end_date, status, created_at, updated_at,
        )
        assert row is not None
        return int(row["subscription_id"])
