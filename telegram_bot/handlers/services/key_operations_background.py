"""Фоновые задачи для создания и обновления ключей"""
import asyncio

from handlers.services.create_keys import create_keys
from handlers.services.update_keys import update_keys
from logger.logging_config import logger


async def create_keys_background(user_id: int, username: str, subscription_id: int, expiry_days: int = 0):
    """
    Фоновая задача для создания ключей.
    Вызывается асинхронно после того, как пользователь получил ответ об успехе.

    Args:
        user_id: ID пользователя Telegram
        username: Имя пользователя (для логирования)
        subscription_id: ID подписки
        expiry_days: Количество дней до истечения (0 = без ограничений)
    """
    try:
        await logger.info(
            f"Запуск фонового создания ключей: user_id={user_id}, username={username}, "
            f"subscription_id={subscription_id}, expiry_days={expiry_days}"
        )
        
        result = await create_keys(user_id, username, subscription_id, expiry_days)
        
        if result:
            await logger.info(
                f"Фоновое создание ключей завершено успешно: user_id={user_id}, "
                f"subscription_id={subscription_id}"
            )
        else:
            await logger.warning(
                f"Фоновое создание ключей завершено с ошибками: user_id={user_id}, "
                f"subscription_id={subscription_id}"
            )
            
    except Exception as e:
        # Логируем ошибку, но не пробрасываем её дальше
        await logger.log_error(
            f"Критическая ошибка в фоновом создании ключей: user_id={user_id}, "
            f"subscription_id={subscription_id}", e
        )


async def update_keys_background(user_id: int, subscription_id: int, status: bool):
    """
    Фоновая задача для обновления статуса ключей.
    Вызывается асинхронно после того, как пользователь получил ответ об успехе.

    Args:
        user_id: ID пользователя Telegram
        subscription_id: ID подписки
        status: True для включения, False для выключения
    """
    try:
        await logger.info(
            f"Запуск фонового обновления ключей: user_id={user_id}, "
            f"subscription_id={subscription_id}, status={status}"
        )
        
        await update_keys(user_id, subscription_id, status)
        
        await logger.info(
            f"Фоновое обновление ключей завершено: user_id={user_id}, "
            f"subscription_id={subscription_id}, status={status}"
        )
            
    except Exception as e:
        # Логируем ошибку, но не пробрасываем её дальше
        await logger.log_error(
            f"Критическая ошибка в фоновом обновлении ключей: user_id={user_id}, "
            f"subscription_id={subscription_id}, status={status}", e
        )
