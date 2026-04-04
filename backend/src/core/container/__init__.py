"""Корневой DI-контейнер: инфраструктура → репозитории → сервисы."""

from core.config import Config
from core.container.infrastructure import InfrastructureContainer
from core.container.repositories import RepositoryContainer
from core.container.services import ServiceContainer
from core.logger import AppLogger


class Container:
    __slots__ = ("config", "infra", "logger", "repos", "services")

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = AppLogger(level=config.logging.LEVEL)
        self.infra = InfrastructureContainer(config, self.logger)
        self.repos = RepositoryContainer(self.infra)
        self.services = ServiceContainer(config, self.infra, self.repos)

    async def closer(self) -> None:
        await self.infra.close()
        self.logger.info("All connections closed")


__all__ = [
    "Container",
    "InfrastructureContainer",
    "RepositoryContainer",
    "ServiceContainer",
]
