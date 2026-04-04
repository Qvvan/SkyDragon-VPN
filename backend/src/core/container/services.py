"""Прикладные сервисы."""

from core.config import Config
from core.container.infrastructure import InfrastructureContainer
from core.container.repositories import RepositoryContainer
from services.public_subscription_service import PublicSubscriptionService


class ServiceContainer:
    __slots__ = ("_config", "_infra", "_repos", "_public_subscription")

    def __init__(
        self,
        config: Config,
        infra: InfrastructureContainer,
        repos: RepositoryContainer,
    ) -> None:
        self._config = config
        self._infra = infra
        self._repos = repos
        self._public_subscription: PublicSubscriptionService | None = None

    @property
    def public_subscription_service(self) -> PublicSubscriptionService:
        if not self._public_subscription:
            self._public_subscription = PublicSubscriptionService(
                self._config,
                self._repos.subscription_repository,
                self._repos.server_repository,
                self._repos.service_tariff_repository,
                self._repos.payment_repository,
                self._infra.vpn_subscription_transport,
                self._infra.yookassa_gateway,
            )
        return self._public_subscription
