import re
import uuid as _uuid
from datetime import datetime, timezone, timedelta

from core.exceptions import ValidationError

MOSCOW_TZ = timezone(timedelta(hours=3))

def is_valid_uuid(value: str) -> bool:
    """Проверяет, является ли строка валидным UUID."""
    try:
        _uuid.UUID(value)
        return True
    except ValueError:
        return False


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