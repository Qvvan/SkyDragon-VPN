import asyncio
import json
import random
import secrets
import string
import uuid

import aiohttp

from config_data.config import MY_SECRET_URL, PORT_X_UI
from handlers.services.get_session_cookies import get_session_cookie

LIMIT = 2


class ServerUnavailableError(Exception):
    """Кастомное исключение для недоступного сервера."""
    pass


class BaseKeyManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.base_url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/panel"
        self.get_cert_api_url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/server/getNewX25519Cert"

    @staticmethod
    def generate_uuid():
        """Генерирует UUID для клиентов."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_port():
        """Генерирует случайный порт в диапазоне 10000-65535."""
        return random.randint(10000, 65535)

    def generate_short_ids(self, count=8):
        """
        Генерирует массив shortIds в hex формате разной длины.
        Формат: от 2 до 16 символов hex для Reality протокола.
        """
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

    def generate_subid(self, length=16):
        """Генерирует ID подписки из букв и цифр."""
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    async def get_inbounds(self):
        """Получает список всех инбаундов."""
        list_api_url = f"{self.base_url}/inbound/list"
        cookies = await get_session_cookie(self.server_ip)
        async with aiohttp.ClientSession() as session:
            async with session.post(list_api_url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_inbound_by_id(self, inbound_id):
        """Получает данные инбаунда по ID."""
        get_inbound_api_url = f"{self.base_url}/api/inbounds/get/{inbound_id}"
        cookies = await get_session_cookie(self.server_ip)
        async with aiohttp.ClientSession() as session:
            async with session.get(get_inbound_api_url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_online_users(self):
        """Получает список онлайн пользователей."""
        url = f"{self.base_url}/inbound/onlines"
        cookies = await get_session_cookie(self.server_ip)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=await response.text()
                    )

    async def get_certificate(self):
        """Получает X25519 сертификат для Reality протокола."""
        max_retries = 3
        retries = 0

        async with aiohttp.ClientSession() as session:
            while retries < max_retries:
                try:
                    cookies = await get_session_cookie(self.server_ip)
                    async with session.post(self.get_cert_api_url, cookies=cookies, ssl=False) as response:
                        if response.status == 200:
                            cert_data = await response.json()
                            if cert_data.get("success"):
                                return cert_data["obj"]
                        print(f"Certificate generation failed (attempt {retries + 1}/{max_retries})")
                        retries += 1
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"Certificate request failed (attempt {retries + 1}/{max_retries}): {e}")
                    retries += 1
                    await asyncio.sleep(1)

            raise ValueError("Failed to generate certificate after multiple attempts")

    async def get_or_create_port_443_inbound(self):
        """
        Получает инбаунд с портом 443, создает если не существует.

        Returns:
            dict: данные инбаунда с портом 443
        """
        # Ищем существующий инбаунд с портом 443
        try:
            inbounds_data = await self.get_inbounds()
            if inbounds_data and inbounds_data.get("success"):
                for inbound in inbounds_data.get("obj", []):
                    if inbound.get("port") == 443:
                        print(f"Found existing inbound with port 443, ID: {inbound['id']}")
                        return inbound
        except Exception as e:
            print(f"Error checking existing inbounds: {e}")

        # Создаем новый инбаунд с портом 443
        print("Creating new inbound with port 443...")

        cert_data = await self.get_certificate()
        generated_short_ids = self.generate_short_ids()

        inbound_data = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": "Main VLESS Inbound - Port 443",
            "enable": True,
            "expiryTime": 0,
            "listen": "",
            "port": 443,
            "protocol": "vless",
            "settings": json.dumps({
                "clients": [],
                "decryption": "none",
                "fallbacks": []
            }),
            "streamSettings": json.dumps({
                "network": "xhttp",
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
                "xhttpSettings": {
                    "path": "/main443",
                    "host": "",
                    "headers": {},
                    "scMaxBufferedPosts": 30,
                    "scMaxEachPostBytes": "1000000",
                    "scStreamUpServerSecs": "20-80",
                    "noSSEHeader": False,
                    "xPaddingBytes": "100-1000",
                    "mode": "auto"
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

        create_api_url = f"{self.base_url}/inbound/add"
        cookies = await get_session_cookie(self.server_ip)

        async with aiohttp.ClientSession() as session:
            async with session.post(create_api_url, cookies=cookies, json=inbound_data, ssl=False) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success"):
                        print(f"Successfully created inbound with port 443, ID: {response_data['obj']['id']}")
                        return response_data["obj"]
                    else:
                        raise Exception(f"API Error: {response_data.get('msg', 'Unknown error')}")
                elif response.status == 400:
                    error_text = await response.text()
                    if "port already in use" in error_text.lower():
                        # Race condition - проверяем еще раз
                        await asyncio.sleep(1)
                        inbounds_data = await self.get_inbounds()
                        if inbounds_data and inbounds_data.get("success"):
                            for inbound in inbounds_data.get("obj", []):
                                if inbound.get("port") == 443:
                                    return inbound
                        raise Exception("Port 443 is occupied but inbound not found")
                    else:
                        raise Exception(f"Bad request: {error_text}")
                elif response.status == 401:
                    # Повторяем с новыми cookies
                    cookies = await get_session_cookie(self.server_ip)
                    async with session.post(create_api_url, cookies=cookies, json=inbound_data,
                                            ssl=False) as retry_response:
                        if retry_response.status == 200:
                            response_data = await retry_response.json()
                            if response_data.get("success"):
                                return response_data["obj"]
                    raise Exception("Failed to create inbound after session refresh")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP Error {response.status}: {error_text}")

    async def add_client_to_inbound(self, tg_id: str, server_name: str):
        """
        Добавляет нового клиента в существующий инбаунд.
        Returns:
            tuple: (client_uuid, email, success)
        """
        add_client_url = f"{self.base_url}/inbound/addClient"

        client_uuid = self.generate_uuid()
        email = self.generate_short_id()
        sub_id = self.generate_subid()

        new_client = {
            "id": client_uuid,
            "flow": "",
            "email": email,
            "limitIp": LIMIT,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
            "tgId": str(tg_id),
            "subId": str(tg_id),
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

        async with aiohttp.ClientSession() as session:
            try:
                cookies = await get_session_cookie(self.server_ip)
                async with session.post(add_client_url, cookies=cookies, json=payload, ssl=False) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get("success"):
                            url_config = self.generate_vless_link_for_client(client_uuid, server_name, main_inbound)
                            print(f"Client {email} successfully added to inbound {inbound_id}")
                            return client_uuid, email, url_config
                        else:
                            print(f"API Error: {response_data.get('msg', 'Unknown error')}")
                            return None, None, False

                    elif response.status == 401:
                        cookies = await get_session_cookie(self.server_ip)
                        async with session.post(add_client_url, cookies=cookies, json=payload,
                                                ssl=False) as retry_response:
                            if retry_response.status == 200:
                                response_data = await retry_response.json()
                                return client_uuid, email, response_data.get("success", False)
                            return None, None, False
                    else:
                        error_text = await response.text()
                        print(f"Error adding client: {response.status}, {error_text}")
                        return None, None, False

            except Exception as e:
                print(f"Exception during add client request: {e}")
                return None, None, False

    async def update_client_status(self, client_uuid: str, email: str, user_id: int, enable: bool):
        """
        Включает или выключает клиента в инбаунде.

        Returns:
            bool: успешность операции
        """
        update_client_url = f"{self.base_url}/inbound/updateClient/{client_uuid}"

        try:
            main_inbound = await self.get_or_create_port_443_inbound()
            inbound_id = main_inbound["id"]

            payload = {
                "id": inbound_id,
                "settings": json.dumps({
                    "clients": [{
                        "id": client_uuid,
                        "flow": "",
                        "email": email,
                        "limitIp": LIMIT,
                        "totalGB": 0,
                        "expiryTime": 0,
                        "enable": enable,
                        "tgId": str(user_id),
                        "subId": str(user_id),
                        "comment": f"TgID: {user_id}",
                        "reset": 0
                    }]
                })
            }

            async with aiohttp.ClientSession() as session:
                cookies = await get_session_cookie(self.server_ip)
                async with session.post(update_client_url, cookies=cookies, json=payload, ssl=False) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get("success"):
                            status = "enabled" if enable else "disabled"
                            print(f"Client {client_uuid} successfully {status}")
                            return True
                        else:
                            print(f"API Error: {response_data.get('msg', 'Unknown error')}")
                            return False

                    elif response.status == 401:
                        cookies = await get_session_cookie(self.server_ip)
                        async with session.post(update_client_url, cookies=cookies, json=payload,
                                                ssl=False) as retry_response:
                            if retry_response.status == 200:
                                response_data = await retry_response.json()
                                return response_data.get("success", False)
                            return False
                    else:
                        error_text = await response.text()
                        print(f"Error updating client: {response.status}, {error_text}")
                        return False

        except Exception as e:
            print(f"Exception during client update: {e}")
            return False

    def generate_vless_link_for_client(self, client_uuid: str, server_name: str, inbound_data: dict):
        """
        Генерирует VLESS ссылку для клиента в инбаунде.

        Args:
            client_uuid: UUID клиента
            server_name: название сервера
            inbound_data: данные инбаунда

        Returns:
            str: готовая VLESS ссылка
        """
        try:
            stream_settings = json.loads(inbound_data["streamSettings"])
            reality_settings = stream_settings["realitySettings"]
            xhttp_settings = stream_settings["xhttpSettings"]

            public_key = reality_settings["settings"]["publicKey"]
            short_ids = reality_settings["shortIds"]
            xhttp_path = xhttp_settings["path"]
            port = inbound_data["port"]

            selected_short_id = random.choice(short_ids)

            return (f"vless://{client_uuid}@{self.server_ip}:{port}"
                    f"?type=xhttp&path={xhttp_path}&host=&mode=auto"
                    f"&security=reality&pbk={public_key}"
                    f"&fp=chrome&pqv=&sni=github.com&sid={selected_short_id}"
                    f"#{server_name}-VLESS")

        except Exception as e:
            print(f"Error generating VLESS link: {e}")
            raise
