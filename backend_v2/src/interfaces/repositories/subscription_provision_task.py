from abc import ABC, abstractmethod

from src.domain.entities.subscription_provision_task import SubscriptionProvisionTask


class ISubscriptionProvisionTaskRepository(ABC):
    @abstractmethod
    async def bulk_insert(self, tasks: list[SubscriptionProvisionTask]) -> None:
        """Вставляет несколько задач за один раз."""
        raise NotImplementedError

    @abstractmethod
    async def claim_pending(self, limit: int = 50) -> list[SubscriptionProvisionTask]:
        """
        Атомарно берёт до `limit` pending-задач, переводит в processing,
        инкрементирует attempts. Использует FOR UPDATE SKIP LOCKED.
        Возвращает задачи с денормализованными полями сервера.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_done(self, task_id: int) -> None:
        """Переводит задачу в статус done, проставляет done_at."""
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(self, task_id: int, error: str, retry_after_seconds: int) -> None:
        """
        Если attempts < max_attempts — возвращает в pending с задержкой.
        Иначе — окончательно failed.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_stale_processing(self, older_than_seconds: int = 300) -> int:
        """
        Возвращает зависшие processing-задачи (воркер упал) обратно в pending.
        Возвращает количество сброшенных задач.
        """
        raise NotImplementedError
