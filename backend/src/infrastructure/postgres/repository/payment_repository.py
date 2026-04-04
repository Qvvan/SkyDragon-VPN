from backend.src.interfaces.repositories.payment_repository import IPaymentRepository


class PostgresPaymentRepository(IPaymentRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def create_pending(
        self,
        *,
        payment_id: str,
        user_id: int,
        service_id: int,
    ) -> None:
        q = """
            INSERT INTO payments (payment_id, user_id, service_id, status)
            VALUES ($1, $2, $3, 'pending')
        """
        await self._qe.execute(q, payment_id, user_id, service_id)
