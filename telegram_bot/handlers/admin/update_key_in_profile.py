from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from collections import defaultdict

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger
from models.models import Keys, NameApp

router = Router()


@router.message(Command(commands="update_profile"), IsAdmin(ADMIN_IDS))
async def update_profile(message: Message):
    """
    Создает недостающие ключи для всех пользователей на всех серверах.
    Оптимизированная версия для обработки больших объемов данных.
    """

    processed_users = 0
    created_keys = 0
    error_count = 0

    async with DatabaseContextManager() as session_methods:
        try:
            # ✅ Загружаем все данные одним запросом
            servers = await session_methods.servers.get_all_servers()
            active_servers = [s for s in servers if s.hidden != 1]

            all_keys = await session_methods.keys.get_all_keys()
            all_subscriptions = await session_methods.subscription.get_subs()

            await logger.info(f"Обрабатываем {len(active_servers)} серверов и {len(all_subscriptions)} подписок")

            # ✅ Группируем ключи по пользователям и серверам для быстрого поиска
            user_keys_by_server = defaultdict(lambda: defaultdict(list))
            for key in all_keys:
                # Получаем user_id из подписок (так как в Keys его нет напрямую)
                for sub in all_subscriptions:
                    if key.id in (sub.key_ids or []):
                        user_keys_by_server[sub.user_id][key.server_ip].append(key)
                        break

            # ✅ Обрабатываем каждую подписку
            for subscription in all_subscriptions:
                try:
                    user_id = subscription.user_id

                    # Получаем пользователя для username
                    user = await session_methods.users.get_user(user_id=user_id)
                    if not user:
                        continue

                    new_key_ids = []
                    user_servers = user_keys_by_server[user_id]

                    # ✅ Проверяем каждый сервер
                    for server in active_servers:
                        server_ip = server.server_ip

                        # Проверяем есть ли у пользователя ключи на этом сервере
                        if server_ip not in user_servers or not user_servers[server_ip]:
                            await logger.info(f"Создаем ключ для пользователя {user_id} на сервере {server_ip}")

                            # ✅ Создаем ключ на этом сервере
                            key_id = await _create_key_for_server(
                                session_methods, user_id, server
                            )

                            if key_id:
                                new_key_ids.append(key_id)
                                created_keys += 1

                    # ✅ Обновляем подписку если были созданы новые ключи
                    if new_key_ids:
                        current_key_ids = list(subscription.key_ids) if subscription.key_ids else []
                        updated_key_ids = current_key_ids + new_key_ids

                        await session_methods.subscription.update_sub(
                            subscription_id=subscription.subscription_id,
                            key_ids=updated_key_ids
                        )

                        processed_users += 1
                        await logger.info(
                            f"✅ Обновлена подписка для пользователя {user_id}, добавлено {len(new_key_ids)} ключей")

                except Exception as e:
                    error_count += 1
                    await logger.log_error(f"Ошибка обработки пользователя {subscription.user_id}", e)

            # ✅ Коммитим все изменения одной транзакцией
            await session_methods.session.commit()

            await message.answer(
                f"✅ Обновление профилей завершено:\n"
                f"• Обработано пользователей: {processed_users}\n"
                f"• Создано ключей: {created_keys}\n"
                f"• Ошибок: {error_count}\n"
                f"• Всего подписок: {len(all_subscriptions)}"
            )

        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error("Критическая ошибка в update_profile", e)
            await message.answer(f"❌ Критическая ошибка: {str(e)}")


async def _create_key_for_server(session_methods, user_id: int, server) -> int:
    """
    Создает ключ для пользователя на конкретном сервере.

    Args:
        session_methods: методы для работы с БД
        user_id: ID пользователя
        server: объект сервера

    Returns:
        int: ID созданного ключа в БД или None при ошибке
    """
    try:
        # ✅ Создаем ключ через BaseKeyManager
        key_manager = BaseKeyManager(server.server_ip)

        client_uuid, email, vless_link = await key_manager.add_client_to_inbound(
            tg_id=str(user_id),
            server_name=server.name
        )

        if client_uuid is None or vless_link is False:
            await logger.log_error(f"Не удалось создать клиента на сервере {server.server_ip}", None)
            return 0

        # ✅ Сохраняем в БД
        key = await session_methods.keys.add_key(
            Keys(
                key_id=client_uuid,  # UUID клиента от X-UI
                key=vless_link,  # VLESS ссылка
                server_ip=server.server_ip,
                email=email,
                name_app=NameApp.VLESS,
                status='active'
            )
        )

        if key and hasattr(key, 'id'):
            await logger.info(f"✅ Создан ключ ID {key.id} для пользователя {user_id} на {server.server_ip}")
            return key.id  # Возвращаем INTEGER ID из БД

        return 0

    except Exception as e:
        await logger.log_error(f"Ошибка создания ключа для пользователя {user_id} на сервере {server.server_ip}", e)
        return 0