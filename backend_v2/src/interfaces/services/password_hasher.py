from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    @abstractmethod
    def hash_password(self, plain: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, password_hash: str, plain: str) -> bool:
        raise NotImplementedError
