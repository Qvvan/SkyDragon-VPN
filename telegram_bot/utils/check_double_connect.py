import asyncio
from collections import defaultdict

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger

router = Router()


async def check_multiple_connections(bot: Bot):
    """
    Проверяет подключения пользователей и выявляет случаи, когда один пользователь
    подключен к нескольким ключам в рамках одной подписки
    """
    try:
        async with DatabaseContextManager() as session:
            # Получаем все сервера
            servers = await session.servers.get_all_servers()

            # Создаем словарь server_ip -> server_name
            server_names = {server.server_ip: server.name for server in servers}

            # Получаем онлайн пользователей для каждого сервера
            server_online_users = {}

            for server in servers:
                try:
                    online_data = await BaseKeyManager(server_ip=server.server_ip).get_online_users()
                    if online_data and online_data.get("success") and online_data.get("obj"):
                        online_emails = online_data.get("obj", [])
                        if online_emails:
                            server_online_users[server.server_ip] = online_emails
                except Exception as e:
                    await logger.warning(
                        f"Ошибка при получении онлайн пользователей для сервера {server.server_ip}: {str(e)}")

            # Если нет онлайн пользователей, выходим
            if not server_online_users:
                await logger.log_info("Нет онлайн пользователей на серверах")
                return

            # Получаем все ключи из базы
            all_keys = await session.keys.get_all_keys()

            # Создаем словарь email -> key
            email_to_key = {}
            for key in all_keys:
                if key.email:
                    email_to_key[key.email] = key

            # Получаем все подписки
            all_subscriptions = await session.subscription.get_subs()

            # Создаем словарь subscription_id -> user_id
            subscription_to_user = {}
            # Создаем словарь subscription_id -> [key_ids]
            subscription_to_keys = {}

            for sub in all_subscriptions:
                subscription_to_user[sub.subscription_id] = sub.user_id
                if hasattr(sub, 'key_ids') and sub.key_ids:
                    subscription_to_keys[sub.subscription_id] = sub.key_ids

            # Создаем словарь key_id -> subscription_id
            key_to_subscription = {}
            for sub_id, key_ids in subscription_to_keys.items():
                for key_id in key_ids:
                    key_to_subscription[key_id] = sub_id

            # Словарь для отслеживания подключений пользователей
            # structure: subscription_id -> {server_ip -> [email]}
            subscription_connections = defaultdict(lambda: defaultdict(list))

            # Заполняем структуру данными о подключениях
            for server_ip, online_emails in server_online_users.items():
                for email in online_emails:
                    key = email_to_key.get(email)
                    if not key:
                        continue

                    sub_id = key_to_subscription.get(key.key_id)
                    if not sub_id:
                        continue

                    subscription_connections[sub_id][server_ip].append((email, key.key_id))

            # Проверяем множественные подключения
            for sub_id, server_data in subscription_connections.items():
                # Подсчитываем общее количество подключений
                flat_connections = [(server, email, key_id) for server, connections in server_data.items()
                                    for email, key_id in connections]

                if len(flat_connections) > 1:
                    user_id = subscription_to_user.get(sub_id, "Неизвестный пользователь")

                    # Формируем информационное сообщение
                    message = f"⚠️ Обнаружено множественное подключение!\n\n"
                    message += f"Пользователь ID: {user_id}\n"
                    message += f"Подписка ID: {sub_id}\n"
                    message += f"Всего активных подключений: {len(flat_connections)}\n\n"
                    message += "Детали подключений:\n"

                    # Группируем подключения по серверам для лучшей читаемости
                    for server_ip, connections in server_data.items():
                        server_name = server_names.get(server_ip, "Неизвестный сервер")
                        message += f"\nСервер: {server_name} ({server_ip})\n"

                        for email, key_id in connections:
                            key = email_to_key.get(email)
                            if key:
                                message += f"  • Email: {email}\n"
                                message += f"    Key ID (панель): {key.key_id}\n"
                                message += f"    Key ID (БД): {key.id}\n"

                    # Отправляем информацию в лог
                    await logger.log_info(message)

    except Exception as e:
        await logger.log_error(f"Ошибка при проверке множественных подключений: {str(e)}")


async def run_multiple_connections_checker(bot: Bot):
    """
    Запускает периодическую проверку множественных подключений
    """
    while True:
        try:
            await check_multiple_connections(bot)
        except Exception as e:
            await logger.log_error("Ошибка в проверке множественных подключений", e)

        # Проверка каждые 10 минут
        await asyncio.sleep(600)
