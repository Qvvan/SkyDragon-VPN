from abc import ABC, abstractmethod

from domain.entities.types import WaitCallResult, SmsSendResult


class ISmsVerificationClient(ABC):
    """Клиент верификации номера (звонок / SMS)."""

    @abstractmethod
    async def wait_call(self, phone: str, hook_url: str) -> WaitCallResult:
        raise NotImplementedError

    @abstractmethod
    async def push_msg(
        self,
        phone: str,
        text: str,
        sender_name: str,
        priority: int | None = None,
        external_id: str | None = None,
    ) -> SmsSendResult:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Закрыть HTTP-клиент и связанные ресурсы."""
        raise NotImplementedError
