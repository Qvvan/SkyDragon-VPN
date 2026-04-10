from urllib.parse import unquote

from cryptography.fernet import Fernet

from src.interfaces.services.token_codec import ITokenCodec


class FernetTokenCodec(ITokenCodec):
    __slots__ = ("_cipher",)

    def __init__(self, secret_key: str) -> None:
        self._cipher = Fernet(secret_key.encode("utf-8"))

    def encrypt(self, user_id: int, subscription_id: int) -> str:
        payload = f"{user_id}|{subscription_id}"
        return self._cipher.encrypt(payload.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_part: str) -> tuple[int, int]:
        normalized = unquote((encrypted_part or "").strip()).replace(" ", "+")
        raw = self._cipher.decrypt(normalized.encode("utf-8")).decode("utf-8")
        user_id_str, subscription_id_str = raw.split("|", maxsplit=1)
        return int(user_id_str), int(subscription_id_str)
