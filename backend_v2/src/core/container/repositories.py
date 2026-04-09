from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer


class RepositoryContainer:
    """Ленивая инициализация всех репозиториев."""

    __slots__ = (
        "_config",
        "_infra",
    )

    def __init__(self, config: Config, infra: InfrastructureContainer) -> None:
        self._config = config
        self._infra = infra
