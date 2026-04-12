from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.server import ServerNode


class IServerPanelClient(ABC):
    """
    Интерфейс управления пользователями на VPN-сервере (3x-ui panel или аналог).
    Каждый метод — идемпотентный: повторный вызов с теми же параметрами безопасен.
    """

    @abstractmethod
    async def provision(
        self,
        server: ServerNode,
        user_id: int,
        subscription_id: int,
        action: str,
        expire_at: datetime | None,
    ) -> None:
        """
        Выполняет действие над пользователем на панели сервера.

        action:
          'create' — создать пользователя / продлить подписку
          'update' — обновить срок действия
          'delete' — удалить пользователя

        Кидает Exception при ошибке (воркер поймает и уйдёт в retry).
        """
        raise NotImplementedError
