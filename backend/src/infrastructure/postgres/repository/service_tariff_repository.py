from domain.entities.service_tariff import ServiceTariff
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.service_tariff_repository import IServiceTariffRepository


class PostgresServiceTariffRepository(IServiceTariffRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def list_for_renewal(self) -> list[ServiceTariff]:
        q = """
            SELECT service_id, name, duration_days, price
            FROM services
            WHERE service_id > 0
            ORDER BY duration_days ASC
        """
        rows = await self._qe.fetch(q)
        return [self._row_to_tariff(r) for r in rows]

    async def get_by_id(self, service_id: int) -> ServiceTariff | None:
        q = """
            SELECT service_id, name, duration_days, price
            FROM services
            WHERE service_id = $1
        """
        row = await self._qe.fetch_row(q, service_id)
        return self._row_to_tariff(row) if row else None

    @staticmethod
    def _row_to_tariff(row: dict) -> ServiceTariff:
        return ServiceTariff(
            service_id=row["service_id"],
            name=row["name"],
            duration_days=row["duration_days"],
            price=row["price"],
        )
