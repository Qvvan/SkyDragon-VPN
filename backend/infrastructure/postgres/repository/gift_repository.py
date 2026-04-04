from datetime import datetime
from typing import Any

from domain.entities.gift import Gift
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.gift_repository import IGiftRepository

_GIFT_ALLOW = frozenset({"status", "activated_at", "service_id"})


class PostgresGiftRepository(IGiftRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def list_ordered(
        self,
        *,
        recipient_user_id: int | None = None,
        limit: int = 500,
    ) -> list[Gift]:
        if recipient_user_id is not None:
            q = """
                SELECT gift_id, giver_id, recipient_user_id, service_id, status, activated_at, created_at
                FROM gifts
                WHERE recipient_user_id = $1
                ORDER BY gift_id DESC
                LIMIT $2
            """
            rows = await self._qe.fetch(q, recipient_user_id, limit)
        else:
            q = """
                SELECT gift_id, giver_id, recipient_user_id, service_id, status, activated_at, created_at
                FROM gifts
                ORDER BY gift_id DESC
                LIMIT $1
            """
            rows = await self._qe.fetch(q, limit)
        return [self._row_to_gift(r) for r in rows]

    async def list_pending(self) -> list[Gift]:
        q = """
            SELECT gift_id, giver_id, recipient_user_id, service_id, status, activated_at, created_at
            FROM gifts WHERE status = 'pending'
            ORDER BY gift_id DESC
        """
        rows = await self._qe.fetch(q)
        return [self._row_to_gift(r) for r in rows]

    async def get_by_id(self, gift_id: int) -> Gift | None:
        q = """
            SELECT gift_id, giver_id, recipient_user_id, service_id, status, activated_at, created_at
            FROM gifts WHERE gift_id = $1
        """
        row = await self._qe.fetch_row(q, gift_id)
        return self._row_to_gift(row) if row else None

    async def insert(
        self,
        *,
        giver_id: int,
        recipient_user_id: int,
        service_id: int | None,
        status: str = "pending",
    ) -> int:
        q = """
            INSERT INTO gifts (giver_id, recipient_user_id, service_id, status, created_at)
            VALUES ($1, $2, $3, $4, NOW())
            RETURNING gift_id
        """
        row = await self._qe.fetch_row(q, giver_id, recipient_user_id, service_id, status)
        assert row is not None
        return int(row["gift_id"])

    async def update_fields(self, gift_id: int, **fields: Any) -> None:
        parts: list[str] = []
        args: list[Any] = []
        i = 1
        for key, value in fields.items():
            if key not in _GIFT_ALLOW:
                continue
            parts.append(f"{key} = ${i}")
            args.append(value)
            i += 1
        if not parts:
            return
        args.append(gift_id)
        q = f"UPDATE gifts SET {', '.join(parts)} WHERE gift_id = ${i}"
        await self._qe.execute(q, *args)

    @staticmethod
    def _row_to_gift(row: dict) -> Gift:
        return Gift(
            gift_id=row["gift_id"],
            giver_id=row["giver_id"],
            recipient_user_id=row["recipient_user_id"],
            service_id=row.get("service_id"),
            status=row["status"],
            activated_at=row.get("activated_at"),
            created_at=row.get("created_at"),
        )
