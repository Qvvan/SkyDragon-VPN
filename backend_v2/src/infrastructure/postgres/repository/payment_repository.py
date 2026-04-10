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
