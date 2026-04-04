import sys
from contextvars import ContextVar
from typing import Any

from loguru import logger

request_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class AppLogger:
    DEFAULT_LOG_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<yellow>request_id={extra[request_id]}</yellow> | "
        "<level>{message}</level> | "
        "<blue>{extra[fields]}</blue>"
    )

    def __init__(
            self,
            level: str = "DEBUG",
            log_format: str = DEFAULT_LOG_FORMAT,
            colorize: bool = True,
            log_file: str | None = None,
    ):
        self.level = level
        self.log_format = log_format
        self.colorize = colorize
        self.log_file = log_file
        self._configure_logger()

    def _configure_logger(self) -> None:
        """Настраиваем loguru с контекстными полями"""
        logger.remove()

        # Настраиваем консольный вывод
        logger.add(
            sys.stdout,
            level=self.level,
            format=self.log_format,
            colorize=self.colorize,
            backtrace=True,
            diagnose=True,
            filter=self._add_context_filter,
        )

    @staticmethod
    def _add_context_filter(record: dict[str, Any]) -> bool:
        """Добавляем контекстные поля в каждую запись (Loguru передаёт record как dict-подобный объект)."""
        request_id = request_context.get() or "no-request"
        record["extra"]["request_id"] = request_id

        if "fields" not in record["extra"]:
            record["extra"]["fields"] = ""

        return True

    @staticmethod
    def set_request_id(request_id: str) -> None:
        """Устанавливаем request_id в контекст"""
        request_context.set(request_id)

    @staticmethod
    def clear_request_id() -> None:
        """Очищаем request_id из контекста"""
        request_context.set(None)

    def info(self, message: str, **fields) -> None:
        """Структурированное info логирование"""
        self._log_with_fields("INFO", message, **fields)

    def error(self, message: str, **fields) -> None:
        """Структурированное error логирование"""
        self._log_with_fields("ERROR", message, **fields)

    def warning(self, message: str, **fields) -> None:
        """Структурированное warning логирование"""
        self._log_with_fields("WARNING", message, **fields)

    def debug(self, message: str, **fields) -> None:
        """Структурированное debug логирование"""
        self._log_with_fields("DEBUG", message, **fields)

    @staticmethod
    def _format_fields(fields: dict) -> str:
        return " ".join(f"{k}={v}" for k, v in fields.items()) if fields else ""

    def exception(self, message: str, exc: BaseException | None = None, **fields) -> None:
        """Логирует ошибку вместе с полным traceback исключения."""
        bound_logger = logger.bind(fields=self._format_fields(fields), **fields)
        bound_logger.opt(exception=exc).error(message)

    def _log_with_fields(self, level: str, message: str, **fields) -> None:
        """Внутренний метод для логирования с полями"""
        bound_logger = logger.bind(fields=self._format_fields(fields), **fields)
        getattr(bound_logger, level.lower())(message)
