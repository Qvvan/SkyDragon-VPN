from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger

router = Router()


@router.callback_query(lambda c: c.data == 'online')
async def callback_get_support(callback: CallbackQuery):
    await callback.answer()
    async with DatabaseContextManager() as session_methods:
        try:
            servers = await session_methods.servers.get_all_servers()
            answer = "Сейчас онлайн на серверах\n"

            for server in servers:
                if server.hidden == 1:
                    continue
                try:
                    gateway = PanelGateway(server)
                    data = await gateway.get_online_users()
                    await gateway.close()

                    if data and data.get('success'):
                        users = data.get('obj') or {}
                        count = len(users) if isinstance(users, (list, dict)) else 0
                        answer += f"\n{server.name}: {count} человек"
                    else:
                        answer += f"\n{server.name}: Ошибка получения данных"

                except Exception as e:
                    answer += f"\n{server.name}: Ошибка соединения"
                    await logger.log_error(f"Ошибка соединения с сервером {server.name}, {server.server_ip}", e)

            await callback.message.answer(
                text=answer,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            text="🌌 Главное меню",
                            callback_data='main_menu'
                        )]
                    ]
                )
            )
        except Exception as e:
            await logger.log_error("Ошибки при отправке онлайн пользователей", e)
            await callback.message.answer("Произошла ошибка при получении данных о пользователях онлайн")
