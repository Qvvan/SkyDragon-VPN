from abc import ABC, abstractmethod


class IJwtAccessTokenService(ABC):
    @abstractmethod
    def issue(self, account_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_account_id(self, token: str) -> int:
        raise NotImplementedError
