import asyncio
import base64
import ssl

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

    import ssl
    import aiohttp

    class BaseKeyManager:
        def __init__(self, server_ip):
            self.server_ip = server_ip
            self.timeout = ClientTimeout(
                total=8,
                connect=3,
                sock_connect=3,
                sock_read=5
            )

        async def _get_sub_3x_ui(self, sub_id):
            # Полностью отключаем SSL проверку для самописных сертификатов
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=3,
                ttl_dns_cache=60,
                use_dns_cache=True,
                keepalive_timeout=10,
                enable_cleanup_closed=True,
                ssl=ssl_context,  # Используем отключенную SSL проверку
                force_close=True
            )

            url = f"https://{self.server_ip}:{SUB_PORT}/sub/{sub_id}"

            try:
                async with aiohttp.ClientSession(
                        timeout=self.timeout,
                        connector=connector
                ) as session:
                    async with session.get(
                            url,
                            ssl=ssl_context,  # ВАЖНО: передаем SSL context и в get()
                            headers={
                                'User-Agent': 'curl/7.88.1',
                                'Accept': '*/*',
                                'Connection': 'close'
                            }
                    ) as response:
                        if response.status == 200:
                            base64_response = await response.text()
                            try:
                                decoded_configs = base64.b64decode(base64_response).decode('utf-8')
                                return decoded_configs
                            except:
                                return base64_response

            except Exception as e:
                print(f"Ошибка для {self.server_ip}: {type(e).__name__}: {e}")
            finally:
                await connector.close()

            return None
