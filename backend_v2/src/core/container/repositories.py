from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.infrastructure.postgres.repository import (
    PostgresPaymentRepository,
    PostgresServerRepository,
    PostgresServicePlanRepository,
    PostgresSubscriptionRepository,
)
from src.interfaces.repositories import (
    IPaymentRepository,
    IServerRepository,
    IServicePlanRepository,
    ISubscriptionRepository,
)


class RepositoryContainer:
    """Ленивая инициализация всех репозиториев."""

    __slots__ = (
        "_config",
        "_infra",
        "_subscription_repository",
        "_server_repository",
        "_service_plan_repository",
        "_payment_repository",
    )

    def __init__(self, config: Config, infra: InfrastructureContainer) -> None:
        self._config = config
        self._infra = infra
        self._subscription_repository: ISubscriptionRepository | None = None
        self._server_repository: IServerRepository | None = None
        self._service_plan_repository: IServicePlanRepository | None = None
        self._payment_repository: IPaymentRepository | None = None

    @property
    def subscription_repository(self) -> ISubscriptionRepository:
        if not self._subscription_repository:
            self._subscription_repository = PostgresSubscriptionRepository(self._infra.query_executor)
        return self._subscription_repository

    @property
    def server_repository(self) -> IServerRepository:
        if not self._server_repository:
            self._server_repository = PostgresServerRepository(self._infra.query_executor)
        return self._server_repository

    @property
    def service_plan_repository(self) -> IServicePlanRepository:
        if not self._service_plan_repository:
            self._service_plan_repository = PostgresServicePlanRepository(self._infra.query_executor)
        return self._service_plan_repository

    @property
    def payment_repository(self) -> IPaymentRepository:
        if not self._payment_repository:
            self._payment_repository = PostgresPaymentRepository(self._infra.query_executor)
        return self._payment_repository
