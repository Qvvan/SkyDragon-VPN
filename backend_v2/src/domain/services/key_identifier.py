"""
Детерминированные идентификаторы для VPN-ключей.

Одинаковая пара (user_id, sub_id) всегда даёт одинаковый UUID и email —
это гарантирует идемпотентность операций на панели 3x-ui.
"""
import base64
import hashlib
import uuid

_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def client_uuid(user_id: int, sub_id: str) -> str:
    """UUID v5, детерминированный. Используется как client_id в 3x-ui."""
    return str(uuid.uuid5(_NAMESPACE, f"user_{user_id}_sub_{sub_id}"))


def sub_email_prefix(user_id: int, sub_id: str, secret: str = "my_secret_key") -> str:
    """
    Base64-кодированная строка с checksum — общий префикс для email всех портов подписки.
    Соответствует encode_numbers() в telegram_bot.
    """
    data = f"{user_id},{sub_id}"
    checksum = hashlib.sha256((data + secret).encode()).hexdigest()[:8]
    return base64.b64encode(f"{data}|{checksum}".encode()).decode()


def client_email(user_id: int, sub_id: str, port: int, secret: str = "my_secret_key") -> str:
    """Email клиента для конкретного инбаунда: {prefix}_port{port}."""
    return f"{sub_email_prefix(user_id, sub_id, secret)}_port{port}"
