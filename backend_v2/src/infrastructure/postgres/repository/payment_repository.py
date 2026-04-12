import asyncpg

from src.domain.entities.payment import Payment
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.payment import IPaymentRepository

_SELECT_WITH_SERVICE = (
    "p.id, p.payment_id, p.user_id, p.recipient_user_id, p.service_id,"
    " p.subscription_id, p.payment_type, p.status, p.amount, p.receipt_link,"
    " p.confirmation_url, p.created_at, p.updated_at,"
    " s.name AS service_name"
)

_SELECT_BASE = (
    "p.id, p.payment_id, p.user_id, p.recipient_user_id, p.service_id,"
    " p.subscription_id, p.payment_type, p.status, p.amount, p.receipt_link,"
    " p.confirmation_url, p.created_at, p.updated_at,"
    " NULL::text AS service_name"
)


class PostgresPaymentRepository(IPaymentRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def create_pending_payment(
        self,
        payment_id: str,
        confirmation_url: str,
        payment_type: str,
        amount,
        user_id: int,
        service_id: int,
        account_id: str | None = None,
        subscription_id: str | None = None,
    ) -> None:
        query = """
            INSERT INTO payments (
                payment_id, confirmation_url, payment_type, amount,
                user_id, account_id, service_id, subscription_id,
                status, created_at, updated_at
            )
            VALUES ($1, $2, $3::payment_type, $4, $5, $6, $7, $8, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        await self._query_executor.execute(
            query,
            payment_id, confirmation_url, payment_type, amount,
            user_id, account_id, service_id, subscription_id,
        )

    async def find_active_pending_for_account(
        self,
        account_id: str,
        service_id: int,
        payment_type: str | None = None,
    ) -> Payment | None:
        if payment_type is not None:
            query = (
                "SELECT " + _SELECT_BASE + " FROM payments p"
                " WHERE p.account_id = $1"
                "   AND p.service_id = $2"
                "   AND p.payment_type = $3::payment_type"
                "   AND p.status = 'pending'"
                "   AND p.confirmation_url IS NOT NULL"
                "   AND p.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'"
                " ORDER BY p.created_at DESC LIMIT 1"
            )
            row = await self._query_executor.fetch_row(query, account_id, service_id, payment_type)
        else:
            query = (
                "SELECT " + _SELECT_BASE + " FROM payments p"
                " WHERE p.account_id = $1"
                "   AND p.service_id = $2"
                "   AND p.status = 'pending'"
                "   AND p.confirmation_url IS NOT NULL"
                "   AND p.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'"
                " ORDER BY p.created_at DESC LIMIT 1"
            )
            row = await self._query_executor.fetch_row(query, account_id, service_id)
        return self._row_to_entity(row) if row else None

    async def find_active_pending_for_subscription(
        self,
        subscription_id: str,
        service_id: int,
    ) -> Payment | None:
        query = (
            "SELECT " + _SELECT_BASE + " FROM payments p"
            " WHERE p.subscription_id = $1"
            "   AND p.service_id = $2"
            "   AND p.status = 'pending'"
            "   AND p.confirmation_url IS NOT NULL"
            "   AND p.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'"
            " ORDER BY p.created_at DESC LIMIT 1"
        )
        row = await self._query_executor.fetch_row(query, subscription_id, service_id)
        return self._row_to_entity(row) if row else None

    async def list_for_account(self, account_id: str) -> list[Payment]:
        query = (
            "SELECT " + _SELECT_WITH_SERVICE + " FROM payments p"
            " LEFT JOIN services s ON s.service_id = p.service_id"
            " WHERE p.account_id = $1"
            "    OR p.user_id IN ("
            "        SELECT telegram_user_id FROM account_telegram_links WHERE account_id = $1"
            "    )"
            " ORDER BY p.created_at DESC LIMIT 50"
        )
        rows = await self._query_executor.fetch(query, account_id)
        return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Payment:
        return Payment(
            id=str(row["id"]),
            payment_id=row["payment_id"],
            user_id=row["user_id"],
            recipient_user_id=row["recipient_user_id"],
            service_id=row["service_id"],
            subscription_id=row["subscription_id"],
            payment_type=row["payment_type"],
            status=row["status"],
            amount=row["amount"],
            receipt_link=row["receipt_link"],
            confirmation_url=row["confirmation_url"],
            service_name=row["service_name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
