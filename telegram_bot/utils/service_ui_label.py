"""Подписи тарифов для UI (кнопки, сообщения): только срок и цена из БД, без имён услуг."""


def _days_word(days: int) -> str:
    n = int(days)
    if n % 10 == 1 and n % 100 != 11:
        return "день"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return "дня"
    return "дней"


def _format_price(price) -> str:
    try:
        x = float(price)
        if x == int(x):
            return str(int(x))
        return f"{x:g}"
    except (TypeError, ValueError):
        return str(price)


def service_keyboard_label(duration_days: int, price) -> str:
    """Одна строка: «30 дней — 100 ₽»."""
    days = int(duration_days)
    return f"{days} {_days_word(days)} — {_format_price(price)} ₽"
