from abc import ABC, abstractmethod

from domain.entities.server import Server


class IVpnSubscriptionTransport(ABC):
    @abstractmethod
    async def fetch_panel_subscription(
        self,
        server: Server,
        encoded_sub_id: str,
        default_sub_port: int,
    ) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def fetch_external_subscription_keys(self, url: str) -> list[str]:
        raise NotImplementedError
