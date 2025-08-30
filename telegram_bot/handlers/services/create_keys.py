import base64
import hashlib
import uuid

from database.context_manager import DatabaseContextManager
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger


async def create_keys(user_id: int, username: str, sub_id):
    async with DatabaseContextManager() as session_methods:
        try:
            sub_uuid = encode_numbers(user_id, sub_id)
            client_id = generate_deterministic_uuid(user_id, sub_id)
            server_ips = await session_methods.servers.get_all_servers()
            for server in server_ips:
                if server.hidden == 1:
                    continue
                try:
                    base = BaseKeyManager(server.server_ip)
                    client_uuid, email, url_config = await base.add_client_to_inbound(
                        tg_id=str(user_id),
                        sub_id=sub_uuid,
                        client_id=client_id
                    )
                    if client_uuid is None:
                        continue

                except Exception as e:
                    await logger.log_error(f"Ошибка создания ключа на сервер {server.server_ip}", e)
            return True

        except Exception as e:
            await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
            return False


def encode_numbers(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
    data = f"{user_id},{sub_id}"

    checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]

    combined = f"{data}|{checksum}"

    encoded = base64.b64encode(combined.encode()).decode()

    return encoded


def generate_deterministic_uuid(user_id: int, sub_id: int) -> str:
    """
    Генерирует детерминированный UUID из user_id и sub_id
    Всегда возвращает одинаковый UUID для одинаковых входных данных
    """
    # Создаем уникальную строку из user_id и sub_id
    unique_string = f"user_{user_id}_sub_{sub_id}"

    # Используем namespace UUID (можешь создать свой)
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace

    # Генерируем UUID v5 (детерминированный)
    deterministic_uuid = uuid.uuid5(namespace, unique_string)

    return str(deterministic_uuid)