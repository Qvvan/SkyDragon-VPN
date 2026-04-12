from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.infrastructure.postgres.repository import (
    PostgresAccountRepository,
    PostgresAccountTelegramLinkRepository,
    PostgresPaymentRepository,
    PostgresServerRepository,
    PostgresServicePlanRepository,
    PostgresSubscriptionProvisionTaskRepository,
    PostgresSubscriptionRepository,
)
from src.interfaces.repositories import (
    IAccountRepository,
    IAccountTelegramLinkRepository,
    IPaymentRepository,
    IServerRepository,
    IServicePlanRepository,
    ISubscriptionProvisionTaskRepository,
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
        "_account_repository",
        "_account_telegram_link_repository",
        "_subscription_provision_task_repository",
    )

    def __init__(self, config: Config, infra: InfrastructureContainer) -> None:
        self._config = config
        self._infra = infra
        self._subscription_repository: ISubscriptionRepository | None = None
        self._server_repository: IServerRepository | None = None
        self._service_plan_repository: IServicePlanRepository | None = None
        self._payment_repository: IPaymentRepository | None = None
        self._account_repository: IAccountRepository | None = None
        self._account_telegram_link_repository: IAccountTelegramLinkRepository | None = None
        self._subscription_provision_task_repository: ISubscriptionProvisionTaskRepository | None = None

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

    @property
    def account_repository(self) -> IAccountRepository:
        if not self._account_repository:
            self._account_repository = PostgresAccountRepository(self._infra.query_executor)
        return self._account_repository

    @property
    def account_telegram_link_repository(self) -> IAccountTelegramLinkRepository:
        if not self._account_telegram_link_repository:
            self._account_telegram_link_repository = PostgresAccountTelegramLinkRepository(self._infra.query_executor)
        return self._account_telegram_link_repository

    @property
    def subscription_provision_task_repository(self) -> ISubscriptionProvisionTaskRepository:
        if not self._subscription_provision_task_repository:
            self._subscription_provision_task_repository = PostgresSubscriptionProvisionTaskRepository(
                self._infra.query_executor
            )
        return self._subscription_provision_task_repository
