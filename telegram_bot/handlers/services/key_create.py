import asyncio
import json
import random
import secrets
import string
import uuid

import aiohttp

from config_data.config import MY_SECRET_URL, LOGIN_X_UI_PANEL, PASSWORD_X_UI_PANEL
from logger.logging_config import logger
from .ssh_tunnel_manager import SSHTunnelManager

LIMIT = 1
PORT = 443
cookies_store = {}


class ServerUnavailableError(Exception):
    """Кастомное исключение для недоступного сервера."""
    pass


class BaseKeyManager:
    """SSH версия BaseKeyManager - только нужные методы"""

    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.tunnel_manager = SSHTunnelManager()

    async def _get_ssh_session_cookie(self):
        """
        Адаптирует get_session_cookie для работы через SSH туннель
        """

        ssh_key = f"ssh_{self.server_ip}"
        if ssh_key in cookies_store:
            if await self._make_ssh_request_with_cookies():
                return cookies_store[ssh_key]

        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            return None

        # Логинимся через туннель
        url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/login"
        payload = {
            "username": LOGIN_X_UI_PANEL,
            "password": PASSWORD_X_UI_PANEL
        }
        timeout = aiohttp.ClientTimeout(connect=2, total=5)

        for attempt in range(2):
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.post(url, data=payload, ssl=False) as response:
                        if response.status == 200:
                            cookies = response.cookies
                            cookies_store[ssh_key] = cookies  # Сохраняем с SSH префиксом
                            await logger.info(f"SSH cookies получены для {self.server_ip}")
                            return cookies
            except asyncio.TimeoutError:
                await logger.info(f"SSH timeout для {self.server_ip}. Повтор...")
            except aiohttp.ClientError as e:
                await logger.info(f"SSH ошибка запроса для {self.server_ip}: {e}")

            if attempt < 1:
                await asyncio.sleep(1)

        await logger.log_error(f"SSH ошибка получения cookies для {self.server_ip}", None)
        return None

    async def _make_ssh_request_with_cookies(self):
        """
        Адаптирует make_request_with_cookies для работы через SSH туннель
        """
        ssh_key = f"ssh_{self.server_ip}"
        cookies = cookies_store.get(ssh_key)
        if not cookies:
            return False

        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            return False

        url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/"
        timeout = aiohttp.ClientTimeout(connect=2, total=5)

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(url, cookies=cookies, ssl=False) as response:
                    return response.status == 200
        except Exception as e:
            await logger.info(f"SSH ошибка проверки cookies для {self.server_ip}: {e}")
            return False

    @staticmethod
    def generate_uuid():
        """Генерирует UUID для клиентов."""
        return str(uuid.uuid4())

    def generate_short_ids(self, count=8):
        """Генерирует массив shortIds в hex формате разной длины."""
        short_ids = []
        possible_lengths = [2, 4, 6, 8, 10, 12, 14, 16]
        for _ in range(count):
            length = random.choice(possible_lengths)
            short_id = secrets.token_hex(length // 2)
            short_ids.append(short_id)
        return short_ids

    def generate_short_id(self, length=8):
        """Генерирует короткий идентификатор из букв и цифр для email."""
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    async def get_certificate(self):
        """Получает X25519 сертификат для Reality протокола через SSH туннель."""
        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

        get_cert_api_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/server/getNewX25519Cert"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                cookies = await self._get_ssh_session_cookie()
                if not cookies:
                    await asyncio.sleep(1)
                    continue

                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(get_cert_api_url, cookies=cookies, ssl=False) as response:
                        if response.status == 200:
                            cert_data = await response.json()
                            if cert_data.get("success"):
                                await logger.info(f"SSH сертификат получен для {self.server_ip}")
                                return cert_data["obj"]

                await logger.warning(
                    f"SSH попытка получения сертификата {attempt + 1}/{max_retries} для {self.server_ip}")
                await asyncio.sleep(1)

            except Exception as e:
                await logger.log_error(
                    f"SSH ошибка получения сертификата (попытка {attempt + 1}/{max_retries}) для {self.server_ip}", e)
                await asyncio.sleep(1)

        raise ServerUnavailableError(
            f"SSH не удалось получить сертификат после {max_retries} попыток для {self.server_ip}")

    async def get_inbounds(self):
        """Получает список всех инбаундов через SSH туннель."""
        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

        list_api_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/inbound/list"
        cookies = await self._get_ssh_session_cookie()
        if not cookies:
            raise ServerUnavailableError(f"SSH cookies недоступны для {self.server_ip}")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(list_api_url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_inbound_by_id(self, inbound_id):
        """Получает данные инбаунда по ID через SSH туннель."""
        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

        get_inbound_api_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/api/inbounds/get/{inbound_id}"
        cookies = await self._get_ssh_session_cookie()
        if not cookies:
            raise ServerUnavailableError(f"SSH cookies недоступны для {self.server_ip}")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(get_inbound_api_url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_online_users(self):
        """Получает список онлайн пользователей через SSH туннель."""
        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

        url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/inbound/onlines"
        cookies = await self._get_ssh_session_cookie()
        if not cookies:
            raise ServerUnavailableError(f"SSH cookies недоступны для {self.server_ip}")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_or_create_port_443_inbound(self):
        """Получает инбаунд с портом 443, создает если не существует через SSH туннель."""
        # Ищем существующий инбаунд с портом 443
        try:
            inbounds_data = await self.get_inbounds()
            if inbounds_data and inbounds_data.get("success"):
                for inbound in inbounds_data.get("obj", []):
                    if inbound.get("port") == PORT:
                        await logger.info(
                            f"SSH найден существующий inbound с портом 443 для {self.server_ip}, ID: {inbound['id']}")
                        return inbound
        except Exception as e:
            await logger.log_error(f"SSH ошибка проверки существующих inbounds для {self.server_ip}", e)

        # Создаем новый инбаунд с портом 443
        await logger.info(f"SSH создание нового inbound с портом 443 для {self.server_ip}")

        cert_data = await self.get_certificate()
        generated_short_ids = self.generate_short_ids()

        inbound_data = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": "SkyDragon",
            "enable": True,
            "expiryTime": 0,
            "listen": self.server_ip,
            "port": PORT,
            "protocol": "vless",
            "settings": json.dumps({
                "clients": [],
                "decryption": "none",
                "fallbacks": []
            }),
            "streamSettings": json.dumps({
                "network": "tcp",
                "security": "reality",
                "externalProxy": [],
                "realitySettings": {
                    "show": False,
                    "xver": 0,
                    "dest": "github.com:443",
                    "serverNames": ["github.com", "www.github.com"],
                    "privateKey": cert_data["privateKey"],
                    "minClientVer": "",
                    "maxClientVer": "",
                    "maxTimediff": 0,
                    "shortIds": generated_short_ids,
                    "mldsa65Seed": "",
                    "settings": {
                        "publicKey": cert_data["publicKey"],
                        "fingerprint": "chrome",
                        "serverName": "",
                        "spiderX": "",
                        "mldsa65Verify": ""
                    }
                },
                "tcpSettings": {
                    "acceptProxyProtocol": False,
                    "header": {
                        "type": "none"
                    }
                }
            }),
            "sniffing": json.dumps({
                "enabled": False,
                "destOverride": ["http", "tls", "quic", "fakedns"],
                "metadataOnly": False,
                "routeOnly": False
            }),
            "allocate": json.dumps({
                "strategy": "always",
                "refresh": 5,
                "concurrency": 3
            })
        }

        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

        create_api_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/inbound/add"
        cookies = await self._get_ssh_session_cookie()
        if not cookies:
            raise ServerUnavailableError(f"SSH cookies недоступны для {self.server_ip}")

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(create_api_url, cookies=cookies, json=inbound_data, ssl=False) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        await logger.info(
                            f"SSH успешно создан inbound с портом 443 для {self.server_ip}, ID: {response_data['obj']['id']}")
                        return response_data["obj"]
                    else:
                        raise Exception(f"SSH API Error: {response_data.get('msg', 'Unknown error')}")
                elif response.status == 400:
                    error_text = await response.text()
                    if "port already in use" in error_text.lower():
                        await asyncio.sleep(1)
                        inbounds_data = await self.get_inbounds()
                        if inbounds_data and inbounds_data.get("success"):
                            for inbound in inbounds_data.get("obj", []):
                                if inbound.get("port") == PORT:
                                    return inbound
                        raise Exception("SSH порт 443 занят но inbound не найден")
                    else:
                        raise Exception(f"SSH Bad request: {error_text}")
                else:
                    error_text = await response.text()
                    raise Exception(f"SSH HTTP Error {response.status}: {error_text}")

    async def add_client_to_inbound(self, tg_id: str, server_name: str, sub_id: str, client_id: str):
        """Добавляет нового клиента в существующий инбаунд через SSH туннель."""

        new_client = {
            "id": client_id,
            "flow": "xtls-rprx-vision",
            "email": sub_id,
            "limitIp": LIMIT,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
            "tgId": str(tg_id),
            "subId": sub_id,
            "comment": f"TgID: {tg_id}",
            "reset": 0
        }

        main_inbound = await self.get_or_create_port_443_inbound()
        inbound_id = main_inbound["id"]

        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [new_client]
            })
        }

        tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
        if not tunnel_port:
            return None, None, False

        add_client_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/inbound/addClient"
        cookies = await self._get_ssh_session_cookie()
        if not cookies:
            return None, None, False

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(add_client_url, cookies=cookies, json=payload, ssl=False) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        await logger.info(
                            f"SSH клиент {client_id} успешно добавлен в inbound {inbound_id} на {self.server_ip}")
                        return sub_id, client_id, True
                    else:
                        await logger.log_error(f"SSH API Error при добавлении клиента на {self.server_ip}",
                                               response_data.get('msg', 'Unknown error'))
                        return None, None, False
                else:
                    error_text = await response.text()
                    await logger.log_error(f"SSH ошибка добавления клиента на {self.server_ip}: {response.status}",
                                           error_text)
                    return None, None, False

    async def update_key_enable(self, user_id, sub_id: str, status: bool, client_id: str):
        """Обновляет статус ключа (включен/выключен) через SSH туннель."""
        try:
            tunnel_port = await self.tunnel_manager.get_tunnel_port(self.server_ip)
            if not tunnel_port:
                raise ServerUnavailableError(f"SSH туннель недоступен для {self.server_ip}")

            main_inbound = await self.get_or_create_port_443_inbound()
            inbound_id = main_inbound["id"]

            payload = {
                "id": inbound_id,
                "settings": json.dumps({
                    "clients": [{
                        "id": client_id,
                        "flow": "xtls-rprx-vision",
                        "email": sub_id,
                        "limitIp": LIMIT,
                        "totalGB": 0,
                        "expiryTime": 0,
                        "enable": status,
                        "tgId": str(user_id),
                        "subId": str(sub_id),
                        "comment": f"TgID: {user_id}",
                        "reset": 0
                    }]
                })
            }

            update_url = f"https://localhost:{tunnel_port}/{MY_SECRET_URL}/panel/inbound/updateClient/{client_id}"

            cookies = await self._get_ssh_session_cookie()
            if not cookies:
                return False

            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(update_url, cookies=cookies, json=payload, ssl=False) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get("success"):
                            status_text = "включен" if status else "выключен"
                            await logger.info(f"SSH ключ {client_id} успешно {status_text} на {self.server_ip}")
                            return True
                        else:
                            await logger.log_error(
                                f"SSH API Error при обновлении ключа {client_id} на {self.server_ip}",
                                response_data.get('msg', 'Unknown error'))
                            return False
                    else:
                        error_text = await response.text()
                        await logger.log_error(
                            f"SSH ошибка обновления ключа {client_id} на {self.server_ip}: {response.status}",
                            error_text)
                        return False

        except Exception as e:
            await logger.log_error(f"SSH исключение при обновлении ключа {client_id} на {self.server_ip}", e)
            return False
