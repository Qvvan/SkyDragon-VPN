from datetime import datetime

from loguru import logger

from src.domain.entities.server import ServerNode
from src.interfaces.clients.server_panel.client import IServerPanelClient


class StubServerPanelClient(IServerPanelClient):
    """
    Заглушка панельного клиента.
    Логирует вызовы — замените реальной реализацией 3x-ui / другой панели.
    """

    async def provision(
        self,
        server: ServerNode,
        user_id: int,
        subscription_id: int,
        action: str,
        expire_at: datetime | None,
    ) -> None:
        logger.info(
            "panel.provision | server={} action={} user_id={} sub_id={} expire_at={}",
            server.server_ip,
            action,
            user_id,
            subscription_id,
            expire_at,
        )
        # TODO: реализовать вызов 3x-ui API
        # POST https://{server.server_ip}:{server.panel_port}/panel/api/inbounds/addClient
