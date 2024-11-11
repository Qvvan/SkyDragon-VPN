from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from aiogram import types

from handlers.user.replace_app import handle_server_selection
from models.models import NameApp, Subscriptions


@pytest.fixture
def mock_state():
    """Фикстура для создания mock FSMContext."""
    state = MagicMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={"subscription_id": 1})
    state.clear = AsyncMock()
    return state


@pytest.fixture
def callback_server_selection():
    """Фикстура для создания CallbackQuery с нужными данными для 'server_select'."""
    return types.CallbackQuery(
        id="2",
        from_user=types.User(id=1, is_bot=False, first_name="TestUser"),
        message=types.Message(
            message_id=2,
            from_user=types.User(id=1, is_bot=False, first_name="TestUser"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial message"
        ),
        data='{"server_ip": "192.168.1.2", "server_name": "Test Server"}',
        chat_instance="test_instance"
    )


@pytest.mark.asyncio
async def test_handle_server_selection(callback_server_selection, mock_state):
    """Тест для обработчика handle_server_selection."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
            patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text, \
            patch('database.context_manager.DatabaseContextManager', return_value=MagicMock()) as mock_db, \
            patch('handlers.services.get_session_cookies.get_session_cookie',
                  new=AsyncMock()) as mock_get_session_cookie, \
            patch('handlers.services.key_create.ShadowsocksKeyManager', new=AsyncMock()) as mock_shadowsocks, \
            patch('handlers.services.key_create.VlessKeyManager', new=AsyncMock()) as mock_vless_manager, \
            patch('logger.logging_config.logger.log_error', new=AsyncMock()) as mock_log_error:
        # Настройка mock методов
        mock_get_session_cookie.return_value = "session_cookie_mock"
        mock_db.subscription.get_subscription_by_id = AsyncMock(return_value=Subscriptions(
            subscription_id=1,
            key_id=1,
            name_app=NameApp.OUTLINE
        ))

        # Вызов функции
        await handle_server_selection(callback_server_selection, state=mock_state)

        # Проверка вызовов
        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text="🔄 Меняем локацию..."
        )
        mock_log_error.assert_not_called()
