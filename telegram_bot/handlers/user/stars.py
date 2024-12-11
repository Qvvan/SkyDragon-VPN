from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command(commands='stars'))
async def command_start(message: Message):
    await message.answer(text="Данную команду нужно вводить в боте @PremiumBot")
