"""Прикладные сервисы (зависят от репозиториев и инфраструктуры)."""

from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.core.container.repositories import RepositoryContainer
from src.core.logger import AppLogger


class ServiceContainer:
    """Ленивая инициализация сервисов."""

    __slots__ = (
        "_config",
        "_logger",
        "_infra",
        "_repos"
    )

    def __init__(
            self,
            config: Config,
            logger: AppLogger,
            infra: InfrastructureContainer,
            repos: RepositoryContainer,
    ) -> None:
        self._config = config
        self._logger = logger
        self._infra = infra
        self._repos = repos
