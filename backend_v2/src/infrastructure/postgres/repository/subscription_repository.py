import asyncpg

from src.domain.entities.subscription import Subscription
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.subscription import ISubscriptionRepository


class PostgresSubscriptionRepository(ISubscriptionRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def get_by_user_and_subscription_id(self, user_id: int, subscription_id: int) -> Subscription | None:
        query = """
            SELECT
                s.subscription_id,
                s.user_id,
                s.service_id,
                s.start_date,
                s.end_date,
                s.status,
                s.reminder_sent,
                s.auto_renewal,
                s.card_details_id,
                s.created_at,
                s.updated_at,
                sv.name AS service_name,
                sv.duration_days AS service_duration_days,
                sv.price AS service_price
            FROM subscriptions s
            LEFT JOIN services sv ON sv.service_id = s.service_id
            WHERE s.user_id = $1 AND s.subscription_id = $2
            LIMIT 1
        """
        row = await self._query_executor.fetch_row(query, user_id, subscription_id)
        return self._row_to_entity(row) if row else None

    async def set_auto_renewal(self, user_id: int, subscription_id: int, enabled: bool) -> bool:
        query = """
            UPDATE subscriptions
            SET auto_renewal = $1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND subscription_id = $3
        """
        status = await self._query_executor.execute(query, enabled, user_id, subscription_id)
        return status != "UPDATE 0"

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Subscription:
        return Subscription(
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            service_id=row["service_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
            reminder_sent=row["reminder_sent"] or 0,
            auto_renewal=bool(row["auto_renewal"]),
            card_details_id=row["card_details_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            service_name=row["service_name"],
            service_duration_days=row["service_duration_days"],
            service_price=row["service_price"],
        )
