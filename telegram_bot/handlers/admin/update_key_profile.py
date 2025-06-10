import json

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config_data.config import ADMIN_IDS, PORT_X_UI, MY_SECRET_URL
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.key_create import BaseKeyManager
from logger.logging_config import logger
from models.models import NameApp

router = Router()


class VlessKeyUpdater:
    def __init__(self, server_ip: str, server_name: str):
        self.server_ip = server_ip
        self.base_url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/panel"
        self.server_name = server_name

    def generate_vless_link(self, client_id, port, short_id, public_key, server_name):
        """Генерирует правильный VLESS URL."""
        return (f"vless://{client_id}@{self.server_ip}:{port}"
                f"?type=tcp&security=reality&pbk={public_key}"
                f"&fp=chrome&sni=github.com&sid={short_id}&flow=xtls-rprx-vision"
                f"#{server_name} - VLESS")


@router.message(Command(commands="update_vless_keys"), IsAdmin(ADMIN_IDS))
async def update_vless_keys_command(message: Message):
    """Команда для обновления всех VLESS ключей на всех серверах."""

    await message.answer("🚀 Запускаю обновление VLESS ключей на всех серверах...")

    async with DatabaseContextManager() as session_methods:
        try:
            keys = await session_methods.keys.get_all_keys()
            for key in keys:
                try:
                    async with DatabaseContextManager() as session:
                        if "github" in key.key:
                            continue

                        if key.name_app != "Vless":
                            continue

                        await logger.info("Вот такой ключ мы пропустили для обновления: " + key.key)

                        server = await session.servers.get_server_by_ip(key.server_ip)
                        get_inbound = await BaseKeyManager(key.server_ip).get_inbound_by_id(key.key_id)

                        # Проверяем что get_inbound не None и имеет правильную структуру
                        if not get_inbound or not get_inbound.get("success") or not get_inbound.get("obj"):
                            await logger.warning(f"Inbound не найден для ключа {key.key_id}")
                            continue

                        inbound_obj = get_inbound["obj"]
                        if inbound_obj.get("protocol") != "vless":
                            continue

                        # Парсим settings для получения client_id
                        settings_str = inbound_obj.get("settings", "")
                        if not settings_str:
                            await logger.warning(f"Нет settings для ключа {key.key_id}")
                            continue

                        settings = json.loads(settings_str)
                        if not settings.get("clients"):
                            await logger.warning(f"Нет клиентов для ключа {key.key_id}")
                            continue

                        client_id = settings["clients"][0]["id"]

                        # Парсим streamSettings для получения параметров Reality
                        stream_settings_str = inbound_obj.get("streamSettings", "")
                        if not stream_settings_str:
                            await logger.warning(f"Нет streamSettings для ключа {key.key_id}")
                            continue

                        stream_settings = json.loads(stream_settings_str)
                        reality_settings = stream_settings.get("realitySettings", {})

                        if not reality_settings.get("shortIds"):
                            await logger.warning(f"Нет shortIds для ключа {key.key_id}")
                            continue

                        short_id = reality_settings["shortIds"][0]

                        reality_inner_settings = reality_settings.get("settings", {})
                        public_key = reality_inner_settings.get("publicKey")

                        if not public_key:
                            await logger.warning(f"Нет publicKey для ключа {key.key_id}")
                            continue

                        # Получаем порт
                        port = inbound_obj.get("port")
                        if not port:
                            await logger.warning(f"Нет порта для ключа {key.key_id}")
                            continue

                        # Создаем updater и генерируем ссылку
                        updater = VlessKeyUpdater(key.server_ip, server.name)
                        vless_link = updater.generate_vless_link(
                            client_id, port, short_id, public_key, server.name
                        )

                        # Обновляем ключ в базе
                        await session.keys.update_key_by_key_id(key.key_id, key=vless_link)
                        await session.session.commit()

                        await logger.info(f"Ключ {key.key_id} обновлен, в бд ID {key.id}")

                except Exception as e:
                    await logger.error(f"Ошибка обработки ключа {key.key_id}:", e)
                    continue

            await message.answer("✅ Все VLESS ключи обновлены!")

        except Exception as e:
            await logger.error(f"Ошибка обновления ключей:", e)
            await message.answer(f"❌ Ошибка: {str(e)}")
