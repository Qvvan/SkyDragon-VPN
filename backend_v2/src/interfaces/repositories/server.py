from abc import ABC, abstractmethod

from src.domain.entities.server import ServerNode


class IServerRepository(ABC):
    @abstractmethod
    async def list_visible(self) -> list[ServerNode]:
        raise NotImplementedError
