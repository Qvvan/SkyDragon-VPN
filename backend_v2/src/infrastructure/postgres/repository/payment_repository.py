import asyncpg

from src.domain.entities.payment import Payment
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.payment import IPaymentRepository


class PostgresPaymentRepository(IPaymentRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def create_pending_payment(self, payment_id: str, user_id: int, service_id: int) -> None:
        query = """
            INSERT INTO payments (payment_id, user_id, service_id, status, payment_type, created_at, updated_at)
            VALUES ($1, $2, $3, 'pending', 'myself', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        await self._query_executor.execute(query, payment_id, user_id, service_id)

    async def list_for_account(self, account_id: int) -> list[Payment]:
        query = """
            SELECT p.id, p.payment_id, p.user_id, p.recipient_user_id, p.service_id,
                   p.status, p.payment_type, p.receipt_link, p.created_at, p.updated_at
            FROM payments p
            WHERE p.user_id = $1
               OR p.user_id IN (
                   SELECT telegram_user_id FROM account_telegram_links WHERE account_id = $1
               )
            ORDER BY p.created_at DESC
            LIMIT 50
        """
        rows = await self._query_executor.fetch(query, account_id)
        return [self._row_to_entity(row) for row in rows]

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> Payment:
        return Payment(
            id=row["id"],
            payment_id=row["payment_id"],
            user_id=row["user_id"],
            recipient_user_id=row["recipient_user_id"],
            service_id=row["service_id"],
            status=row["status"],
            payment_type=row["payment_type"],
            receipt_link=row["receipt_link"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
