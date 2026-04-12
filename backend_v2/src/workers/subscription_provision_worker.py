"""
Воркер провижнинга подписок на VPN-серверах.

Запуск:
    python -m src.workers.subscription_provision_worker

Воркер читает таблицу subscription_provision_tasks и выполняет действия
на панелях серверов (create / update / delete).
Использует FOR UPDATE SKIP LOCKED — безопасен для запуска в нескольких репликах.
"""

import asyncio
import signal
import sys

from loguru import logger

from src.core.config import Config
from src.core.container import Container


class SubscriptionProvisionWorker:
    """Тонкий polling-цикл. Вся логика — в SubscriptionProvisionService."""

    __slots__ = ("_service", "_running", "_poll_interval", "_stale_reset_interval", "_batch_size")

    def __init__(
        self,
        service,
        poll_interval: float = 5.0,
        stale_reset_interval: float = 60.0,
        batch_size: int = 50,
    ) -> None:
        self._service = service
        self._running = True
        self._poll_interval = poll_interval
        self._stale_reset_interval = stale_reset_interval
        self._batch_size = batch_size

    def stop(self) -> None:
        self._running = False

    async def run(self) -> None:
        logger.info("provision_worker.start | poll={}s batch={}", self._poll_interval, self._batch_size)
        last_stale_reset = 0.0

        while self._running:
            now = asyncio.get_event_loop().time()

            # Периодически сбрасываем зависшие processing-задачи
            if now - last_stale_reset >= self._stale_reset_interval:
                await self._service.reset_stale()
                last_stale_reset = now

            processed = await self._service.claim_and_process_batch(self._batch_size)

            # Если задач нет — ждём; если были — сразу следующий цикл (backlog)
            if processed == 0:
                await asyncio.sleep(self._poll_interval)

        logger.info("provision_worker.stopped")


async def main() -> None:
    config = Config.load()
    container = Container(config)

    try:
        await container.infra.init()
        service = container.services.subscription_provision_service

        worker = SubscriptionProvisionWorker(service)

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, worker.stop)

        await worker.run()
    finally:
        await container.infra.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
