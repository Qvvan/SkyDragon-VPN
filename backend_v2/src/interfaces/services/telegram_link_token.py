from abc import ABC, abstractmethod


class ITelegramLinkTokenService(ABC):
    @abstractmethod
    def generate(self, account_id: int) -> str:
        """Encrypt account_id into a URL-safe token for Telegram ?start= parameter."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, token: str) -> int:
        """Decrypt token and return account_id. Raises ValidationError if invalid or expired."""
        raise NotImplementedError
