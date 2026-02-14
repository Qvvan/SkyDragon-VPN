import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.panel_gateway import PanelGateway
from keyboards.kb_inline import ServerCallbackData
from logger.logging_config import logger

notification_dict = {}

router = Router()


async def ping_servers(bot: Bot):
    while True:
        async with DatabaseContextManager() as session_methods:
            servers = []
            try:
                servers = await session_methods.servers.get_all_servers()
            except Exception as e:
                await logger.log_error("Не удалось взять список серверов, при проверке работоспособности серверов", e)

        for server in servers:
            if server.hidden == 1:
                continue

            # Проверка доступности по HTTPS (лёгкий пинг)
            gateway = PanelGateway(server)
            reachable = await gateway.ping_only()
            await gateway.close()
            if reachable:
                if server.server_ip in notification_dict:
                    del notification_dict[server.server_ip]
            else:
                button = [InlineKeyboardButton(
                    text="Выключить сервер",
                    callback_data=ServerCallbackData(
                        action='disable',
                        server_ip=server.server_ip).pack()
                )]
                keyboard = InlineKeyboardMarkup(inline_keyboard=[button])
                await logger.log_error(
                    message=f'Сервер: {server.server_ip}\n'
                            f'Название: {server.name}',
                    error='⚠️Недоступен ‼',
                    keyboard=keyboard
                )
                if server.server_ip not in notification_dict:
                    notification_dict[server.server_ip] = {}

        current_time = datetime.now()
        for server_ip in list(notification_dict.keys()):
            for user_id in list(notification_dict[server_ip].keys()):
                if current_time - notification_dict[server_ip][user_id] > timedelta(minutes=30):
                    del notification_dict[server_ip][user_id]
            if not notification_dict[server_ip]:
                del notification_dict[server_ip]

        # Проверяем не чаще чем раз в 3 минуты; проверка — только лёгкий пинг без авторизации
        await asyncio.sleep(180)
