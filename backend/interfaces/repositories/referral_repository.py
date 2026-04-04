from abc import ABC, abstractmethod

from domain.entities.referral import Referral


class IReferralRepository(ABC):
    @abstractmethod
    async def insert(
        self,
        *,
        referred_id: int,
        referrer_id: int,
        bonus_issued: str,
        invited_username: str | None = None,
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_by_referrer(self, referrer_id: int) -> list[Referral]:
        raise NotImplementedError

    @abstractmethod
    async def mark_subscribed_if_was_invited(self, referred_id: int) -> int | None:
        """Если у referred_id статус «приглашен», ставит «купил»; возвращает referrer_id или None."""
        raise NotImplementedError
