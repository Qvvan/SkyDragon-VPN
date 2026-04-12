from datetime import datetime, timezone

import asyncpg

from src.domain.entities.subscription_provision_task import SubscriptionProvisionTask
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.subscription_provision_task import ISubscriptionProvisionTaskRepository

_SELECT_FIELDS = """
    t.id, t.subscription_id, t.user_id, t.server_ip, t.action, t.status,
    t.attempts, t.max_attempts, t.last_error, t.expire_at,
    t.scheduled_at, t.done_at, t.created_at,
    s.name        AS server_name,
    s.panel_port  AS server_panel_port,
    s.url_secret  AS server_url_secret,
    s.sub_port    AS server_sub_port
"""


class PostgresSubscriptionProvisionTaskRepository(ISubscriptionProvisionTaskRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def bulk_insert(self, tasks: list[SubscriptionProvisionTask]) -> None:
        if not tasks:
            return
        query = """
            INSERT INTO subscription_provision_tasks
                (subscription_id, user_id, server_ip, action, status,
                 attempts, max_attempts, expire_at, scheduled_at)
            SELECT
                r.subscription_id, r.user_id, r.server_ip, r.action, 'pending',
                0, r.max_attempts, r.expire_at, CURRENT_TIMESTAMP
            FROM unnest($1::int[], $2::bigint[], $3::text[], $4::text[], $5::int[], $6::timestamp[])
                AS r(subscription_id, user_id, server_ip, action, max_attempts, expire_at)
        """
        await self._query_executor.execute(
            query,
            [t.subscription_id for t in tasks],
            [t.user_id for t in tasks],
            [t.server_ip for t in tasks],
            [t.action for t in tasks],
            [t.max_attempts for t in tasks],
            [t.expire_at for t in tasks],
        )

    async def claim_pending(self, limit: int = 50) -> list[SubscriptionProvisionTask]:
        query = f"""
            WITH claimed AS (
                UPDATE subscription_provision_tasks
                SET status = 'processing', attempts = attempts + 1
                WHERE id IN (
                    SELECT id FROM subscription_provision_tasks
                    WHERE status = 'pending'
                      AND scheduled_at <= CURRENT_TIMESTAMP
                    ORDER BY scheduled_at ASC
                    LIMIT $1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING *
            )
            SELECT {_SELECT_FIELDS}
            FROM claimed t
            LEFT JOIN servers s ON s.server_ip = t.server_ip
        """
        rows = await self._query_executor.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def mark_done(self, task_id: int) -> None:
        query = """
            UPDATE subscription_provision_tasks
            SET status = 'done', done_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        await self._query_executor.execute(query, task_id)

    async def mark_failed(self, task_id: int, error: str, retry_after_seconds: int) -> None:
        query = """
            UPDATE subscription_provision_tasks
            SET
                status       = CASE
                                   WHEN attempts >= max_attempts THEN 'failed'
                                   ELSE 'pending'
                               END,
                last_error   = $2,
                scheduled_at = CASE
                                   WHEN attempts >= max_attempts THEN scheduled_at
                                   ELSE CURRENT_TIMESTAMP + ($3 * INTERVAL '1 second')
                               END
            WHERE id = $1
        """
        await self._query_executor.execute(query, task_id, error, retry_after_seconds)

    async def reset_stale_processing(self, older_than_seconds: int = 300) -> int:
        query = """
            UPDATE subscription_provision_tasks
            SET status = 'pending', scheduled_at = CURRENT_TIMESTAMP
            WHERE status = 'processing'
              AND scheduled_at < CURRENT_TIMESTAMP - ($1 * INTERVAL '1 second')
        """
        result = await self._query_executor.execute(query, older_than_seconds)
        try:
            return int(result.split()[-1])
        except (ValueError, AttributeError, IndexError):
            return 0

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> SubscriptionProvisionTask:
        return SubscriptionProvisionTask(
            id=row["id"],
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            server_ip=row["server_ip"],
            action=row["action"],
            status=row["status"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            last_error=row["last_error"],
            expire_at=row["expire_at"],
            scheduled_at=row["scheduled_at"],
            done_at=row["done_at"],
            created_at=row["created_at"],
            server_name=row["server_name"],
            server_panel_port=row["server_panel_port"],
            server_url_secret=row["server_url_secret"],
            server_sub_port=row["server_sub_port"],
        )
