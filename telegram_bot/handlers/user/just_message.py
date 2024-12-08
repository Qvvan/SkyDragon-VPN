from aiogram import Router, Bot
from aiogram.types import Message

router = Router()


@router.message()
async def process_start_command(message: Message, bot: Bot):
    await message.answer(
        text="Я еще не научился понимать человечкую речь, поэтому передал ваше сообщение администратору.\n\nВ начало /start",
    )
    await bot.forward_message(chat_id=323993202, from_chat_id=message.chat.id, message_id=message.message_id)
