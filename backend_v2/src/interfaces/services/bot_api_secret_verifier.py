from abc import ABC, abstractmethod


class IBotApiSecretVerifier(ABC):
    """Проверка секрета входящих вызовов от доверенного клиента (например, Telegram-бота)."""

    @abstractmethod
    def assert_valid(self, presented_secret: str | None) -> None:
        """Бросает ForbiddenError, если секрет неверен или вызовы отключены конфигурацией."""
        raise NotImplementedError
