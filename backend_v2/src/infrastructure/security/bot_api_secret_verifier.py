import secrets

from pydantic import SecretStr

from src.core.exceptions import ForbiddenError
from src.interfaces.services.bot_api_secret_verifier import IBotApiSecretVerifier


class BotApiSecretVerifier(IBotApiSecretVerifier):
    __slots__ = ("_expected",)

    def __init__(self, configured_secret: SecretStr) -> None:
        self._expected = configured_secret.get_secret_value().strip()

    def assert_valid(self, presented_secret: str | None) -> None:
        if not self._expected:
            raise ForbiddenError("Приватный API бота отключён")
        got = (presented_secret or "").strip()
        a = got.encode("utf-8")
        b = self._expected.encode("utf-8")
        if len(a) != len(b) or not secrets.compare_digest(a, b):
            raise ForbiddenError("Недостаточно прав")
