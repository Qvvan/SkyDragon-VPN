from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.interfaces.services.password_hasher import IPasswordHasher


class Argon2PasswordHasher(IPasswordHasher):
    __slots__ = ("_hasher",)

    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash_password(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify(self, password_hash: str, plain: str) -> bool:
        try:
            return self._hasher.verify(password_hash, plain)
        except VerifyMismatchError:
            return False
