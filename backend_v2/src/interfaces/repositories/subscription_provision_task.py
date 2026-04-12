from abc import ABC, abstractmethod

from src.domain.entities.subscription_provision_task import KeyOperation


class IKeyOperationRepository(ABC):
    @abstractmethod
    async def bulk_insert(self, operations: list[KeyOperation]) -> None:
        """Вставляет несколько операций за один раз."""
        raise NotImplementedError

    @abstractmethod
    async def claim_pending(self, limit: int = 50) -> list[KeyOperation]:
        """
        Атомарно берёт до `limit` pending-операций, переводит в processing,
        инкрементирует retry_count. Использует FOR UPDATE SKIP LOCKED.
        Возвращает операции с денормализованными полями сервера.
        """
        raise NotImplementedError

    @abstractmethod
    async def mark_completed(self, operation_id: int) -> None:
        """Переводит операцию в статус completed, проставляет completed_at."""
        raise NotImplementedError

    @abstractmethod
    async def mark_failed(self, operation_id: int, error: str, retry_after_seconds: int) -> None:
        """
        Если retry_count < max_retries — возвращает в pending с задержкой.
        Иначе — окончательно failed.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_stale_processing(self, older_than_seconds: int = 300) -> int:
        """
        Возвращает зависшие processing-операции (воркер упал) обратно в pending.
        Возвращает количество сброшенных операций.
        """
        raise NotImplementedError


# Backwards-compat alias
ISubscriptionProvisionTaskRepository = IKeyOperationRepository
