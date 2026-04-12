from datetime import datetime, timezone

import asyncpg

from src.domain.entities.subscription_provision_task import KeyOperation
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.subscription_provision_task import IKeyOperationRepository

_SELECT_FIELDS = """
    op.operation_id, op.user_id, op.subscription_id, op.server_id, op.action, op.days,
    op.status, op.retry_count, op.max_retries, op.error_message,
    op.scheduled_at, op.started_at, op.completed_at, op.created_at, op.updated_at,
    s.server_ip       AS server_ip,
    s.name            AS server_name,
    s.panel_port      AS server_panel_port,
    s.url_secret      AS server_url_secret,
    s.sub_port        AS server_sub_port,
    s.available_ports AS server_available_ports
"""


class PostgresKeyOperationRepository(IKeyOperationRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def bulk_insert(self, operations: list[KeyOperation]) -> None:
        if not operations:
            return
        query = """
            INSERT INTO key_operations
                (user_id, subscription_id, server_id, action, days, status,
                 retry_count, max_retries, scheduled_at)
            SELECT
                r.user_id, r.subscription_id, r.server_id, r.action::key_operation_action,
                r.days, 'pending', 0, r.max_retries, CURRENT_TIMESTAMP
            FROM unnest($1::bigint[], $2::uuid[], $3::int[], $4::text[], $5::int[], $6::int[])
                AS r(user_id, subscription_id, server_id, action, days, max_retries)
        """
        await self._query_executor.execute(
            query,
            [op.user_id for op in operations],
            [op.subscription_id for op in operations],
            [op.server_id for op in operations],
            [op.action for op in operations],
            [op.days for op in operations],
            [op.max_retries for op in operations],
        )

    async def claim_pending(self, limit: int = 50) -> list[KeyOperation]:
        query = f"""
            WITH claimed AS (
                UPDATE key_operations
                SET status = 'processing',
                    retry_count = retry_count + 1,
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE operation_id IN (
                    SELECT operation_id FROM key_operations
                    WHERE status = 'pending'
                      AND scheduled_at <= CURRENT_TIMESTAMP
                    ORDER BY scheduled_at ASC
                    LIMIT $1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING *
            )
            SELECT {_SELECT_FIELDS}
            FROM claimed op
            JOIN servers s ON s.server_id = op.server_id
        """
        rows = await self._query_executor.fetch(query, limit)
        return [self._row_to_entity(row) for row in rows]

    async def mark_completed(self, operation_id: int) -> None:
        query = """
            UPDATE key_operations
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE operation_id = $1
        """
        await self._query_executor.execute(query, operation_id)

    async def mark_failed(self, operation_id: int, error: str, retry_after_seconds: int) -> None:
        query = """
            UPDATE key_operations
            SET
                status        = CASE
                                    WHEN retry_count >= max_retries THEN 'failed'
                                    ELSE 'pending'
                                END,
                error_message = $2,
                scheduled_at  = CASE
                                    WHEN retry_count >= max_retries THEN scheduled_at
                                    ELSE CURRENT_TIMESTAMP + ($3 * INTERVAL '1 second')
                                END,
                updated_at    = CURRENT_TIMESTAMP
            WHERE operation_id = $1
        """
        await self._query_executor.execute(query, operation_id, error, retry_after_seconds)

    async def reset_stale_processing(self, older_than_seconds: int = 300) -> int:
        query = """
            UPDATE key_operations
            SET status = 'pending',
                scheduled_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'processing'
              AND started_at < CURRENT_TIMESTAMP - ($1 * INTERVAL '1 second')
        """
        result = await self._query_executor.execute(query, older_than_seconds)
        try:
            return int(result.split()[-1])
        except (ValueError, AttributeError, IndexError):
            return 0

    @staticmethod
    def _row_to_entity(row: asyncpg.Record) -> KeyOperation:
        return KeyOperation(
            operation_id=row["operation_id"],
            user_id=row["user_id"],
            subscription_id=str(row["subscription_id"]),
            server_id=row["server_id"],
            action=row["action"],
            days=row["days"],
            status=row["status"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            error_message=row["error_message"],
            scheduled_at=row["scheduled_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            server_ip=row["server_ip"],
            server_name=row["server_name"],
            server_panel_port=row["server_panel_port"],
            server_url_secret=row["server_url_secret"],
            server_sub_port=row["server_sub_port"],
            server_available_ports=row["server_available_ports"],
        )


# Backwards-compat alias
PostgresSubscriptionProvisionTaskRepository = PostgresKeyOperationRepository
