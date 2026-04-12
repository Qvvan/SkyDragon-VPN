from loguru import logger

from src.domain.entities.server import ServerNode
from src.interfaces.clients.server_panel.client import IServerPanelClient


class StubServerPanelClient(IServerPanelClient):
    """
    Заглушка панельного клиента.
    Логирует вызовы — фактическое управление ключами выполняется в telegram_bot
    через PanelGateway (3x-ui API). Замените реальной реализацией при необходимости.
    """

    async def provision(
        self,
        server: ServerNode,
        user_id: int,
        subscription_id: str,
        action: str,
        days: int | None = None,
    ) -> None:
        logger.info(
            "panel.provision (stub) | server={} action={} user_id={} sub_id={} days={}",
            server.server_ip,
            action,
            user_id,
            subscription_id,
            days,
        )
        # Реальные вызовы к панели выполняет воркер в telegram_bot/workers/key_operations_worker.py
