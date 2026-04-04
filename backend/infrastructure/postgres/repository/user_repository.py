from typing import Any

from domain.entities.user import User
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.user_repository import IUserRepository

_USER_ALLOW = frozenset({"username", "ban", "trial_used", "reminder_trial_sub", "last_visit"})


class PostgresUserRepository(IUserRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def get_by_id(self, user_id: int) -> User | None:
        q = """
            SELECT user_id, username, ban, trial_used, reminder_trial_sub, last_visit, created_at
            FROM users WHERE user_id = $1
        """
        row = await self._qe.fetch_row(q, user_id)
        return self._row_to_user(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        q = """
            SELECT user_id, username, ban, trial_used, reminder_trial_sub, last_visit, created_at
            FROM users WHERE username = $1
        """
        row = await self._qe.fetch_row(q, username)
        return self._row_to_user(row) if row else None

    async def exists(self, user_id: int) -> bool:
        q = "SELECT 1 AS x FROM users WHERE user_id = $1"
        row = await self._qe.fetch_row(q, user_id)
        return row is not None

    async def insert(self, user: User) -> None:
        q = """
            INSERT INTO users (user_id, username, ban, trial_used, reminder_trial_sub, last_visit, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, COALESCE($7, NOW()))
            ON CONFLICT (user_id) DO NOTHING
        """
        await self._qe.execute(
            q,
            user.user_id,
            user.username,
            user.ban,
            user.trial_used,
            user.reminder_trial_sub,
            user.last_visit,
            user.created_at,
        )

    async def update_fields(self, user_id: int, **fields: Any) -> None:
        parts: list[str] = []
        args: list[Any] = []
        i = 1
        for key, value in fields.items():
            if key not in _USER_ALLOW or value is None:
                continue
            parts.append(f"{key} = ${i}")
            args.append(value)
            i += 1
        if not parts:
            return
        args.append(user_id)
        q = f"UPDATE users SET {', '.join(parts)} WHERE user_id = ${i}"
        await self._qe.execute(q, *args)

    async def list_all(self, *, limit: int = 5000, offset: int = 0) -> list[User]:
        q = """
            SELECT user_id, username, ban, trial_used, reminder_trial_sub, last_visit, created_at
            FROM users
            ORDER BY user_id
            LIMIT $1 OFFSET $2
        """
        rows = await self._qe.fetch(q, limit, offset)
        return [self._row_to_user(r) for r in rows]

    @staticmethod
    def _row_to_user(row: dict) -> User:
        return User(
            user_id=row["user_id"],
            username=row.get("username"),
            ban=row.get("ban"),
            trial_used=row.get("trial_used"),
            reminder_trial_sub=row.get("reminder_trial_sub"),
            last_visit=row.get("last_visit"),
            created_at=row.get("created_at"),
        )
