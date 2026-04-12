from cryptography.fernet import Fernet, InvalidToken

from src.core.exceptions import ValidationError
from src.interfaces.services.telegram_link_token import ITelegramLinkTokenService


class FernetTelegramLinkTokenService(ITelegramLinkTokenService):
    __slots__ = ("_cipher", "_ttl")

    def __init__(self, key: str, ttl_seconds: int = 900) -> None:
        self._cipher = Fernet(key.encode("utf-8"))
        self._ttl = ttl_seconds

    def generate(self, account_id: int) -> str:
        return self._cipher.encrypt(str(account_id).encode()).decode()

    def parse(self, token: str) -> int:
        try:
            data = self._cipher.decrypt(token.encode(), ttl=self._ttl)
            return int(data.decode())
        except (InvalidToken, ValueError, Exception):
            raise ValidationError("Недействительный или устаревший токен привязки")
