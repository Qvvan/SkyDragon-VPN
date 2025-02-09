from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat

from config_data.config import ADMIN_IDS
from lexicon.lexicon_ru import LEXICON_COMMANDS, LEXICON_COMMANDS_ADMIN


async def set_main_menu(bot: Bot, user_id: int):
    """Настраивает разное меню для админов, операторов и пользователей."""

    if user_id in ADMIN_IDS:
        commands = LEXICON_COMMANDS_ADMIN
    else:
        commands = LEXICON_COMMANDS

    # Устанавливаем команды
    main_menu_commands = [BotCommand(command=cmd, description=desc) for cmd, desc in commands.items()]
    await bot.set_my_commands(main_menu_commands, scope=BotCommandScopeChat(chat_id=user_id))
