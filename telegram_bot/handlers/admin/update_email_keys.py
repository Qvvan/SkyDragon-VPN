from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
import time

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger

router = Router()


@router.message(Command(commands="update_keys"), IsAdmin(ADMIN_IDS))
async def show_servers_handler(message: types.Message):
    start_time = time.time()
    await message.answer(text="Начинаю обновление ключей")
    async with DatabaseContextManager() as session:
        total = 0
        update_total = 0
        no_change_total = 0
        missing_total = 0
        error_total = 0
        servers = await session.servers.get_all_servers()

        for server in servers:
            if server.hidden == 1:
                continue
            await logger.log_info(f"Начинаем проверку сервера: {server.server_ip}")
            try:
                keys_response = await BaseKeyManager(server_ip=server.server_ip).get_inbounds()
                keys = keys_response.get("obj", [])

                if not isinstance(keys, list) or not keys:
                    await logger.log_info(f"Нет ключей на сервере: {server.server_ip}")
                    continue

                await logger.log_info(f"Ключей найдено: {len(keys)}")
                total += len(keys)

                server_updates = 0
                server_no_change = 0
                server_missing = 0
                server_errors = 0

                for key in keys:
                    try:
                        # Проверяем, есть ли clientStats и не пустой ли он
                        client_stats = key.get("clientStats", [])
                        if not client_stats or not isinstance(client_stats, list):
                            continue

                        key_id = key.get("id")
                        if not key_id:
                            continue

                        # Получаем email из первого элемента clientStats
                        email = client_stats[0].get("email", "")
                        if not email:
                            continue

                        async with DatabaseContextManager() as session_methods:
                            # Получаем запись ключа из БД по key_id
                            key_record = await session_methods.keys.get_key_by_key_id(key_id)

                            if key_record:
                                # Проверяем, изменился ли email
                                if key_record.email != email:
                                    # Обновляем по id, а не по key_id!
                                    await session_methods.keys.update_key(key_record.id, email=email)
                                    await session_methods.session.commit()
                                    server_updates += 1
                                else:
                                    # Email не изменился, пропускаем
                                    server_no_change += 1
                            else:
                                # Ключа нет в базе
                                server_missing += 1
                                await logger.warning(f"Ключа нет в базе данных {key_id}, сервер: {server.server_ip}")

                    except Exception as e:
                        server_errors += 1
                        await logger.warning(f"Ошибка при обработке ключа {key_id}: {str(e)}")

                    # Небольшая задержка между запросами для снижения нагрузки
                    await asyncio.sleep(0.01)

                update_total += server_updates
                no_change_total += server_no_change
                missing_total += server_missing
                error_total += server_errors

                await logger.log_info(f"Сервер {server.server_ip}: из {len(keys)} ключей обновлено {server_updates}, " +
                                      f"без изменений {server_no_change}, отсутствует в БД {server_missing}, ошибок {server_errors}")

            except Exception as e:
                await logger.warning(f"Ошибка при обработке сервера {server.server_ip}: {str(e)}")

        execution_time = time.time() - start_time

        # Итоговый отчет
        await logger.log_info(f"Закончили обновление ключей:")
        await logger.log_info(f"Всего ключей найдено: {total}")
        await logger.log_info(f"Обновлено: {update_total}")
        await logger.log_info(f"Без изменений: {no_change_total}")
        await logger.log_info(f"Отсутствует в БД: {missing_total}")
        await logger.log_info(f"Ошибок: {error_total}")
        await logger.log_info(f"Время выполнения: {execution_time:.2f} секунд")

        await message.answer(
            f"Обновление ключей завершено.\n" +
            f"Всего ключей найдено: {total}\n" +
            f"Обновлено: {update_total}\n" +
            f"Без изменений: {no_change_total}\n" +
            f"Отсутствует в БД: {missing_total}\n" +
            f"Ошибок: {error_total}\n" +
            f"Время выполнения: {execution_time:.2f} секунд"
        )