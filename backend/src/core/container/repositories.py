"""Репозитории поверх Postgres (IQueryExecutor)."""

from core.container.infrastructure import InfrastructureContainer
from infrastructure.postgres.repository.payment_repository import PostgresPaymentRepository
from infrastructure.postgres.repository.server_repository import PostgresServerRepository
from infrastructure.postgres.repository.service_tariff_repository import PostgresServiceTariffRepository
from infrastructure.postgres.repository.subscription_repository import PostgresSubscriptionRepository
from interfaces.repositories.payment_repository import IPaymentRepository
from interfaces.repositories.server_repository import IServerRepository
from interfaces.repositories.service_tariff_repository import IServiceTariffRepository
from interfaces.repositories.subscription_repository import ISubscriptionRepository


class RepositoryContainer:
    __slots__ = (
        "_infra",
        "_subscription_repo",
        "_server_repo",
        "_tariff_repo",
        "_payment_repo",
    )

    def __init__(self, infra: InfrastructureContainer) -> None:
        self._infra = infra
        self._subscription_repo: PostgresSubscriptionRepository | None = None
        self._server_repo: PostgresServerRepository | None = None
        self._tariff_repo: PostgresServiceTariffRepository | None = None
        self._payment_repo: PostgresPaymentRepository | None = None

    @property
    def subscription_repository(self) -> ISubscriptionRepository:
        if not self._subscription_repo:
            self._subscription_repo = PostgresSubscriptionRepository(self._infra.query_executor)
        return self._subscription_repo

    @property
    def server_repository(self) -> IServerRepository:
        if not self._server_repo:
            self._server_repo = PostgresServerRepository(self._infra.query_executor)
        return self._server_repo

    @property
    def service_tariff_repository(self) -> IServiceTariffRepository:
        if not self._tariff_repo:
            self._tariff_repo = PostgresServiceTariffRepository(self._infra.query_executor)
        return self._tariff_repo

    @property
    def payment_repository(self) -> IPaymentRepository:
        if not self._payment_repo:
            self._payment_repo = PostgresPaymentRepository(self._infra.query_executor)
        return self._payment_repo
