from abc import ABC, abstractmethod

from domain.entities.server import Server


class IServerRepository(ABC):
    @abstractmethod
    async def list_visible(self) -> list[Server]:
        raise NotImplementedError
