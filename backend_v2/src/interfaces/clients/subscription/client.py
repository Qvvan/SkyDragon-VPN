from abc import ABC, abstractmethod

from src.domain.entities.server import ServerNode


class ISubscriptionClient(ABC):
    @abstractmethod
    async def fetch_server_subscription(self, server: ServerNode, encoded_sub_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_external_subscription_keys(self, url: str) -> list[str]:
        raise NotImplementedError
