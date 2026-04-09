"""Корневой DI-контейнер: инфраструктура → репозитории → сервисы."""

from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.core.container.repositories import RepositoryContainer
from src.core.container.services import ServiceContainer
from src.core.logger import AppLogger


class Container:
    """
    Собирает подконтейнеры и предоставляет общий логгер и shutdown.

    - infra: Postgres, Redis, S3, SSMS, query executor
    - repos: репозитории
    - services: прикладные сервисы
    """

    __slots__ = ("config", "infra", "logger", "repos", "services")

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = AppLogger()
        self.infra = InfrastructureContainer(config, self.logger)
        self.repos = RepositoryContainer(config, self.infra)
        self.services = ServiceContainer(config, self.logger, self.infra, self.repos)

    async def closer(self) -> None:
        await self.infra.close()
        self.logger.info("All connections closed")


__all__ = [
    "Container",
    "InfrastructureContainer",
    "RepositoryContainer",
    "ServiceContainer",
]
