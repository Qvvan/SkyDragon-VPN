import pytest
from aiogram import types
from unittest.mock import AsyncMock, patch
from handlers.user.support import get_support, handle_low_speed, handle_install_guide, \
    handle_back_to_support_menu, handle_subscribe, handle_vpn_issue  # Импортируем функцию обработчика
from lexicon.lexicon_ru import LEXICON_RU
from keyboards.kb_inline import InlineKeyboards

@pytest.fixture
def test_message():
    """Фикстура для создания тестового сообщения с командой /support."""
    return types.Message(
        message_id=1,
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        chat=types.Chat(id=1, type="private"),
        date="2024-01-01",
        text="/support",
    )

@pytest.mark.asyncio
async def test_support_command(test_message):
    """Тест для команды /support."""
    # Используем patch для подмены метода answer в классе Message
    with patch('aiogram.types.Message.answer', new=AsyncMock()) as mock_answer:
        # Вызываем функцию обработчика напрямую
        await get_support(test_message)

        # Проверяем, что answer был вызван с правильными аргументами
        mock_answer.assert_called_once_with(
            text=LEXICON_RU['support'],
            reply_markup=await InlineKeyboards.get_support()
        )



@pytest.fixture
def callback_vpn_issue():
    """Фикстура для создания CallbackQuery с data 'vpn_issue'."""
    return types.CallbackQuery(
        id="1",
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        message=types.Message(
            message_id=1,
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial text"
        ),
        data="vpn_issue",
        chat_instance="test_instance"
    )

@pytest.mark.asyncio
async def test_handle_vpn_issue(callback_vpn_issue):
    """Тест для обработчика vpn_issue."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
         patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text:

        await handle_vpn_issue(callback_vpn_issue)

        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text=LEXICON_RU['vpn_issue_response'],
            reply_markup=await InlineKeyboards.get_back_button_keyboard()
        )

@pytest.fixture
def callback_low_speed():
    """Фикстура для создания CallbackQuery с data 'low_speed'."""
    return types.CallbackQuery(
        id="2",
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        message=types.Message(
            message_id=2,
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial text"
        ),
        data="low_speed",
        chat_instance="test_instance"
    )

@pytest.mark.asyncio
async def test_handle_low_speed(callback_low_speed):
    """Тест для обработчика low_speed."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
         patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text:

        await handle_low_speed(callback_low_speed)

        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text=LEXICON_RU['low_speed_response'],
            reply_markup=await InlineKeyboards.get_back_button_keyboard()
        )

@pytest.fixture
def callback_install_guide():
    """Фикстура для создания CallbackQuery с data 'install_guide'."""
    return types.CallbackQuery(
        id="3",
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        message=types.Message(
            message_id=3,
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial text"
        ),
        data="install_guide",
        chat_instance="test_instance"
    )

@pytest.mark.asyncio
async def test_handle_install_guide(callback_install_guide):
    """Тест для обработчика install_guide."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
         patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text:

        await handle_install_guide(callback_install_guide)

        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text="Инструкция ⬇️",
            reply_markup=await InlineKeyboards.get_guide('back_to_support_menu')
        )

@pytest.fixture
def callback_back_to_support_menu():
    """Фикстура для создания CallbackQuery с data 'back_to_support_menu'."""
    return types.CallbackQuery(
        id="4",
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        message=types.Message(
            message_id=4,
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial text"
        ),
        data="back_to_support_menu",
        chat_instance="test_instance"
    )

@pytest.mark.asyncio
async def test_handle_back_to_support_menu(callback_back_to_support_menu):
    """Тест для обработчика back_to_support_menu."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
         patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text:

        await handle_back_to_support_menu(callback_back_to_support_menu)

        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text=LEXICON_RU['support'],
            reply_markup=await InlineKeyboards.get_support()
        )

@pytest.fixture
def callback_support_callback():
    """Фикстура для создания CallbackQuery с data 'support_callback'."""
    return types.CallbackQuery(
        id="5",
        from_user=types.User(id=1, is_bot=False, first_name="Test"),
        message=types.Message(
            message_id=5,
            from_user=types.User(id=1, is_bot=False, first_name="Test"),
            chat=types.Chat(id=1, type="private"),
            date="2024-01-01",
            text="Initial text"
        ),
        data="support_callback",
        chat_instance="test_instance"
    )

@pytest.mark.asyncio
async def test_handle_subscribe(callback_support_callback):
    """Тест для обработчика support_callback."""
    with patch('aiogram.types.CallbackQuery.answer', new=AsyncMock()) as mock_answer, \
         patch('aiogram.types.Message.edit_text', new=AsyncMock()) as mock_edit_text:

        await handle_subscribe(callback_support_callback)

        mock_answer.assert_called_once()
        mock_edit_text.assert_called_once_with(
            text=LEXICON_RU['support'],
            reply_markup=await InlineKeyboards.get_support()
        )