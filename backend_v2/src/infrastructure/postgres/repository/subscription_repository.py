import asyncpg

from src.domain.entities.subscription import Subscription
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.subscription import ISubscriptionRepository

_SUBSCRIPTION_SELECT = """
            SELECT
                s.subscription_id,
                s.user_id,
                s.account_id,
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
"""

_PRINCIPAL_MATCH = """
    (
        s.user_id = $1
        OR s.account_id = $1
        OR EXISTS (
            SELECT 1 FROM account_telegram_links tl_a
            WHERE tl_a.telegram_user_id = $1 AND tl_a.account_id = s.account_id
        )
        OR EXISTS (
            SELECT 1 FROM account_telegram_links tl_b
            WHERE tl_b.account_id = $1 AND tl_b.telegram_user_id = s.user_id
        )
    )
"""


class PostgresSubscriptionRepository(ISubscriptionRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def get_by_principal_and_subscription_id(self, principal_id: int, subscription_id: int) -> Subscription | None:
        query = f"""
            {_SUBSCRIPTION_SELECT.strip()}
            FROM subscriptions s
            LEFT JOIN services sv ON sv.service_id = s.service_id
            WHERE s.subscription_id = $2
              AND {_PRINCIPAL_MATCH}
            LIMIT 1
        """
        row = await self._query_executor.fetch_row(query, principal_id, subscription_id)
        return self._row_to_entity(row) if row else None

    async def set_auto_renewal(self, principal_id: int, subscription_id: int, enabled: bool) -> bool:
        query = f"""
            UPDATE subscriptions
            SET auto_renewal = $1, updated_at = CURRENT_TIMESTAMP
            WHERE subscription_id = $2
              AND (
                subscriptions.user_id = $3
                OR subscriptions.account_id = $3
                OR EXISTS (
                    SELECT 1 FROM account_telegram_links tl_a
                    WHERE tl_a.telegram_user_id = $3 AND tl_a.account_id = subscriptions.account_id
                )
                OR EXISTS (
                    SELECT 1 FROM account_telegram_links tl_b
                    WHERE tl_b.account_id = $3 AND tl_b.telegram_user_id = subscriptions.user_id
                )
              )
        """
        status = await self._query_executor.execute(query, enabled, subscription_id, principal_id)
        return status != "UPDATE 0"

    async def list_for_account_owner(self, account_id: int) -> list[Subscription]:
        query = f"""
            {_SUBSCRIPTION_SELECT.strip()}
            FROM subscriptions s
            LEFT JOIN services sv ON sv.service_id = s.service_id
            WHERE s.account_id = $1
               OR s.user_id = $1
               OR s.user_id IN (
                   SELECT telegram_user_id FROM account_telegram_links WHERE account_id = $1
               )
            ORDER BY s.subscription_id DESC
        """
        rows = await self._query_executor.fetch(query, account_id)
        return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Subscription:
        return Subscription(
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            account_id=row["account_id"],
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
