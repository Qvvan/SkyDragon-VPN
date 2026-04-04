from domain.entities.subscription import Subscription
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.subscription_repository import ISubscriptionRepository


_SUB_SELECT = """
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
LEFT JOIN services sv ON s.service_id = sv.service_id
"""


class PostgresSubscriptionRepository(ISubscriptionRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def get_by_user_and_subscription_id(
        self,
        user_id: int,
        subscription_id: int,
    ) -> Subscription | None:
        q = f"{_SUB_SELECT} WHERE s.user_id = $1 AND s.subscription_id = $2"
        row = await self._qe.fetch_row(q, user_id, subscription_id)
        return self._row_to_subscription(row) if row else None

    async def set_auto_renewal(
        self,
        user_id: int,
        subscription_id: int,
        *,
        enabled: bool,
    ) -> None:
        q = """
            UPDATE subscriptions
            SET auto_renewal = $3
            WHERE user_id = $1 AND subscription_id = $2
        """
        await self._qe.execute(q, user_id, subscription_id, enabled)

    @staticmethod
    def _row_to_subscription(row: dict) -> Subscription:
        return Subscription(
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            service_id=row["service_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
            reminder_sent=row["reminder_sent"],
            auto_renewal=row["auto_renewal"],
            card_details_id=row["card_details_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            service_name=row.get("service_name"),
            service_duration_days=row.get("service_duration_days"),
            service_price=row.get("service_price"),
        )
