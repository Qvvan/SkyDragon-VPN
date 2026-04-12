from datetime import datetime, timezone

from loguru import logger

from src.domain.entities.server import ServerNode
from src.domain.entities.subscription_provision_task import SubscriptionProvisionTask
from src.interfaces.clients.server_panel.client import IServerPanelClient
from src.interfaces.repositories.server import IServerRepository
from src.interfaces.repositories.subscription_provision_task import ISubscriptionProvisionTaskRepository


class SubscriptionProvisionService:
    """
    Оркестрирует создание задач провижнинга и их обработку.

    enqueue_for_subscription() — вызывается при создании/обновлении/отмене подписки.
    process_task()             — вызывается воркером для каждой задачи.
    """

    __slots__ = ("_task_repo", "_server_repo", "_panel_client")

    def __init__(
        self,
        task_repo: ISubscriptionProvisionTaskRepository,
        server_repo: IServerRepository,
        panel_client: IServerPanelClient,
    ) -> None:
        self._task_repo = task_repo
        self._server_repo = server_repo
        self._panel_client = panel_client

    async def enqueue_for_subscription(
        self,
        subscription_id: int,
        user_id: int,
        action: str,
        expire_at: datetime | None,
        max_attempts: int = 5,
    ) -> int:
        """
        Создаёт по одной задаче на каждый видимый сервер.
        Возвращает количество поставленных задач.
        """
        servers = await self._server_repo.list_visible()
        if not servers:
            logger.warning("provision.enqueue | no visible servers, skipping sub_id={}", subscription_id)
            return 0

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        tasks = [
            SubscriptionProvisionTask(
                id=None,
                subscription_id=subscription_id,
                user_id=user_id,
                server_ip=server.server_ip,
                action=action,
                status="pending",
                attempts=0,
                max_attempts=max_attempts,
                last_error=None,
                expire_at=expire_at,
                scheduled_at=now,
                done_at=None,
                created_at=None,
            )
            for server in servers
        ]
        await self._task_repo.bulk_insert(tasks)
        logger.info(
            "provision.enqueue | sub_id={} action={} tasks={}",
            subscription_id,
            action,
            len(tasks),
        )
        return len(tasks)

    async def process_task(self, task: SubscriptionProvisionTask) -> None:
        """
        Выполняет одну задачу. Помечает done или возвращает в pending с backoff.
        Не кидает исключений — ошибки пишет в репозиторий.
        """
        server = ServerNode(
            server_ip=task.server_ip,
            name=task.server_name or task.server_ip,
            limit=None,
            hidden=0,
            available_ports=None,
            panel_port=task.server_panel_port,
            url_secret=task.server_url_secret,
            sub_port=task.server_sub_port,
            created_at=None,
        )
        try:
            await self._panel_client.provision(
                server=server,
                user_id=task.user_id,
                subscription_id=task.subscription_id,
                action=task.action,
                expire_at=task.expire_at,
            )
            await self._task_repo.mark_done(task.id)
            logger.info(
                "provision.done | task_id={} server={} action={}",
                task.id,
                task.server_ip,
                task.action,
            )
        except Exception as exc:
            retry_seconds = min(30 * (2 ** task.attempts), 3600)  # 30s → 60s → 120s … max 1h
            await self._task_repo.mark_failed(task.id, str(exc), retry_seconds)
            logger.warning(
                "provision.failed | task_id={} server={} attempt={} retry_in={}s error={}",
                task.id,
                task.server_ip,
                task.attempts,
                retry_seconds,
                exc,
            )

    async def claim_and_process_batch(self, batch_size: int = 50) -> int:
        """
        Берёт пачку задач и обрабатывает их. Возвращает количество обработанных.
        Вызывается воркером в каждой итерации цикла.
        """
        tasks = await self._task_repo.claim_pending(limit=batch_size)
        for task in tasks:
            await self.process_task(task)
        return len(tasks)

    async def reset_stale(self) -> int:
        """Освобождает зависшие processing-задачи (воркер упал в середине)."""
        count = await self._task_repo.reset_stale_processing(older_than_seconds=300)
        if count:
            logger.warning("provision.reset_stale | released={}", count)
        return count
