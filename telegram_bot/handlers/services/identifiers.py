"""Утилиты для генерации идентификаторов клиентов и подписок"""
import base64
import hashlib
import uuid


def encode_numbers(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
    """
    Кодирует user_id и sub_id в base64 строку с checksum.
    
    Args:
        user_id: ID пользователя Telegram
        sub_id: ID подписки
        secret_key: Секретный ключ для checksum (по умолчанию "my_secret_key")
    
    Returns:
        Закодированная строка в формате base64
    """
    data = f"{user_id},{sub_id}"
    checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]
    combined = f"{data}|{checksum}"
    encoded = base64.b64encode(combined.encode()).decode()
    return encoded


def generate_deterministic_uuid(user_id: int, sub_id: int) -> str:
    """
    Генерирует детерминированный UUID из user_id и sub_id.
    Всегда возвращает одинаковый UUID для одинаковых входных данных.
    
    Args:
        user_id: ID пользователя Telegram
        sub_id: ID подписки
    
    Returns:
        UUID строка (v5, детерминированный)
    """
    unique_string = f"user_{user_id}_sub_{sub_id}"
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    deterministic_uuid = uuid.uuid5(namespace, unique_string)
    return str(deterministic_uuid)
