import asyncio
from collections import defaultdict
from typing import List

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger

router = Router()

CHAT_ADMIN_ID = 323993202


async def check_multiple_connections(bot: Bot):
    """
    Проверяет подключения пользователей и выявляет случаи, когда один пользователь
    подключен к нескольким ключам в рамках одной подписки
    """
    try:
        # Получаем данные о серверах, ключах и онлайн пользователях
        # Используем библиотеку asyncio для параллельного выполнения запросов
        online_users_by_server = {}
        key_data = {}
        subscription_keys = {}

        async with DatabaseContextManager() as session:
            # Получаем все сервера
            servers = await session.servers.get_all_servers()

            # Асинхронно получаем онлайн пользователей для всех серверов
            get_online_tasks = []
            for server in servers:
                task = fetch_online_users(server.server_ip)
                get_online_tasks.append(task)

            online_results = await asyncio.gather(*get_online_tasks)

            # Сохраняем результаты в словарь
            for i, server in enumerate(servers):
                online_emails = online_results[i]
                if online_emails:
                    online_users_by_server[server.server_ip] = online_emails

            # Если нет онлайн пользователей, выходим
            if not any(online_users_by_server.values()):
                await logger.log_info("Нет онлайн пользователей на серверах")
                return

            # Получаем все ключи из базы
            all_keys = await session.keys.get_all_keys()

            # Создаем словарь email -> key_id
            email_to_key_id = {}
            for key in all_keys:
                if key.email:
                    email_to_key_id[key.email] = key.key_id

            # Получаем все подписки с ключами
            all_subscriptions = await session.subscription.get_subs()

            # Создаем словарь subscription_id -> [key_ids]
            for sub in all_subscriptions:
                if sub.key_ids and len(sub.key_ids) > 0:
                    subscription_keys[sub.subscription_id] = sub.key_ids

            # Создаем обратный словарь key_id -> subscription_id
            key_to_subscription = {}
            for sub_id, key_ids in subscription_keys.items():
                for key_id in key_ids:
                    key_to_subscription[key_id] = sub_id

            # Отображение онлайн пользователей по подпискам и серверам
            subscription_online_users = defaultdict(lambda: defaultdict(list))

            for server_ip, online_emails in online_users_by_server.items():
                for email in online_emails:
                    # Находим key_id по email
                    key_id = email_to_key_id.get(email)
                    if not key_id:
                        continue

                    # Находим subscription_id по key_id
                    sub_id = key_to_subscription.get(key_id)
                    if not sub_id:
                        continue

                    # Добавляем сервер и email в список подписки
                    subscription_online_users[sub_id][server_ip].append(email)

            # Выявляем подписки с множественными подключениями
            issues_found = False

            for sub_id, server_data in subscription_online_users.items():
                # Считаем общее количество подключений по подписке
                total_connections = sum(len(emails) for emails in server_data.values())

                # Если больше одного подключения
                if total_connections > 1:
                    issues_found = True

                    # Формируем сообщение для админа
                    message = f"⚠️ Обнаружено множественное подключение!\n\n"
                    message += f"Подписка ID: {sub_id}\n"
                    message += f"Всего активных подключений: {total_connections}\n\n"
                    message += "Подключения по серверам:\n"

                    for server_ip, emails in server_data.items():
                        message += f"\n🖥 Сервер: {server_ip}\n"
                        for email in emails:
                            key_id = email_to_key_id.get(email, "Неизвестный ключ")
                            message += f"  • Email: {email} (Key ID: {key_id})\n"

                    # Получаем информацию о пользователе
                    try:
                        sub_info = await session.subscription.get_subscription_by_id(sub_id)
                        if sub_info:
                            user_id = sub_info.get('user_id')
                            message += f"\nПользователь ID: {user_id}\n"
                    except Exception as e:
                        await logger.warning(
                            f"Не удалось получить данные о пользователе для подписки {sub_id}: {str(e)}")

                    # Отправляем сообщение админу
                    try:
                        await bot.send_message(CHAT_ADMIN_ID, message, parse_mode="HTML")
                        await logger.log_info(
                            f"Отправлено уведомление о множественных подключениях для подписки {sub_id}")
                    except Exception as e:
                        await logger.log_error(f"Ошибка при отправке уведомления админу: {str(e)}")

            if not issues_found:
                await logger.log_info("Множественных подключений не обнаружено")

    except Exception as e:
        await logger.log_error(f"Ошибка при проверке множественных подключений", e)


async def fetch_online_users(server_ip: str) -> List[str]:
    """
    Получает список email пользователей, которые в данный момент онлайн на сервере
    """
    try:
        online_data = await BaseKeyManager(server_ip=server_ip).get_online_users()
        if online_data and online_data.get("success") and online_data.get("obj"):
            return online_data.get("obj", [])
        return []
    except Exception as e:
        await logger.warning(f"Ошибка при получении онлайн пользователей с сервера {server_ip}: {str(e)}")
        return []


async def run_multiple_connections_checker(bot: Bot):
    """
    Запускает периодическую проверку множественных подключений
    """
    while True:
        try:
            await bot.send_message(chat_id=CHAT_ADMIN_ID, text="Начинаем проверку множественных подключений")
            await check_multiple_connections(bot)
        except Exception as e:
            await logger.log_error("Ошибка в проверке множественных подключений", e)

        # Проверка каждые 15 минут
        await asyncio.sleep(900)
