from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger

router = Router()


@router.message(Command(commands="update_keys"), IsAdmin(ADMIN_IDS))
async def show_servers_handler(message: types.Message):
    await message.answer(text="начинаю обновление ключей")
    async with DatabaseContextManager() as session:
        servers = await session.servers.get_all_servers()
        for server in servers:
            await logger.log_info(f"Начинаем проверку сервера: {server.server_ip}")
            keys = await BaseKeyManager(server_ip=server.server_ip).get_inbounds()
            keys = keys.get("obj", {})
            await logger.info(keys)
            await logger.log_info(f"ключей найдено: {len(keys)}")
            for key in keys:
                async with DatabaseContextManager() as session_methods:
                    email = key.get("clientStats", {})[0].get("email", "")
                    key_id = key.get("id")
                    if key_id:
                        continue
                    key_exists =  await session_methods.keys.get_key_by_key_id(key_id)
                    if key_exists:
                        await session_methods.keys.update_key(key_id, email=email)
                        await session_methods.session.commit()
                    else:
                        await logger.warning(f"ключа нет в базе данных {key_id}\n"
                                             f"сервер: {server.server_ip}")
