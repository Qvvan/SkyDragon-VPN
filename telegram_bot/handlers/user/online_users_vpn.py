import aiohttp
from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import PORT_X_UI
from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
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
                try:
                    base = BaseKeyManager(server.server_ip)
                    data = await base.get_online_users()

                    if data and data.get('success'):
                        users = data.get('obj', {})
                        answer += f"\n{server.name}: {len(users) if users else 0} человек"
                    else:
                        answer += f"\n{server.name}: Ошибка получения данных"

                except Exception as e:
                    answer += f"\n{server.name}: Ошибка соединения"
                    await logger.log_error(f"Ошибка соединения с сервером {server.name}", e)

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


@router.callback_query(lambda c: c.data == 'online')
async def callback_get_support(callback: CallbackQuery):
    await callback.answer()
    async with DatabaseContextManager() as session_methods:
        try:
            servers = await session_methods.servers.get_all_servers()
            answer = "Сейчас онлайн на серверах\n"

            async with aiohttp.ClientSession() as session:
                for server in servers:
                    try:
                        url = f"https://{server.server_ip}:{PORT_X_UI}/0PkmGmepRhDqrFJ/panel/inbound/onlines"
                        base = BaseKeyManager(server.server_ip)
                        cookies = await base._get_ssh_session_cookie()

                        if not cookies:
                            answer += f"\n{server.name}: Не удалось получить данные авторизации"
                            continue

                        async with session.post(url=url, cookies=cookies, timeout=10, ssl=False) as response:
                            if response.status == 200:
                                data = await response.json()
                                users = data.get('obj', {})
                                answer += f"\n{server.name}: {len(users) if users else 0} человек"
                            else:
                                answer += f"\n{server.name}: Ошибка {response.status}"
                    except aiohttp.ClientError as e:
                        answer += f"\n{server.name}: Ошибка соединения"
                        await logger.log_error(f"Ошибка соединения с сервером {server.name}", e)
                    except Exception as e:
                        answer += f"\n{server.name}: Неизвестная ошибка"
                        await logger.log_error(f"Неизвестная ошибка при обработке сервера {server.name}", e)

            await callback.message.answer(
                text=answer,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🌌 Главное меню",
                                callback_data='main_menu'
                            )
                        ]
                    ]
                )
            )
        except Exception as e:
            await logger.log_error("Ошибки при отправке онлайн пользователей", e)
            await callback.message.answer("Произошла ошибка при получении данных о пользователях онлайн")
