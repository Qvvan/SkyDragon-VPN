"""
Хелперы для постановки операций с ключами в очередь (таблица key_operations).

Вызываются внутри уже открытой транзакции (session_methods передаётся извне).
Commit делает вызывающий код — это позволяет атомарно сохранить
и подписку, и операции с ключами в одной транзакции.
"""
from logger.logging_config import logger


async def enqueue_create(
    user_id: int,
    subscription_id: int,
    session_methods,
    days: int | None = None,
) -> None:
    """Ставит в очередь операцию 'create' для всех активных серверов."""
    servers = await session_methods.servers.get_active_servers_for_keys()
    if not servers:
        await logger.warning(
            f"enqueue_create: нет доступных серверов для sub_id={subscription_id}"
        )
        return
    await session_methods.key_operations.create_operations(
        user_id=user_id,
        subscription_id=subscription_id,
        action='create',
        servers=servers,
        days=days,
    )
    await logger.info(
        f"enqueue_create: {len(servers)} операций для sub_id={subscription_id}"
    )


async def enqueue_enable(
    user_id: int,
    subscription_id: int,
    session_methods,
) -> None:
    """Ставит в очередь операцию 'enable' для всех активных серверов."""
    servers = await session_methods.servers.get_active_servers_for_keys()
    if not servers:
        await logger.warning(
            f"enqueue_enable: нет доступных серверов для sub_id={subscription_id}"
        )
        return
    await session_methods.key_operations.create_operations(
        user_id=user_id,
        subscription_id=subscription_id,
        action='enable',
        servers=servers,
    )
    await logger.info(
        f"enqueue_enable: {len(servers)} операций для sub_id={subscription_id}"
    )


async def enqueue_delete(
    user_id: int,
    subscription_id: int,
    session_methods,
) -> None:
    """Ставит в очередь операцию 'delete' для всех активных серверов."""
    servers = await session_methods.servers.get_active_servers_for_keys()
    if not servers:
        return
    await session_methods.key_operations.create_operations(
        user_id=user_id,
        subscription_id=subscription_id,
        action='delete',
        servers=servers,
    )


async def enqueue_disable(
    user_id: int,
    subscription_id: int,
    session_methods,
) -> None:
    """Ставит в очередь операцию 'disable' для всех активных серверов."""
    servers = await session_methods.servers.get_active_servers_for_keys()
    if not servers:
        return
    await session_methods.key_operations.create_operations(
        user_id=user_id,
        subscription_id=subscription_id,
        action='disable',
        servers=servers,
    )
    await logger.info(
        f"enqueue_disable: {len(servers)} операций для sub_id={subscription_id}"
    )


# ── Backwards-compat wrappers для старого API ────────────────────────────────
# Позволяют использовать asyncio.create_task(create_keys_background(...)) без изменения
# вызывающего кода — просто записывают операцию в key_operations вместо прямого вызова панели.

async def create_keys_background(
    user_id: int,
    username: str,
    subscription_id: int,
    expiry_days: int = 0,
) -> None:
    from database.context_manager import DatabaseContextManager
    async with DatabaseContextManager() as sm:
        await enqueue_create(user_id, subscription_id, sm, days=expiry_days or None)
        await sm.session.commit()


async def update_keys_background(
    user_id: int,
    subscription_id: int,
    status: bool = True,
) -> None:
    from database.context_manager import DatabaseContextManager
    async with DatabaseContextManager() as sm:
        if status:
            await enqueue_enable(user_id, subscription_id, sm)
        else:
            await enqueue_disable(user_id, subscription_id, sm)
        await sm.session.commit()
