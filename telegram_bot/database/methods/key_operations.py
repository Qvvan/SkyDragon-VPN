from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import KeyOperations, Servers


class KeyOperationsMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_operations(
        self,
        user_id: int,
        subscription_id: int,
        action: str,
        servers: list,
        days: int | None = None,
        max_retries: int = 10,
    ) -> None:
        """
        Создаёт по одной операции для каждого сервера из списка.
        Вызывать внутри открытой транзакции — без commit.
        """
        try:
            for server in servers:
                op = KeyOperations(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    server_id=server.server_id,
                    action=action,
                    days=days,
                    status='pending',
                    retry_count=0,
                    max_retries=max_retries,
                )
                self.session.add(op)
            await self.session.flush()
        except SQLAlchemyError as e:
            await logger.log_error(
                f"Ошибка создания key_operations для sub_id={subscription_id}", e
            )
            raise

    async def claim_pending(self, limit: int = 10) -> list[KeyOperations]:
        """
        Атомарно берёт до `limit` pending-операций с данными сервера.
        Использует FOR UPDATE SKIP LOCKED.
        """
        try:
            now = datetime.now(timezone.utc)
            result = await self.session.execute(
                select(KeyOperations)
                .where(
                    KeyOperations.status == 'pending',
                    KeyOperations.scheduled_at <= now,
                    KeyOperations.retry_count < KeyOperations.max_retries,
                )
                .order_by(KeyOperations.scheduled_at.asc())
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            operations = result.scalars().all()

            if operations:
                op_ids = [op.operation_id for op in operations]
                await self.session.execute(
                    update(KeyOperations)
                    .where(KeyOperations.operation_id.in_(op_ids))
                    .values(
                        status='processing',
                        started_at=now,
                        updated_at=now,
                    )
                )
                await self.session.flush()

            return operations
        except SQLAlchemyError as e:
            await logger.log_error("Ошибка при получении pending key_operations", e)
            return []

    async def mark_completed(self, operation_id: int) -> None:
        try:
            now = datetime.now(timezone.utc)
            await self.session.execute(
                update(KeyOperations)
                .where(KeyOperations.operation_id == operation_id)
                .values(status='completed', completed_at=now, updated_at=now)
            )
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка mark_completed для op_id={operation_id}", e)
            raise

    async def mark_failed(self, operation_id: int, error: str, retry_after_seconds: int = 60) -> None:
        """
        Если retry_count < max_retries — возвращает в pending с задержкой (backoff).
        Иначе — окончательно failed.
        """
        try:
            result = await self.session.execute(
                select(KeyOperations).where(KeyOperations.operation_id == operation_id)
            )
            op = result.scalars().first()
            if not op:
                return

            now = datetime.now(timezone.utc)
            op.error_message = error
            op.updated_at = now

            if op.retry_count >= op.max_retries:
                op.status = 'failed'
            else:
                op.status = 'pending'
                op.scheduled_at = now + timedelta(seconds=retry_after_seconds)

            self.session.add(op)
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка mark_failed для op_id={operation_id}", e)
            raise

    async def reset_stale_processing(self, older_than_seconds: int = 300) -> int:
        """Сбрасывает зависшие processing-операции обратно в pending."""
        try:
            threshold = datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
            result = await self.session.execute(
                select(KeyOperations)
                .where(
                    KeyOperations.status == 'processing',
                    KeyOperations.started_at < threshold,
                )
            )
            stale = result.scalars().all()
            now = datetime.now(timezone.utc)
            for op in stale:
                op.status = 'pending'
                op.scheduled_at = now
                op.updated_at = now
                self.session.add(op)
            return len(stale)
        except SQLAlchemyError as e:
            await logger.log_error("Ошибка reset_stale_processing", e)
            return 0
