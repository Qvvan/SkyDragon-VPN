import html
import logging
import traceback
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config_data import config


class CustomLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(levelname)s - %(asctime)s - %(name)s - %(funcName)s - line: %(lineno)d - %(message)s"
        ))
        self.logger.addHandler(console_handler)

        # Обработчик для файла
        file_handler = logging.FileHandler("app.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(levelname)s - %(asctime)s - %(name)s - %(funcName)s - line: %(lineno)d - %(message)s"
        ))
        self.logger.addHandler(file_handler)

    @staticmethod
    async def notify_group(message: str, error: Exception = None, warning: bool = False, keyboard=None):
        """
        Оповещение в соответствующую группу (ошибки, предупреждения или информация).
        """
        if error:
            group_id = config.ERROR_GROUP_ID
            notification_type = "🚨 <b>Ошибка:</b>\n"
            error_message = f"<pre>{html.escape(traceback.format_exc())}</pre>"
        elif warning:
            group_id = config.ERROR_GROUP_ID or config.INFO_GROUP_ID  # Создайте WARNING_GROUP_ID в конфиге
            notification_type = "⚠️ <b>Предупреждение:</b>\n"
            error_message = ""
        else:
            group_id = config.INFO_GROUP_ID
            notification_type = "ℹ️ <b>Информация:</b>\n"
            error_message = ""

        escaped_message = html.escape(message)
        async with Bot(
                token=config.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            await bot.send_message(
                chat_id=group_id,
                text=f"{notification_type}{escaped_message}{error_message}",
                reply_markup=keyboard
            )

    async def log_info(self, message: str, keyboard=None):
        """Логгирование информации и отправка уведомления."""
        self.logger.info(message)
        await self.notify_group(message, keyboard)

    async def log_error(self, message: str, error: Exception, keyboard=None):
        """Логгирование ошибки и отправка уведомления."""
        full_message = f"{message}. Error: {str(error)}"
        self.logger.error(full_message, exc_info=True)
        await self.notify_group(message, error=error, keyboard=keyboard)

    async def warning(self, message: str, keyboard=None):
        """Логгирование предупреждения и отправка уведомления."""
        self.logger.warning(message)
        await self.notify_group(message, warning=True, keyboard=keyboard)

    async def info(self, message):
        self.logger.info(message)

    async def error(self, message: str, error):
        full_message = f"{message}. Error: {str(error)}"
        self.logger.error(full_message, exc_info=True)


# Экземпляр логгера для использования в других модулях
logger = CustomLogger(__name__)
