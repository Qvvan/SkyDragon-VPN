from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

router = Router()


@router.message(Command(commands=['wheel']))
async def spin_wheel(message: Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Запустить колесо", web_app=WebAppInfo(url="https://your-miniapp-url.com")))
    await message.answer("Привет! Крути колесо!", reply_markup=keyboard)
