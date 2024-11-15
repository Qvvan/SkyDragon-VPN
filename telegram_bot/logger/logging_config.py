import logging
import traceback
from logging.handlers import RotatingFileHandler

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_data import config


class CustomLogger:
    def __init__(self, name: str, log_file: str = "bot.log", max_file_size: int = 5 * 1024 * 1024, backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Логгируем все, включая DEBUG

        # Формат логов
        log_format = logging.Formatter(
            "%(levelname)s - %(asctime)s - [%(name)s] - [%(module)s.%(funcName)s] - line: %(lineno)d - %(message)s"
        )

        # Вывод логов в файл с ротацией
        file_handler = RotatingFileHandler(log_file, maxBytes=max_file_size, backupCount=backup_count)
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)

        # Вывод логов в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)

        # Добавляем хендлеры к логгеру
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @staticmethod
    async def notify_group(message: str, error: Exception = None, keyboard=None):
        """Оповещение в соответствующую группу (ошибки или информация)."""
        group_id = config.ERROR_GROUP_ID if error else config.INFO_GROUP_ID
        notification_type = "🚨 Ошибка:\n" if error else "ℹ️ Информация:\n"

        # Формируем сообщение об ошибке
        error_message = ""
        if error:
            error_message = f"\n\nОшибка: {str(error)}\n" \
                            f"Трассировка:\n<pre>{traceback.format_exc()}</pre>"

        async with Bot(
                token=config.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            await bot.send_message(
                chat_id=group_id,
                text=f"{notification_type}{message}{error_message}",
                reply_markup=keyboard
            )

    async def log_debug(self, message: str):
        """Логгирование отладочной информации."""
        self.logger.debug(message, stacklevel=3)

    async def log_info(self, message: str):
        """Логгирование информации и отправка уведомления."""
        self.logger.info(message, stacklevel=3)
        await self.notify_group(message)

    async def log_warning(self, message: str):
        """Логгирование предупреждений."""
        self.logger.warning(message, stacklevel=3)

    async def log_error(self, message: str, error: Exception, keyboard=None):
        """Логгирование ошибки и отправка уведомления."""
        full_message = f"{message}. Error: {str(error)}"
        self.logger.error(full_message, exc_info=True, stacklevel=3)
        await self.notify_group(message, error, keyboard)

    async def log_critical(self, message: str, error: Exception, keyboard=None):
        """Логгирование критической ошибки и отправка уведомления."""
        full_message = f"{message}. Critical Error: {str(error)}"
        self.logger.critical(full_message, exc_info=True, stacklevel=3)
        await self.notify_group(message, error, keyboard)


# Экземпляр логгера
logger = CustomLogger(__name__)
