import asyncio
import ssl

import aiohttp

from config_data.config import MY_SECRET_URL, LOGIN_X_UI_PANEL, PASSWORD_X_UI_PANEL, PORT_X_UI
from logger.logging_config import logger


async def get_session_cookie(server_ip: str) -> str | None:
    url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/login"
    payload = {
        "username": LOGIN_X_UI_PANEL,
        "password": PASSWORD_X_UI_PANEL
    }

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with aiohttp.ClientSession() as session:
            for attempt in range(3):
                timeout = 3 + attempt * 2
                try:
                    async with session.post(url, json=payload, ssl=ssl_context, timeout=timeout) as response:
                        if response.status == 200:
                            set_cookie_headers = response.headers.getall("Set-Cookie", [])
                            if not set_cookie_headers:
                                await logger.log_error(
                                    f"Заголовки Set-Cookie отсутствуют в ответе от {server_ip}",
                                    Exception(f"Ответ: {response.headers}"),
                                )
                                return None

                            session_value = next(
                                (header.split("3x-ui=", 1)[1].split(";")[0] for header in set_cookie_headers if "3x-ui" in header),
                                None
                            )
                            if session_value:
                                return session_value
                            else:
                                await logger.log_error(
                                    f"Сессионный ключ 3x-ui не найден в Set-Cookie заголовках от {server_ip}",
                                    Exception(f"Ответ: {response.headers}"),
                                )
                        else:
                            await logger.log_error(
                                f"Неудачный ответ от {server_ip}: статус {response.status}",
                                Exception(f"Текст ответа: {await response.text()}"),
                            )
                    break  # Успешное завершение
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)  # Увеличиваем ожидание
                    else:
                        await logger.log_error(
                            f"Ошибка соединения с {server_ip} после трех попыток",
                            e,
                        )
    except Exception as e:
        await logger.log_error(
            f"Неизвестная ошибка при подключении к {server_ip}",
            e,
        )

    return None

