from datetime import datetime, timezone

from loguru import logger

from src.domain.entities.server import ServerNode
from src.domain.entities.subscription_provision_task import KeyOperation
from src.interfaces.clients.server_panel.client import IServerPanelClient
from src.interfaces.repositories.server import IServerRepository
from src.interfaces.repositories.subscription_provision_task import IKeyOperationRepository


class KeyOperationService:
    """
    Оркестрирует создание задач управления ключами и их обработку.

    enqueue_for_subscription() — вызывается при создании/обновлении/отмене подписки.
    process_operation()        — вызывается воркером для каждой задачи.
    """

    __slots__ = ("_op_repo", "_server_repo", "_panel_client")

    def __init__(
        self,
        op_repo: IKeyOperationRepository,
        server_repo: IServerRepository,
        panel_client: IServerPanelClient,
    ) -> None:
        self._op_repo = op_repo
        self._server_repo = server_repo
        self._panel_client = panel_client

    async def enqueue_for_subscription(
        self,
        subscription_id: str,
        user_id: int,
        action: str,
        days: int | None = None,
        max_retries: int = 10,
    ) -> int:
        """
        Создаёт по одной операции на каждый видимый сервер.
        Возвращает количество поставленных операций.
        """
        servers = await self._server_repo.list_visible()
        if not servers:
            logger.warning("key_ops.enqueue | no visible servers, skipping sub_id={}", subscription_id)
            return 0

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        operations = [
            KeyOperation(
                operation_id=None,
                user_id=user_id,
                subscription_id=subscription_id,
                server_id=server.server_id,
                action=action,
                days=days,
                status="pending",
                retry_count=0,
                max_retries=max_retries,
                error_message=None,
                scheduled_at=now,
                started_at=None,
                completed_at=None,
                created_at=None,
                updated_at=None,
            )
            for server in servers
        ]
        await self._op_repo.bulk_insert(operations)
        logger.info(
            "key_ops.enqueue | sub_id={} action={} operations={}",
            subscription_id,
            action,
            len(operations),
        )
        return len(operations)

    async def process_operation(self, op: KeyOperation) -> None:
        """
        Выполняет одну операцию. Помечает completed или возвращает в pending с backoff.
        Не кидает исключений — ошибки пишет в репозиторий.
        """
        server = ServerNode(
            server_id=op.server_id,
            server_ip=op.server_ip or "",
            name=op.server_name or op.server_ip or "",
            limit=None,
            hidden=0,
            available_ports=op.server_available_ports,
            panel_port=op.server_panel_port,
            url_secret=op.server_url_secret,
            sub_port=op.server_sub_port,
            created_at=None,
        )
        try:
            await self._panel_client.provision(
                server=server,
                user_id=op.user_id,
                subscription_id=op.subscription_id,
                action=op.action,
                days=op.days,
            )
            await self._op_repo.mark_completed(op.operation_id)
            logger.info(
                "key_ops.completed | op_id={} server={} action={}",
                op.operation_id,
                op.server_ip,
                op.action,
            )
        except Exception as exc:
            retry_seconds = min(30 * (2 ** op.retry_count), 3600)  # 30s → 60s → 120s … max 1h
            await self._op_repo.mark_failed(op.operation_id, str(exc), retry_seconds)
            logger.warning(
                "key_ops.failed | op_id={} server={} retry_count={} retry_in={}s error={}",
                op.operation_id,
                op.server_ip,
                op.retry_count,
                retry_seconds,
                exc,
            )

    async def claim_and_process_batch(self, batch_size: int = 50) -> int:
        """
        Берёт пачку операций и обрабатывает их. Возвращает количество обработанных.
        Вызывается воркером в каждой итерации цикла.
        """
        operations = await self._op_repo.claim_pending(limit=batch_size)
        for op in operations:
            await self.process_operation(op)
        return len(operations)

    async def reset_stale(self) -> int:
        """Освобождает зависшие processing-операции (воркер упал в середине)."""
        count = await self._op_repo.reset_stale_processing(older_than_seconds=300)
        if count:
            logger.warning("key_ops.reset_stale | released={}", count)
        return count


# Backwards-compat alias
SubscriptionProvisionService = KeyOperationService
