import unittest
from unittest.mock import Mock, patch

from aiogram.fsm.context import FSMContext

from telegram_bot.handlers.user.replace_app import handle_server_selection


class TestHandleServerSelection(unittest.IsolatedAsyncioTestCase):
    @patch('telegram_bot.handlers.user.replace_app.get_session_cookie')
    @patch('telegram_bot.handlers.user.replace_app.VlessKeyManager')
    @patch('telegram_bot.handlers.user.replace_app.ShadowsocksKeyManager')
    async def test_successful_app_replacement_outline(self, mock_shadowsocks_manager, mock_vless_manager,
                                                      mock_get_session_cookie):
        # Mock dependencies
        mock_get_session_cookie.return_value = 'session_cookie'
        mock_vless_manager.return_value.manage_vless_key.return_value = ('key', 'key_id')
        mock_vless_manager.return_value.delete_key.return_value = None

        # Create mock callback query and state
        callback_query = Mock()
        callback_query.from_user.id = 123
        callback_query.from_user.username = 'test_user'
        state = FSMContext()
        state_data = {'subscription_id': 1}
        await state.update_data(state_data)

        # Call the function
        await handle_server_selection(callback_query, state)

        # Assert expected behavior
        mock_get_session_cookie.assert_called_once_with('server_ip')
        mock_vless_manager.assert_called_once_with('server_ip', 'session_cookie')
        mock_vless_manager.return_value.manage_vless_key.assert_called_once_with(tg_id='123', username='test_user')
        mock_vless_manager.return_value.delete_key.assert_called_once_with('old_key_id')
        callback_query.message.edit_text.assert_called_once_with(
            text='Приложение успешно изменено на VLESS.\n🔑 Новый ключ:\n<pre>key</pre>', parse_mode='HTML')

    @patch('telegram_bot.handlers.user.replace_app.get_session_cookie')
    @patch('telegram_bot.handlers.user.replace_app.VlessKeyManager')
    @patch('telegram_bot.handlers.user.replace_app.ShadowsocksKeyManager')
    async def test_successful_app_replacement_vless(self, mock_shadowsocks_manager, mock_vless_manager,
                                                    mock_get_session_cookie):
        # Mock dependencies
        mock_get_session_cookie.return_value = 'session_cookie'
        mock_shadowsocks_manager.return_value.manage_shadowsocks_key.return_value = ('key', 'key_id')
        mock_shadowsocks_manager.return_value.delete_key.return_value = None

        # Create mock callback query and state
        callback_query = Mock()
        callback_query.from_user.id = 123
        callback_query.from_user.username = 'test_user'
        state = FSMContext()
        state_data = {'subscription_id': 1}
        await state.update_data(state_data)

        # Call the function
        await handle_server_selection(callback_query, state)

        # Assert expected behavior
        mock_get_session_cookie.assert_called_once_with('server_ip')
        mock_shadowsocks_manager.assert_called_once_with('server_ip', 'session_cookie')
        mock_shadowsocks_manager.return_value.manage_shadowsocks_key.assert_called_once_with(tg_id='123',
                                                                                             username='test_user')
        mock_shadowsocks_manager.return_value.delete_key.assert_called_once_with('old_key_id')
        callback_query.message.edit_text.assert_called_once_with(
            text='Приложение успешно изменено на OUTLINE.\n🔑 Новый ключ:\n<pre>key</pre>', parse_mode='HTML')

    @patch('telegram_bot.handlers.user.replace_app.get_session_cookie')
    async def test_server_unavailable_error(self, mock_get_session_cookie):
        # Mock dependencies
        mock_get_session_cookie.return_value = None

        # Create mock callback query and state
        callback_query = Mock()
        callback_query.from_user.id = 123
        callback_query.from_user.username = 'test_user'
        state = FSMContext()
        state_data = {'subscription_id': 1}
        await state.update_data(state_data)

        # Call the function
        await handle_server_selection(callback_query, state)

        # Assert expected behavior
        mock_get_session_cookie.assert_called_once_with('server_ip')
        callback_query.answer.assert_called_once_with('Выберите другой сервер, этот пока что недоступен.',
                                                      show_alert=True)
        callback_query.message.delete.assert_called_once()

    @patch('telegram_bot.handlers.user.replace_app.get_session_cookie')
    async def test_general_exception_error(self, mock_get_session_cookie):
        # Mock dependencies
        mock_get
