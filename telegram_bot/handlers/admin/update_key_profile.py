import base64
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

    def generate_ss_link(self, port, password, method, server_name):
        user_info = f"{method}:{password}".encode()
        user_info_base64 = base64.b64encode(user_info).decode()
        return f"ss://{user_info_base64}@{self.server_ip}:{port}?prefix=POST%20&type=tcp#{server_name} - Shadowsocks"


@router.message(Command(commands="update_vless_keys"), IsAdmin(ADMIN_IDS))
async def update_vless_keys_command(message: Message):
    """Команда для обновления всех VLESS и Shadowsocks ключей на всех серверах."""

    await message.answer("🚀 Запускаю обновление ключей на всех серверах...")

    async with DatabaseContextManager() as session_methods:
        try:
            keys = await session_methods.keys.get_all_keys()
            updated_count = 0

            for key in keys:
                try:
                    async with DatabaseContextManager() as session:
                        server = await session.servers.get_server_by_ip(key.server_ip)
                        get_inbound = await BaseKeyManager(key.server_ip).get_inbound_by_id(key.key_id)

                        if not get_inbound or not get_inbound.get("success") or not get_inbound.get("obj"):
                            await logger.warning(f"Inbound не найден для ключа {key.key_id}")
                            continue

                        inbound_obj = get_inbound["obj"]
                        protocol = inbound_obj.get("protocol")

                        if protocol == "vless":
                            settings_str = inbound_obj.get("settings", "")
                            if not settings_str:
                                continue

                            settings = json.loads(settings_str)
                            if not settings.get("clients"):
                                continue

                            client_id = settings["clients"][0]["id"]

                            stream_settings_str = inbound_obj.get("streamSettings", "")
                            if not stream_settings_str:
                                continue

                            stream_settings = json.loads(stream_settings_str)
                            reality_settings = stream_settings.get("realitySettings", {})

                            if not reality_settings.get("shortIds"):
                                continue

                            short_id = reality_settings["shortIds"][0]
                            reality_inner_settings = reality_settings.get("settings", {})
                            public_key = reality_inner_settings.get("publicKey")

                            if not public_key:
                                continue

                            port = inbound_obj.get("port")
                            if not port:
                                continue

                            updater = VlessKeyUpdater(key.server_ip, server.name)
                            vless_link = updater.generate_vless_link(
                                client_id, port, short_id, public_key, server.name
                            )

                            await session.keys.update_key(key.id, key=vless_link)

                        elif protocol == "shadowsocks":
                            settings_str = inbound_obj.get("settings", "")
                            if not settings_str:
                                continue

                            settings = json.loads(settings_str)
                            password = settings.get("password")
                            method = settings.get("method", "chacha20-ietf-poly1305")

                            if not password:
                                continue

                            port = inbound_obj.get("port")
                            if not port:
                                continue

                            # Генерируем SS ссылку
                            user_info = f"{method}:{password}".encode()
                            user_info_base64 = base64.b64encode(user_info).decode()
                            ss_link = f"ss://{user_info_base64}@{key.server_ip}:{port}#{server.name} - Shadowsocks"

                            await session.keys.update_key(key.id, key=ss_link)

                        else:
                            await logger.info(f"Неизвестный протокол {protocol} для ключа {key.key_id}")
                            continue

                        await session.session.commit()
                        updated_count += 1
                        await logger.info(f"Ключ {key.key_id} ({protocol}) обновлен, в бд ID {key.id}")

                except Exception as e:
                    await logger.error(f"Ошибка обработки ключа {key.key_id}: {e}")
                    continue

            await message.answer(f"✅ Обновление завершено! Обновлено ключей: {updated_count}")

        except Exception as e:
            await logger.error(f"Ошибка обновления ключей: {e}")
            await message.answer(f"❌ Ошибка: {str(e)}")
