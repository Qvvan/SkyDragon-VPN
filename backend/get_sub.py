import asyncio
import base64

import aiohttp
from aiohttp import ClientTimeout

from cfg.config import SUB_PORT


class BaseKeyManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        # Создаем сессию один раз при инициализации
        self.timeout = ClientTimeout(
            total=15,  # Уменьшаем общий таймаут
            connect=5,  # Быстрое подключение
            sock_read=10
        )
        # Настройки для повторного использования соединений
        self.connector = aiohttp.TCPConnector(
            limit=100,  # Общий лимит соединений
            limit_per_host=30,  # Лимит на хост
            ttl_dns_cache=300,  # Кеш DNS
            use_dns_cache=True,
            keepalive_timeout=30,  # Keep-alive соединений
            enable_cleanup_closed=True
        )

    async def _get_sub_3x_ui(self, sub_id):
        url = f"https://{self.server_ip}:{SUB_PORT}/sub/{sub_id}"

        try:
            # Используем сессию с коннектором
            async with aiohttp.ClientSession(
                    timeout=self.timeout,
                    connector=self.connector
            ) as session:
                async with session.get(
                        url,
                        ssl=False,
                        headers={
                            'User-Agent': 'FastAPI-Client/1.0',
                            'Accept': '*/*',
                            'Connection': 'keep-alive',
                            'Accept-Encoding': 'gzip, deflate'  # Сжатие
                        }
                ) as response:
                    if response.status == 200:
                        # Убираем дополнительный asyncio.wait_for
                        base64_response = await response.text()
                        try:
                            decoded_configs = base64.b64decode(base64_response).decode('utf-8')
                            return decoded_configs
                        except Exception as decode_error:
                            print(f"Ошибка декодирования base64: {decode_error}")
                            return base64_response
                    else:
                        print(f"HTTP {response.status} для {url}")

        except asyncio.TimeoutError:
            print(f"Таймаут для {url}")
        except Exception as e:
            print(f"Error getting subscription: {e}")

        return None

    async def close(self):
        """Закрытие коннектора"""
        if hasattr(self, 'connector'):
            await self.connector.close()
