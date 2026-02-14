"""Ручной запуск проверки онлайна по подпискам (для теста). Админ получает отчёт."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config_data.config import ADMIN_IDS
from filters.admin import IsAdmin
from logger.logging_config import logger
from utils.online_abuse_checker import (
    MAX_CONNECTIONS_PER_SUBSCRIPTION,
    collect_all_online_data,
    _format_abuse_message,
)

router = Router()


@router.message(Command(commands="test_online_check"), IsAdmin(ADMIN_IDS))
async def cmd_test_online_check(message: Message):
    """Запускает одну проверку онлайна и присылает отчёт (и уведомления о нарушениях — только запросившему админу)."""
    await message.answer("Собираю онлайн со всех серверов…")
    try:
        by_sub = await collect_all_online_data()
    except Exception as e:
        await logger.log_error("Ошибка при тестовой проверке онлайна", e)
        await message.answer(f"Ошибка: {e}")
        return

    total_subs = len(by_sub)
    violations = [
        sub_online
        for sub_online in by_sub.values()
        if sub_online.total_keys > MAX_CONNECTIONS_PER_SUBSCRIPTION
    ]

    summary = (
        f"Проверка завершена.\n"
        f"Подписок с онлайном: {total_subs}\n"
        f"С превышением лимита ({MAX_CONNECTIONS_PER_SUBSCRIPTION}): {len(violations)}\n"
    )
    if violations:
        summary += "\nНиже — уведомления о нарушениях (как при автоматической проверке):"
    await message.answer(summary)

    for sub_online in violations:
        try:
            await message.answer(_format_abuse_message(sub_online))
        except Exception as e:
            await logger.log_error("Ошибка отправки тестового уведомления о нарушении", e)
            await message.answer(f"Не удалось отправить блок: {e}")
