from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import ServerDisconnectedError
from environs import Env

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.create_keys import encode_numbers, generate_deterministic_uuid
from handlers.services.key_create import BaseKeyManager

env = Env()
env.read_env()

subs = {}

router = Router()

import asyncio


# @router.message(Command(commands='update_keys'), IsAdmin(ADMIN_IDS))
# async def update_keys(message: Message):
#     async with DatabaseContextManager() as session:
#         servers = await session.servers.get_all_servers()
#         for server in servers:
#             if server.hidden == 1:
#                 continue
#             try:
#                 base = BaseKeyManager(server.server_ip)
#                 for key, value in subs.items():
#                     max_retries = 7
#                     retry_delay = 1
#
#                     for attempt in range(max_retries):
#                         try:
#                             user_id = value['user_id']
#                             sub_id = encode_numbers(user_id, key)
#                             client_id = generate_deterministic_uuid(user_id, key)
#
#                             client_uuid, email, url_config = await base.add_client_to_inbound(
#                                 tg_id=str(user_id),
#                                 server_name=server.name,
#                                 sub_id=sub_id,
#                                 client_id=client_id
#                             )
#                             print(f"Создали ключ для пользователя {user_id} на сервере {server.server_ip}")
#                             break
#
#                         except ServerDisconnectedError as e:
#                             print(f"Ошибка подключения (попытка {attempt + 1}/{max_retries}): {e}")
#                             if attempt < max_retries - 1:
#                                 await asyncio.sleep(retry_delay)
#                                 retry_delay *= 2
#                             else:
#                                 print(f"Не удалось создать ключ для пользователя {user_id} после {max_retries} попыток")
#
#                         except Exception as e:
#                             print(f"Неизвестная ошибка для пользователя {user_id}: {e}")
#                             print(f"Не удалось создать ключ для пользователя {user_id} после {max_retries} попыток")
#                             break
#
#             except Exception as e:
#                 print(f"Ошибка при работе с сервером {server.server_ip}: {e}")
