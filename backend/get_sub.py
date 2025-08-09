import asyncio
import base64

import aiohttp
from aiohttp import ClientTimeout

from cfg.config import SUB_PORT


class BaseKeyManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        # Увеличиваем таймауты значительно
        self.timeout = ClientTimeout(
            total=60,  # Общий таймаут 60 секунд
            connect=15,  # Таймаут подключения 15 секунд
            sock_read=30  # Таймаут чтения 30 секунд
        )

    async def _get_sub_3x_ui(self, sub_id):
        url = f"https://{self.server_ip}:{SUB_PORT}/sub/{sub_id}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                        url,
                        ssl=False,
                        headers={
                            'User-Agent': 'FastAPI-Client/1.0',
                            'Accept': '*/*',
                            'Connection': 'keep-alive'
                        }
                ) as response:
                    if response.status == 200:
                        base64_response = await asyncio.wait_for(
                            response.text(),
                            timeout=30
                        )
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
