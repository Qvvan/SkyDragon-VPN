from abc import ABC, abstractmethod


class ITokenCodec(ABC):
    @abstractmethod
    def encrypt(self, user_id: int, subscription_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, encrypted_part: str) -> tuple[int, str]:
        raise NotImplementedError
