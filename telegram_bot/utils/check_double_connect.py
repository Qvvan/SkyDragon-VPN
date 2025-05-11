import asyncio
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
        # Словарь для хранения онлайн пользователей на каждом сервере
        online_users_by_server = {}

        # Словарь для хранения информации о подписках и пользователях
        subscription_user_info = {}

        # Словарь для хранения данных о ключах
        key_info = {}

        async with DatabaseContextManager() as session:
            # Получаем все сервера
            servers = await session.servers.get_all_servers()

            # Создаем словарь server_ip -> server_name для более информативных сообщений
            server_names = {server.server_ip: server.name for server in servers}

            # Асинхронно получаем онлайн пользователей для всех серверов
            get_online_tasks = []
            for server in servers:
                task = fetch_online_users(server.server_ip)
                get_online_tasks.append((server.server_ip, task))

            # Ожидаем завершения всех задач
            for server_ip, task in get_online_tasks:
                try:
                    online_emails = await task
                    if online_emails:
                        online_users_by_server[server_ip] = online_emails
                except Exception as e:
                    await logger.warning(f"Ошибка при получении онлайн пользователей для сервера {server_ip}: {str(e)}")

            # Если нет онлайн пользователей, выходим
            if not any(online_users_by_server.values()):
                await logger.log_info("Нет онлайн пользователей на серверах")
                return

            # Получаем все ключи из базы
            all_keys = await session.keys.get_all_keys()

            # Словарь email -> ключ (объект)
            email_to_key = {}
            # Словарь key_id -> (server_ip, email)
            key_info = {}

            for key in all_keys:
                if key.email:
                    email_to_key[key.email] = key
                    key_info[key.key_id] = (key.server_ip, key.email, key.id)

            # Получаем все подписки с ключами
            all_subscriptions = await session.subscription.get_subs()

            # Создаем мапу key_id -> subscription_id
            key_to_subscription = {}
            # Создаем мапу subscription_id -> user_id
            subscription_to_user = {}
            # Создаем словарь subscription_id -> [key_ids]
            subscription_keys = {}

            for sub in all_subscriptions:
                if hasattr(sub, 'user_id'):
                    subscription_to_user[sub.subscription_id] = sub.user_id

                if hasattr(sub, 'key_ids') and sub.key_ids:
                    subscription_keys[sub.subscription_id] = sub.key_ids
                    for key_id in sub.key_ids:
                        key_to_subscription[key_id] = sub.subscription_id

            # Структура для хранения информации о пользователях с множественными подключениями
            # user_id -> {subscription_id -> {server_ip -> [email]}}
            user_connections = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

            # Анализируем онлайн подключения
            for server_ip, online_emails in online_users_by_server.items():
                for email in online_emails:
                    # Находим соответствующий ключ
                    key = email_to_key.get(email)
                    if not key:
                        continue

                    # Находим подписку по ключу
                    sub_id = key_to_subscription.get(key.key_id)
                    if not sub_id:
                        continue

                    # Находим пользователя по подписке
                    user_id = subscription_to_user.get(sub_id)
                    if not user_id:
                        continue

                    # Добавляем подключение в структуру
                    user_connections[user_id][sub_id][server_ip].append(email)

            # Проверяем наличие множественных подключений
            issues_found = False

            for user_id, user_data in user_connections.items():
                for sub_id, server_data in user_data.items():
                    # Подсчитываем общее количество подключений
                    total_connections = sum(len(emails) for emails in server_data.values())

                    # Если больше одного подключения
                    if total_connections > 1:
                        issues_found = True

                        # Формируем сообщение для админа
                        message = f"⚠️ <b>Обнаружено множественное подключение!</b>\n\n"
                        message += f"👤 <b>Пользователь ID:</b> {user_id}\n"
                        message += f"🔑 <b>Подписка ID:</b> {sub_id}\n"
                        message += f"📊 <b>Всего активных подключений:</b> {total_connections}\n\n"
                        message += "<b>Подключения по серверам:</b>\n"

                        # Информация по каждому серверу
                        for server_ip, emails in server_data.items():
                            server_name = server_names.get(server_ip, "Неизвестный сервер")
                            message += f"\n🖥 <b>Сервер:</b> {server_name} ({server_ip})\n"

                            for email in emails:
                                key = email_to_key.get(email)
                                if key:
                                    message += f"  • Email: <code>{email}</code>\n"
                                    message += f"    Key ID (панель): <code>{key.key_id}</code>\n"
                                    message += f"    Key ID (БД): <code>{key.id}</code>\n"

                        # Добавляем кнопки для быстрых действий
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Деактивировать все ключи",
                                                  callback_data=f"deactivate_keys:{user_id}:{sub_id}")],
                            [InlineKeyboardButton(text="Отправить предупреждение",
                                                  callback_data=f"warn_user:{user_id}:{sub_id}")]
                        ])

                        # Отправляем сообщение админу
                        try:
                            await bot.send_message(CHAT_ADMIN_ID, message, parse_mode="HTML", reply_markup=keyboard)
                            await logger.log_info(
                                f"Отправлено уведомление о множественных подключениях пользователя {user_id}, подписка {sub_id}")
                        except Exception as e:
                            await logger.log_error(f"Ошибка при отправке уведомления админу: {str(e)}")

            if not issues_found:
                await logger.log_info("Множественных подключений не обнаружено")

    except Exception as e:
        await logger.log_error(f"Ошибка при проверке множественных подключений: {str(e)}", e)


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
            await check_multiple_connections(bot)
        except Exception as e:
            await logger.log_error("Ошибка в проверке множественных подключений", e)

        # Проверка каждые 10 минут - более частая проверка для быстрого обнаружения нарушений
        await asyncio.sleep(600)


# Обработчики колбеков от кнопок
@router.callback_query(lambda c: c.data.startswith("deactivate_keys:"))
async def deactivate_keys_handler(callback_query: CallbackQuery, bot: Bot):
    """Обработчик для деактивации всех ключей пользователя по подписке"""
    try:
        # Получаем user_id и subscription_id из callback_data
        _, user_id, sub_id = callback_query.data.split(":")
        user_id = int(user_id)
        sub_id = int(sub_id)

        async with DatabaseContextManager() as session:
            # Получаем подписку
            subscription = await session.subscription.get_subscription_by_id(sub_id)
            if not subscription:
                await callback_query.answer("Подписка не найдена!")
                return

            # Получаем ключи подписки
            key_ids = subscription.get('key_ids', [])
            if not key_ids:
                await callback_query.answer("У подписки нет ключей!")
                return

            # Деактивируем все ключи
            deactivated_count = 0
            for key_id in key_ids:
                # Получаем ключ из базы
                key = await session.keys.get_key_by_key_id(key_id)
                if key:
                    # Меняем статус на неактивный
                    await session.keys.update_key(key.id, status='inactive')
                    deactivated_count += 1

            await session.session.commit()

            # Отправляем сообщение пользователю
            try:
                await bot.send_message(
                    user_id,
                    "❗️ Ваша подписка была деактивирована администратором из-за нарушения правил использования сервиса. "
                    "Для получения дополнительной информации обратитесь в поддержку."
                )
            except Exception as e:
                await logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {str(e)}")

            # Отвечаем на колбек
            await callback_query.answer(f"Деактивировано {deactivated_count} ключей!")

            # Обновляем сообщение
            await callback_query.message.edit_text(
                callback_query.message.text + f"\n\n✅ <b>Ключи деактивированы: {deactivated_count}</b>",
                parse_mode="HTML"
            )

            await logger.log_info(
                f"Администратор деактивировал {deactivated_count} ключей для пользователя {user_id}, подписка {sub_id}")

    except Exception as e:
        await logger.log_error(f"Ошибка при деактивации ключей: {str(e)}")
        await callback_query.answer("Произошла ошибка при деактивации ключей!")


@router.callback_query(lambda c: c.data.startswith("warn_user:"))
async def warn_user_handler(callback_query: CallbackQuery, bot: Bot):
    """Обработчик для отправки предупреждения пользователю"""
    try:
        # Получаем user_id и subscription_id из callback_data
        _, user_id, sub_id = callback_query.data.split(":")
        user_id = int(user_id)
        sub_id = int(sub_id)

        # Отправляем предупреждение пользователю
        try:
            await bot.send_message(
                chat_id=CHAT_ADMIN_ID,
                text="⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n\n"
                "Обнаружено нарушение правил использования сервиса: одновременное использование нескольких подключений "
                "в рамках одной подписки.\n\n"
                "Пожалуйста, прекратите использование множественных подключений. "
                "В случае продолжения нарушений, ваша подписка может быть деактивирована без возможности возврата средств.\n\n"
                "Если вы считаете, что произошла ошибка, пожалуйста, свяжитесь с нашей поддержкой.",
                parse_mode="HTML"
            )
            await callback_query.answer("Предупреждение отправлено!")

            # Обновляем сообщение
            await callback_query.message.edit_text(
                callback_query.message.text + "\n\n✅ <b>Предупреждение отправлено</b>",
                parse_mode="HTML",
                reply_markup=callback_query.message.reply_markup
            )

            await logger.log_info(f"Администратор отправил предупреждение пользователю {user_id}, подписка {sub_id}")

        except Exception as e:
            await logger.warning(f"Не удалось отправить предупреждение пользователю {user_id}: {str(e)}")
            await callback_query.answer("Не удалось отправить предупреждение пользователю!")

    except Exception as e:
        await logger.log_error(f"Ошибка при отправке предупреждения: {str(e)}")
        await callback_query.answer("Произошла ошибка при отправке предупреждения!")