import asyncio
import ssl
import aiohttp
from config_data.config import LOGIN_X_UI_PANEL, MY_SECRET_URL, PASSWORD_X_UI_PANEL, PORT_X_UI
from logger.logging_config import logger


async def get_session_cookie(server_ip: str) -> str | None:
    """
    Получить сессионный ключ от сервера.

    :param server_ip: IP-адрес сервера
    :return: Сессионный ключ или None, если сервер недоступен
    """
    url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/login"
    payload = {
        "username": LOGIN_X_UI_PANEL,
        "password": PASSWORD_X_UI_PANEL
    }

    # Создаем контекст SSL для отключения проверки сертификата
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                # Запрос к серверу
                async with session.post(url, json=payload, ssl=ssl_context, timeout=3) as response:
                    if response.status == 200:
                        # Парсинг заголовка Set-Cookie для извлечения сессионного ключа
                        session_value = parse_session_cookie(response.headers)
                        if session_value:
                            await logger.info(f"Сессионный ключ успешно получен с {server_ip}")
                            return session_value
                        else:
                            await logger.warning(
                                f"Сессионный ключ 3x-ui не найден в заголовках Set-Cookie от {server_ip}."
                            )
                    else:
                        await logger.warning(
                            f"Неудачный ответ от {server_ip}: статус {response.status}. Тело ответа: {await response.text()}"
                        )
                break  # Прекращаем попытки после успешного ответа

            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
                if attempt == 2:  # После 3-й попытки логируем предупреждение
                    await logger.warning(f"Сервер {server_ip} недоступен после трех попыток: {e}")
                else:
                    await asyncio.sleep(1)  # Задержка перед повторной попыткой
            except ssl.SSLError as e:
                # Логируем ошибки SSL
                await logger.log_error(f"Ошибка SSL при подключении к {server_ip}: {e}", e)
                break  # Прекращаем попытки при ошибке SSL
            except ssl.CertificateError as e:
                # Логируем ошибки сертификатов
                await logger.log_error(f"Ошибка сертификата SSL при подключении к {server_ip}: {e}", e)
                break  # Прекращаем попытки при ошибке сертификата
            except Exception as e:
                # Логируем только непредвиденные ошибки
                await logger.log_error(f"Непредвиденная ошибка при подключении к {server_ip} на попытке {attempt + 1}", e)
                break  # Прекращаем попытки при критической ошибке

    return None  # Возвращаем None, если сессия не была получена


def parse_session_cookie(headers) -> str | None:
    """
    Извлечь сессионный ключ из заголовков Set-Cookie.

    :param headers: Заголовки ответа
    :return: Значение сессионного ключа или None
    """
    set_cookie_headers = headers.getall("Set-Cookie", [])
    for header in set_cookie_headers:
        if "3x-ui" in header:
            return header.split("3x-ui=", 1)[1].split(";")[0]
    return None
