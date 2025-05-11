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
    async with DatabaseContextManager() as session:
        keys = await session.keys.get_all_keys()
        for key in keys:
            async with DatabaseContextManager() as session_methods:
                try:
                    email = await BaseKeyManager(server_ip=key.server_ip).get_traffic_by_id(key.key_id)
                    email = email["obj"][0]["email"]
                    await session_methods.keys.update_key(key.id, email=email)
                    await session_methods.session.commit()
                except Exception as e:
                    await logger.log_error(f"произошла ошбика при обновление email у ключа ID: {key.key_id}\n"
                                           f"сервер: {key.server_ip}", e)
