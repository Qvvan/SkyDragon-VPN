from domain.entities.referral import Referral
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.referral_repository import IReferralRepository

_INVITED = "приглашен"
_SUBSCRIBED = "купил"


class PostgresReferralRepository(IReferralRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def insert(
        self,
        *,
        referred_id: int,
        referrer_id: int,
        bonus_issued: str,
        invited_username: str | None = None,
    ) -> int:
        q = """
            INSERT INTO referrals (referred_id, referrer_id, bonus_issued, invited_username, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            RETURNING id
        """
        row = await self._qe.fetch_row(q, referred_id, referrer_id, bonus_issued, invited_username)
        assert row is not None
        return int(row["id"])

    async def list_by_referrer(self, referrer_id: int) -> list[Referral]:
        q = """
            SELECT id, referred_id, referrer_id, bonus_issued, invited_username, created_at
            FROM referrals
            WHERE referrer_id = $1
            ORDER BY id
        """
        rows = await self._qe.fetch(q, referrer_id)
        return [self._row_to_referral(r) for r in rows]

    async def mark_subscribed_if_was_invited(self, referred_id: int) -> int | None:
        q = """
            UPDATE referrals
            SET bonus_issued = $2
            WHERE referred_id = $1 AND bonus_issued = $3
            RETURNING referrer_id
        """
        row = await self._qe.fetch_row(q, referred_id, _SUBSCRIBED, _INVITED)
        if not row:
            return None
        return int(row["referrer_id"])

    @staticmethod
    def _row_to_referral(row: dict) -> Referral:
        return Referral(
            id=row["id"],
            referred_id=row["referred_id"],
            referrer_id=row["referrer_id"],
            bonus_issued=row.get("bonus_issued"),
            invited_username=row.get("invited_username"),
            created_at=row.get("created_at"),
        )
