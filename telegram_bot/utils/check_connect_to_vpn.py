import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger

router = Router()

CHAT_ADMIN_ID = 323993202
# Период в днях, после которого можно повторно отправить уведомление
NOTIFICATION_COOLDOWN_DAYS = 7
MIN_SUBSCRIPTION_AGE_HOURS = 8


async def check_connect(bot: Bot):
    """
    Проверяет подключения пользователей и отправляет уведомления админу и пользователю,
    если пользователь активировал подписку, но не подключился
    """
    async with DatabaseContextManager() as session:
        # Получаем все активные подписки
        subs = await session.subscription.get_subs()

        # Проверяем каждую подписку
        for sub in subs:
            await asyncio.sleep(1)

            # Проверяем, прошёл ли минимум 1 час с момента создания подписки
            if datetime.now() - sub.created_at < timedelta(hours=MIN_SUBSCRIPTION_AGE_HOURS):
                continue

            async with DatabaseContextManager() as session_methods:
                # Сначала проверяем, было ли уже отправлено уведомление для этой подписки
                existing_notification = await session_methods.notifications.get_notification_by_subscription(
                    subscription_id=sub.subscription_id,
                    notification_type="no_connection"
                )

                # Если уведомление существует и статус активный, пропускаем эту подписку
                if existing_notification and existing_notification.status == "active":
                    continue

                # Если уведомление существует, но прошло достаточно времени для повторной отправки
                if existing_notification:
                    cooldown_period = timedelta(days=NOTIFICATION_COOLDOWN_DAYS)
                    if datetime.now() - existing_notification.created_at < cooldown_period:
                        continue

                # Проверяем использование ключей подписки
                key_ids = sub.key_ids
                total_usage = 0

                for key_id in key_ids:
                    try:
                        key = await session_methods.keys.get_key_by_id(key_id)
                        if not key:
                            continue

                        key_info = await BaseKeyManager(server_ip=key.server_ip).get_inbound_by_id(key.key_id)
                        total = key_info.get("obj", {}).get("down", 0)
                        total_usage += total

                    except Exception as e:
                        await logger.warning(f"Произошла ошибка при получении ключа {key_id}\n"
                                               f"Сервер: {key.server_ip}")
                        continue

                # Если трафик не использовался, отправляем уведомления
                if total_usage == 0:
                    # Отправляем уведомление админу
                    await bot.send_message(
                        chat_id=CHAT_ADMIN_ID,
                        text=f"Пользователь активировал подписку, но не подключился\n"
                             f"ID пользователя: {sub.user_id}\n"
                             f"ID подписки: {sub.subscription_id}"
                    )

                    # Создаем клавиатуру с кнопкой для перехода в техподдержку
                    support_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🧙‍ Техническая поддержка", url="https://t.me/skydragonsupport")],
                        [InlineKeyboardButton(
                            text="🐉 Мои подписки",
                            callback_data="view_subs"
                        )]
                    ])

                    # Отправляем уведомление пользователю с инструкцией
                    try:
                        await bot.send_message(
                            chat_id=sub.user_id,
                            text=(
                                "🔔 *Мы заметили, что вы активировали подписку, но ещё не подключились к сервису.* 😊\n\n"
                                "Если у вас возникли трудности с подключением, наша *техническая поддержка* с радостью поможет! 💙\n\n"
                                "В разделе *«Мои подписки»* вы найдёте всю информацию:\n"
                                "▪️ *Инструкции* по подключению\n"
                                "▪️ *Продление* и срок действия подписки\n"
                                "▪️ *Другие важные детали*\n\n"
                                "Не стесняйтесь обращаться — мы всегда на связи! 🤗"
                            ),
                            parse_mode="Markdown",
                            reply_markup=support_keyboard
                        )

                        await bot.send_message(
                            chat_id=CHAT_ADMIN_ID,
                            text=f"Уведомили пользователя с ID: {sub.user_id}"
                        )
                    except Exception as e:
                        await logger.log_error(f"Ошибка при отправке уведомления пользователю {sub.user_id}", e)

                    # Создаём или обновляем запись в таблице уведомлений
                    if existing_notification:
                        # Обновляем существующее уведомление
                        await session_methods.notifications.update_notification(
                            notification_id=existing_notification.id,
                            status="active",
                            updated_at=datetime.now()
                        )
                    else:
                        # Создаём новое уведомление
                        await session_methods.notifications.create_notification(
                            user_id=sub.user_id,
                            subscription_id=sub.subscription_id,
                            notification_type="no_connection",
                            message=f"Пользователь {sub.user_id} активировал подписку {sub.subscription_id}, но не подключился",
                            status="active",
                            created_at=datetime.now()
                        )


async def run_checker_connect(bot: Bot):
    """
    Запускает периодическую проверку подключений
    """
    while True:
        try:
            await check_connect(bot)
        except Exception as e:
            await logger.log_error("Ошибка в проверке подключений", e)

        # Изменено время проверки на 3600 секунд (1 час) для более редких проверок
        await asyncio.sleep(3600)  # Проверка каждый час