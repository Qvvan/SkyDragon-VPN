import pytest
from aiogram import types
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.user.start import process_start_command, handle_know_more
from lexicon.lexicon_ru import LEXICON_RU
from keyboards.kb_inline import InlineKeyboards
from models.models import Users


@pytest.fixture
def start_message():
    """Фикстура для создания тестового сообщения с командой /start."""
    return types.Message(
        message_id=1,
        from_user=types.User(id=1, is_bot=False, first_name="Test", username="test_user"),
        chat=types.Chat(id=1, type="private"),
        date="2024-01-01",
        text="/start",
    )


@pytest.mark.asyncio
async def test_process_start_command(start_message):
    """Тест для команды /start."""
    with patch('aiogram.types.Message.answer', new=AsyncMock()) as mock_answer, \
            patch('database.context_manager.DatabaseContextManager.__aenter__',
                  return_value=MagicMock()) as mock_db_context_manager, \
            patch('logger.logging_config.logger.log_info', new=AsyncMock()) as mock_log_info:
        # Настраиваем session и методы базы данных в контексте mock_db_context_manager
        mock_session = MagicMock()
        mock_db_context_manager.return_value.session = mock_session
        mock_db_context_manager.return_value.users.add_user = AsyncMock(return_value=True)
        mock_session.commit = AsyncMock()

        # Вызываем функцию обработчика напрямую
        await process_start_command(start_message)

        # Проверяем вызовы методов
        mock_answer.assert_called_once_with(
            text=LEXICON_RU['start'],
            reply_markup=await InlineKeyboards.show_start_menu()
        )

        mock_db_context_manager.return_value.users.add_user.assert_called_once_with(Users(
            user_id=start_message.from_user.id,
            username=start_message.from_user.username
        ))

        mock_session.commit.assert_called_once()
        mock_log_info.assert_called_once_with(
            f"К нам присоединился:\n"
            f"Имя: @{start_message.from_user.username}\n"
            f"id: {start_message.from_user.id}"
        )
