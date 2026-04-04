import json
from datetime import datetime
from typing import Any

from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.user_notification_repository import IUserNotificationRepository


def _json_param(data: dict[str, Any] | None) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


class PostgresUserNotificationRepository(IUserNotificationRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def insert(
        self,
        *,
        user_id: int,
        notification_type: str,
        subscription_id: int | None = None,
        message: str | None = None,
        additional_data: dict[str, Any] | None = None,
        status: str = "active",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> int:
        now = datetime.now()
        c_at = created_at or now
        u_at = updated_at or now
        json_s = _json_param(additional_data)
        q = """
            INSERT INTO notifications
                (user_id, subscription_id, notification_type, message, status, additional_data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, CAST($6 AS jsonb), $7, $8)
            RETURNING id
        """
        row = await self._qe.fetch_row(
            q, user_id, subscription_id, notification_type, message, status, json_s, c_at, u_at,
        )
        if not row:
            raise RuntimeError(
                "notifications: INSERT не вернул id. Добавьте DEFAULT nextval(...) или BIGSERIAL на id.",
            )
        return int(row["id"])

    async def get_last_by_subscription_and_type(
        self,
        subscription_id: int,
        notification_type: str,
    ) -> dict[str, Any] | None:
        q = """
            SELECT id, user_id, subscription_id, notification_type, message, status, additional_data,
                   created_at, updated_at
            FROM notifications
            WHERE subscription_id = $1 AND notification_type = $2
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await self._qe.fetch_row(q, subscription_id, notification_type)
        return self._normalize_json_row(row)

    async def get_last_by_user_and_type(
        self,
        user_id: int,
        notification_type: str,
    ) -> dict[str, Any] | None:
        q = """
            SELECT id, user_id, subscription_id, notification_type, message, status, additional_data,
                   created_at, updated_at
            FROM notifications
            WHERE user_id = $1 AND notification_type = $2
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await self._qe.fetch_row(q, user_id, notification_type)
        return self._normalize_json_row(row)

    async def update_fields(
        self,
        notification_id: int,
        *,
        status: str | None = None,
        message: str | None = None,
        additional_data: dict[str, Any] | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        parts: list[str] = []
        args: list[Any] = []
        i = 1
        u_at = updated_at or datetime.now()
        parts.append(f"updated_at = ${i}")
        args.append(u_at)
        i += 1
        if status is not None:
            parts.append(f"status = ${i}")
            args.append(status)
            i += 1
        if message is not None:
            parts.append(f"message = ${i}")
            args.append(message)
            i += 1
        if additional_data is not None:
            parts.append(f"additional_data = CAST(${i} AS jsonb)")
            args.append(_json_param(additional_data))
            i += 1
        args.append(notification_id)
        q = f"UPDATE notifications SET {', '.join(parts)} WHERE id = ${i}"
        await self._qe.execute(q, *args)

    async def list_active(self, *, user_id: int | None = None) -> list[dict[str, Any]]:
        if user_id is not None:
            q = """
                SELECT id, user_id, subscription_id, notification_type, message, status, additional_data,
                       created_at, updated_at
                FROM notifications
                WHERE status = 'active' AND user_id = $1
                ORDER BY created_at DESC
            """
            rows = await self._qe.fetch(q, user_id)
        else:
            q = """
                SELECT id, user_id, subscription_id, notification_type, message, status, additional_data,
                       created_at, updated_at
                FROM notifications
                WHERE status = 'active'
                ORDER BY created_at DESC
            """
            rows = await self._qe.fetch(q)
        return [r for r in (self._normalize_json_row(x) for x in rows) if r is not None]

    async def delete_before(self, cutoff: datetime) -> None:
        q = "DELETE FROM notifications WHERE created_at < $1"
        await self._qe.execute(q, cutoff)

    async def delete_by_id(self, notification_id: int) -> bool:
        row = await self._qe.fetch_row(
            "DELETE FROM notifications WHERE id = $1 RETURNING id",
            notification_id,
        )
        return row is not None

    @staticmethod
    def _normalize_json_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        ad = row.get("additional_data")
        if isinstance(ad, str):
            try:
                row = {**row, "additional_data": json.loads(ad)}
            except json.JSONDecodeError:
                pass
        return row
