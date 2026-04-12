from abc import ABC, abstractmethod

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
        subscription_id: str,
        action: str,
        days: int | None = None,
    ) -> None:
        """
        Выполняет действие над пользователем на панели сервера.

        action:
          'create'  — создать ключ
          'update'  — обновить ключ (продление)
          'delete'  — удалить ключ
          'enable'  — включить ключ
          'disable' — выключить ключ

        days — количество дней подписки для create/update (None = без ограничений).
        Кидает Exception при ошибке (воркер поймает и уйдёт в retry).
        """
        raise NotImplementedError
