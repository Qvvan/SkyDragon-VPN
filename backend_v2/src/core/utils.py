import re
import secrets
import uuid as _uuid
from datetime import datetime, timezone, timedelta

from src.core.exceptions import ValidationError

MOSCOW_TZ = timezone(timedelta(hours=3))

def is_valid_uuid(value: str) -> bool:
    """Проверяет, является ли строка валидным UUID."""
    try:
        _uuid.UUID(value)
        return True
    except ValueError:
        return False


def mask_email(email: str) -> str:
    """Маскирует email для безопасного логирования."""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"


def utcnow() -> datetime:
    """Текущее московское время (UTC+3) как naive datetime."""
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def normalize_phone(raw: str) -> str:
    """Привести номер к формату 7XXXXXXXXXX (только цифры, начинается с 7)."""
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValidationError("Некорректный номер телефона")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "7" + digits
    elif not digits.startswith("7") or len(digits) != 11:
        raise ValidationError("Номер должен быть в формате 7XXXXXXXXXX (Россия)")
    return digits


def generate_code() -> str:
    """Генерирует криптографически безопасный токен для email-ссылки."""
    return secrets.token_urlsafe(48)