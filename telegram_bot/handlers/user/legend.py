from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from lexicon.lexicon_ru import LEXICON_RU

router = Router()


@router.message(Command(commands="legend"))
async def process_start_command(message: Message):
    await message.answer(
        text=LEXICON_RU['legend'],
        parse_mode="Markdown"
    )
