from aiogram import Router, Bot, F
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def process_start_command(message: Message, bot: Bot):
    await message.answer(
        text="Я пока не научился понимать человеческую речь, поэтому передал ваше сообщение администратору. 📨😊\n\nВернуться в начало — /start"
    )
    await bot.forward_message(chat_id=323993202, from_chat_id=message.chat.id, message_id=message.message_id)
