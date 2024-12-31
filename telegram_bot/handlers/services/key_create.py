import base64
import json
import random
import uuid

import aiohttp

from config_data.config import MY_SECRET_URL, PORT_X_UI
from handlers.services.get_session_cookies import get_session_cookie


class ServerUnavailableError(Exception):
    """Кастомное исключение для недоступного сервера."""
    pass


class BaseKeyManager:
    def __init__(self, server_ip):
        self.server_ip = server_ip
        self.base_url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/panel"

    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())

    @staticmethod
    def generate_port():
        return random.randint(10000, 65535)

    async def get_inbounds(self, session):
        list_api_url = f"{self.base_url}/inbound/list"
        cookies = await get_session_cookie(self.server_ip)
        async with session.post(list_api_url, cookies=cookies, ssl=False) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise aiohttp.ClientResponseError(
                    response.request_info, response.history,
                    status=response.status, message=await response.text()
                )

    async def get_inbound_by_id(self, inbound_id):
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

            return None

    async def delete_key(self, key_id: str):
        """
        Удаляет ключ с указанным key_id.

        Args:
            key_id (str): Идентификатор ключа для удаления.
        """
        delete_api_url = f"{self.base_url}/api/inbounds/del/{key_id}"

        async with aiohttp.ClientSession() as session:
            cookies = await get_session_cookie(self.server_ip)
            async with session.post(delete_api_url, cookies=cookies, ssl=False) as response:
                if response.status == 200:
                    print(f"Key with ID {key_id} successfully deleted.")
                elif response.status == 401:
                    # Получаем новый session_cookie
                    cookies = await get_session_cookie(self.server_ip)
                    async with session.post(delete_api_url, cookies=cookies, ssl=False) as retry_response:
                        if retry_response.status == 200:
                            print(f"Key with ID {key_id} successfully deleted after refreshing session.")
                        else:
                            error_text = await retry_response.text()
                            print(f"Error deleting key after retry: {retry_response.status}, {error_text}")
                            raise aiohttp.ClientResponseError(
                                retry_response.request_info, retry_response.history,
                                status=retry_response.status, message=error_text
                            )
                else:
                    error_text = await response.text()
                    print(f"Error deleting key: {response.status}, {error_text}")
                    raise aiohttp.ClientResponseError(
                        response.request_info, response.history,
                        status=response.status, message=error_text
                    )

    async def update_key_enable(self, key_id: str, enable: bool):
        """
        Обновляет только поле `enable` для ключа с указанным key_id.

        Args:
            key_id (str): Идентификатор ключа для обновления.
            enable (bool): Новый статус для поля `enable`.

        Raises:
            ValueError: Если ключ не удалось получить или обновить.
        """
        # Получаем текущий объект ключа
        get_api_url = f"{self.base_url}/api/inbounds/get/{key_id}"
        update_api_url = f"{self.base_url}/api/inbounds/update/{key_id}"

        async with aiohttp.ClientSession() as session:
            try:
                cookies = await get_session_cookie(self.server_ip)
                async with session.get(get_api_url, cookies=cookies, ssl=False) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Failed to fetch key with ID {key_id}: {response.status}, {error_text}")

                    data = await response.json()
                    if not data.get("success"):
                        raise ValueError(
                            f"API Error while fetching key with ID {key_id}: {data.get('msg', 'Unknown error')}"
                        )

                    # Получаем объект ключа
                    key_data = data["obj"]

                # Обновляем только поле `enable` в объекте
                key_data["enable"] = enable

                # Если поле `settings` или `streamSettings` — строка, декодируем для обновления
                if isinstance(key_data.get("settings"), str):
                    key_data["settings"] = json.loads(key_data["settings"])
                if isinstance(key_data.get("streamSettings"), str):
                    key_data["streamSettings"] = json.loads(key_data["streamSettings"])
                if isinstance(key_data.get("sniffing"), str):
                    key_data["sniffing"] = json.loads(key_data["sniffing"])

                # Возвращаем преобразованные строки
                key_data["settings"] = json.dumps(key_data["settings"])
                key_data["streamSettings"] = json.dumps(key_data["streamSettings"])
                key_data["sniffing"] = json.dumps(key_data["sniffing"])

                # Отправляем обновленный объект на сервер
                async with session.post(update_api_url, cookies=cookies, json=key_data,
                                        ssl=False) as update_response:
                    if update_response.status == 200:
                        print(f"Key with ID {key_id} successfully updated to {'enabled' if enable else 'disabled'}.")
                    elif update_response.status == 401:
                        cookies = await get_session_cookie(self.server_ip)

                        async with session.post(update_api_url, cookies=cookies, json=key_data,
                                                ssl=False) as retry_response:
                            if retry_response.status == 200:
                                print(f"Key with ID {key_id} successfully updated after refreshing session.")
                            else:
                                error_text = await retry_response.text()
                                raise ValueError(
                                    f"Failed to update key with ID {key_id} after retry: {retry_response.status}, {error_text}")
                    else:
                        error_text = await update_response.text()
                        raise ValueError(
                            f"Failed to update key with ID {key_id}: {update_response.status}, {error_text}")

            except aiohttp.ClientError as e:
                raise ValueError(f"HTTP Client Error while processing key with ID {key_id}: {e}")
            except ValueError as e:
                # Логируем ошибку и возвращаем информативное сообщение
                print(f"Error: {e}")
                raise
            except Exception as e:
                print(f"Unexpected error while updating key with ID {key_id}: {e}")
                raise ValueError(f"Unexpected error while updating key with ID {key_id}: {e}")


class VlessKeyManager(BaseKeyManager):
    def __init__(self, server_ip):
        super().__init__(server_ip)
        self.get_cert_api_url = f"https://{server_ip}:{PORT_X_UI}/{MY_SECRET_URL}/server/getNewX25519Cert"

    async def get_certificate(self, session):
        cookies = await get_session_cookie(self.server_ip)
        async with session.post(self.get_cert_api_url, cookies=cookies, ssl=False) as response:
            if response.status == 200:
                cert_data = await response.json()
                if cert_data.get("success"):
                    return cert_data["obj"]
                else:
                    raise ValueError("Certificate generation failed.")
            else:
                raise aiohttp.ClientResponseError(
                    response.request_info, response.history,
                    status=response.status, message=await response.text()
                )

    async def create_vless_key(self, session, new_client, private_key, public_key):
        create_api_url = f"{self.base_url}/inbound/add"

        while True:
            cookies = await get_session_cookie(self.server_ip)

            port = self.generate_port()
            short_id = uuid.uuid4().hex[:8]

            sub_id = str(uuid.uuid4())

            new_vless_key_data = {
                "up": 0,
                "down": 0,
                "total": 0,
                "remark": new_client["remark"],
                "enable": True,
                "expiryTime": 0,
                "listen": "",
                "port": port,
                "protocol": "vless",
                "settings": json.dumps({
                    "clients": [
                        {
                            "id": new_client["id"],
                            "flow": "xtls-rprx-vision-udp443",
                            "email": new_client.get("email", ""),
                            "limitIp": 1,
                            "totalGB": 0,
                            "expiryTime": 0,
                            "enable": True,
                            "tgId": "",
                            "subId": sub_id,  # Укажите здесь ваш `subId`
                            "reset": 0
                        }
                    ],
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
                        "dest": "google.com:443",
                        "serverNames": ["google.com", "www.google.com"],
                        "privateKey": private_key,
                        "minClient": "",
                        "maxClient": "",
                        "maxTimediff": 0,
                        "shortIds": [
                            "99", "b5056a7fd4c966", "7a331546705f21a6", "0f6e",
                            "2f08168c", "c68d0a1befc3", "53b0e4", "e3b7a4adcc"
                        ],
                        "settings": {
                            "publicKey": public_key,
                            "fingerprint": "chrome",  # Заменено с `firefox` на `chrome`
                            "serverName": "",
                            "spiderX": "/"
                        }
                    },
                    "tcpSettings": {
                        "acceptProxyProtocol": False,
                        "header": {"type": "none"}
                    }
                }),
                "sniffing": json.dumps({
                    "enabled": True,
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

            try:
                # Попытка отправить запрос с текущими данными
                async with session.post(
                        create_api_url,
                        cookies=cookies,  # Используем актуальные куки
                        json=new_vless_key_data,
                        ssl=False
                ) as response:
                    if response.status == 200:
                        # Если запрос успешен, возвращаем результат
                        return await response.json(), port, short_id
                    elif response.status == 400 and "port already in use" in await response.text().lower():
                        print(f"Port {port} is already in use, trying a new port...")
                        continue
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history,
                            status=response.status, message=await response.text()
                        )
            except aiohttp.ClientError as e:
                print(f"An error occurred during the request: {e}")
                raise

    async def manage_vless_key(self, tg_id, username):
        async with aiohttp.ClientSession() as session:
            try:
                new_client = {
                    "id": self.generate_uuid(),
                    "flow": "xtls-rprx-vision-udp443",
                    "email": self.generate_uuid(),
                    "limitIp": 1,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": tg_id,
                    "remark": f"Пользователь: {username}, TgId: {tg_id}"
                }

                cert_data = await self.get_certificate(session)
                response, port, short_id = await self.create_vless_key(
                    session,
                    new_client,
                    cert_data["privateKey"],
                    cert_data["publicKey"],
                )
                key_id = response.get('obj', {}).get('id')
                vless_link = self.generate_vless_link(
                    client_id=new_client["id"],
                    port=port,
                    short_id=short_id,
                    public_key=cert_data["publicKey"],
                    server_name="google.com"
                )
                return vless_link, key_id
            except aiohttp.ClientResponseError as e:
                print(f"Request error: {e}")

    def generate_vless_link(self, client_id, port, short_id, public_key, server_name="google.com"):
        return (f"vless://{client_id}@{self.server_ip}:{port}"
                f"?type=tcp&security=reality&pbk={public_key}"
                f"&fp=chrome&sni={server_name}&sid={99}&spx=%2F&flow=xtls-rprx-vision-udp443"
                f"#SkyDragon")


class ShadowsocksKeyManager(BaseKeyManager):
    async def create_shadowsocks_key(self, session, new_client, new_password, new_port):
        create_api_url = f"{self.base_url}/inbound/add"

        while True:
            # Получаем (или обновляем) куки
            cookies = await get_session_cookie(self.server_ip)

            # Формируем данные для запроса
            new_ss_key_data = {
                "up": 0,
                "down": 0,
                "total": 0,
                "remark": new_client["remark"],
                "enable": True,
                "expiryTime": 0,
                "listen": "",
                "port": new_port,
                "protocol": "shadowsocks",
                "settings": json.dumps({
                    "method": "chacha20-ietf-poly1305",
                    "password": new_password,
                    "network": "tcp,udp",
                    "clients": [new_client]
                }),
                "streamSettings": json.dumps({
                    "network": "tcp",
                    "security": "none",
                    "tcpSettings": {
                        "acceptProxyProtocol": False,
                        "header": {"type": "none"}
                    },
                    "externalProxy": []
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

            # Выполняем запрос
            try:
                async with session.post(
                        create_api_url,
                        cookies=cookies,
                        json=new_ss_key_data,
                        ssl=False
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        response_data['password'] = new_password
                        return response_data
                    elif response.status == 401:
                        # Если ошибка авторизации, перезапрашиваем куки
                        print("Cookies expired, re-authenticating...")
                        cookies = await get_session_cookie(self.server_ip)
                        if not cookies:
                            raise Exception("Re-authentication failed.")
                    elif response.status == 400 and "port already in use" in await response.text().lower():
                        new_port = self.generate_port()
                        continue
                    else:
                        raise aiohttp.ClientResponseError(
                            response.request_info, response.history,
                            status=response.status, message=await response.text()
                        )
            except aiohttp.ClientError as e:
                print(f"An error occurred during the request: {e}")
                raise

    async def manage_shadowsocks_key(self, tg_id, username):
        async with aiohttp.ClientSession() as session:
            try:
                new_port = self.generate_port()
                new_password = uuid.uuid4().hex
                method = "chacha20-ietf-poly1305"
                new_client = {
                    "method": method,
                    "password": new_password,
                    "email": self.generate_uuid(),
                    "limitIp": 1,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": tg_id,
                    "remark": f"Пользователь: {username}, TgId: {tg_id}"
                }

                # Используем session_cookie в create_shadowsocks_key
                response = await self.create_shadowsocks_key(session, new_client, new_password, new_port)
                key_id = response.get('obj', {}).get('id')
                return self.generate_ss_link(new_port, new_password, method, key_id), key_id
            except aiohttp.ClientResponseError as e:
                print(f"Request error: {e}")

    def generate_ss_link(self, port, password, method, key_id):
        user_info = f"{method}:{password}".encode()
        user_info_base64 = base64.b64encode(user_info).decode()
        return f"ss://{user_info_base64}@{self.server_ip}:{port}?prefix=POST%20&type=tcp#SkyDragon"
