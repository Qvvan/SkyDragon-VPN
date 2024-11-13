# from unittest.mock import AsyncMock
#
# import pytest
#
# from handlers.user.start import process_start_command
# from keyboards.kb_inline import InlineKeyboards
# from lexicon.lexicon_ru import LEXICON_RU
#
#
# @pytest.mark.asyncio
# async def test_start_command():
#     message = AsyncMock()
#     message.text = "/start 123"  # Добавляем текст команды с аргументом
#     message.from_user.id = 456  # Задаем значение для message.from_user.id
#     message.from_user.username = "testuser"  # Задаем значение для message.from_user.username
#
#     await process_start_command(message)
#
#     await message.answer.assert_called_with(
#         text=LEXICON_RU['start'],
#         reply_markup=await InlineKeyboards.get_menu_keyboard(),
#         parse_mode="Markdown"
#     )
#
