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

# $1 must be a UUID account_id.
# Matches subscriptions that belong to the account directly or via linked telegram user.
_PRINCIPAL_MATCH = """
    (
        s.account_id = $1
        OR EXISTS (
            SELECT 1 FROM account_telegram_links tl
            WHERE tl.account_id = $1 AND tl.telegram_user_id = s.user_id
        )
    )
"""


class PostgresSubscriptionRepository(ISubscriptionRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def get_by_principal_and_subscription_id(self, principal_id: str, subscription_id: str) -> Subscription | None:
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

    async def set_auto_renewal(self, principal_id: str, subscription_id: str, enabled: bool) -> bool:
        query = """
            UPDATE subscriptions
            SET auto_renewal = $1, updated_at = CURRENT_TIMESTAMP
            WHERE subscription_id = $2
              AND (
                account_id = $3
                OR EXISTS (
                    SELECT 1 FROM account_telegram_links tl
                    WHERE tl.account_id = $3 AND tl.telegram_user_id = subscriptions.user_id
                )
              )
        """
        status = await self._query_executor.execute(query, enabled, subscription_id, principal_id)
        return status != "UPDATE 0"

    async def list_for_account_owner(self, account_id: str) -> list[Subscription]:
        query = f"""
            {_SUBSCRIPTION_SELECT.strip()}
            FROM subscriptions s
            LEFT JOIN services sv ON sv.service_id = s.service_id
            WHERE s.account_id = $1
               OR s.user_id IN (
                   SELECT telegram_user_id FROM account_telegram_links WHERE account_id = $1
               )
            ORDER BY s.created_at DESC
        """
        rows = await self._query_executor.fetch(query, account_id)
        return [self._row_to_entity(row) for row in rows]

    async def has_used_trial(self, account_id: str) -> bool:
        query = """
            SELECT 1
            FROM subscriptions s
            JOIN services sv ON sv.service_id = s.service_id
            WHERE sv.is_trial = TRUE
              AND (
                  s.account_id = $1
                  OR s.user_id IN (
                      SELECT telegram_user_id FROM account_telegram_links WHERE account_id = $1
                  )
              )
            LIMIT 1
        """
        row = await self._query_executor.fetch_row(query, account_id)
        return row is not None

    async def create_for_account(
        self,
        *,
        account_id: str,
        telegram_user_id: int,
        service_id: int,
        duration_days: int,
    ) -> Subscription:
        query = """
            INSERT INTO subscriptions
                (user_id, account_id, service_id, start_date, end_date, status, auto_renewal)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + ($4 || ' days')::INTERVAL, 'активная', FALSE)
            RETURNING subscription_id, user_id, account_id, service_id,
                      start_date, end_date, status, reminder_sent,
                      auto_renewal, card_details_id, created_at, updated_at
        """
        row = await self._query_executor.fetch_row(
            query, telegram_user_id, account_id, service_id, str(duration_days)
        )
        if not row:
            msg = "Failed to create subscription"
            raise RuntimeError(msg)
        return self._row_to_entity_no_service(row)

    @staticmethod
    def _row_to_entity_no_service(row: asyncpg.Record) -> Subscription:
        return Subscription(
            subscription_id=str(row["subscription_id"]),
            user_id=row["user_id"],
            account_id=str(row["account_id"]) if row["account_id"] is not None else None,
            service_id=row["service_id"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
            reminder_sent=row["reminder_sent"] or 0,
            auto_renewal=bool(row["auto_renewal"]),
            card_details_id=row["card_details_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Subscription:
        return Subscription(
            subscription_id=str(row["subscription_id"]),
            user_id=row["user_id"],
            account_id=str(row["account_id"]) if row["account_id"] is not None else None,
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
