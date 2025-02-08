from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands=['send_sticker']))
async def send_sticker(message: Message):
    await message.answer_sticker(sticker="CAACAgIAAxkBAAENh-JnjCQaRNV_5iBIdsVeQ5NztQVWEwACZ2QAAvKtwUo-e2J2a0JtWjYE")