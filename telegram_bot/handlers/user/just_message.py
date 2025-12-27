from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def process_start_command(message: Message, bot: Bot, state: FSMContext):
    await message.answer(
        text="Я пока не научился понимать человеческую речь, поэтому передал ваше сообщение администратору. 📨😊 Или напишите в техподдержку @SkyDragonSupport\n\nВернуться в начало — /start"
    )
    await bot.forward_message(chat_id=323993202, from_chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(chat_id=323993202, text=f"{message.chat.id}: {message.text}")
