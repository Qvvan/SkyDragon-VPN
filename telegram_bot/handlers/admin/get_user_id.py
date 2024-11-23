from aiogram import Router, types
from aiogram.filters import Command

from config_data.config import ADMIN_IDS
from filters.admin import IsAdmin
from lexicon.lexicon_ru import LEXICON_COMMANDS_ADMIN

router = Router()


@router.message(Command(commands='user_id'), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message):
    pass
