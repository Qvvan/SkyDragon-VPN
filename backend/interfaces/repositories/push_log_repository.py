from abc import ABC, abstractmethod

from domain.entities.push_log import PushLog


class IPushLogRepository(ABC):
    @abstractmethod
    async def insert(self, *, message: str, user_ids: list[int]) -> PushLog:
        raise NotImplementedError
