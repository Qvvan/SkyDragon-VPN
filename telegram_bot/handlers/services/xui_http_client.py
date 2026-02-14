"""HTTP клиент для работы с 3x-ui панелью через новую API"""
import asyncio
import json
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ContentTypeError

from logger.logging_config import logger


class ServerUnavailableError(Exception):
    """Исключение для недоступного сервера"""
    pass


def _client_settings_by_protocol(
    protocol: str,
    client_id: str,
    email: str,
    tg_id: str,
    sub_id: str,
    limit_ip: int = 1,
    total_gb: int = 0,
    expiry_time: int = 0,
    enable: bool = True,
    comment: str | None = None,
) -> dict[str, Any]:
    """
    Формирует объект клиента для settings.clients в зависимости от протокола инбаунда.
    VLESS: id (UUID), flow, email, limitIp, ...
    Trojan: password (используем client_id как пароль), email, limitIp, ... (без id и flow)
    Остальные протоколы: как VLESS.
    """
    comment = comment or f"TgID: {tg_id}"
    proto = (protocol or "vless").strip().lower()

    if proto == "trojan":
        return {
            "password": client_id,
            "email": email,
            "limitIp": limit_ip,
            "totalGB": total_gb,
            "expiryTime": expiry_time,
            "enable": enable,
            "tgId": tg_id,
            "subId": sub_id,
            "comment": comment,
            "reset": 0,
        }
    # vless, vmess и остальные
    return {
        "id": client_id,
        "flow": "xtls-rprx-vision",
        "email": email,
        "limitIp": limit_ip,
        "totalGB": total_gb,
        "expiryTime": expiry_time,
        "enable": enable,
        "tgId": tg_id,
        "subId": sub_id,
        "comment": comment,
        "reset": 0,
    }


class XuiPanelHttpClient:
    """HTTP клиент для работы с 3x-ui панелью через новую API"""

    __slots__ = [
        "_server_url",
        "_base_path",
        "_login",
        "_password",
        "_connect_timeout",
        "_total_timeout",
        "_max_retries",
        "_session",
        "_is_authenticated",
    ]

    def __init__(
        self,
        server_url: str,
        base_path: str,
        login: str,
        password: str,
        connect_timeout: int = 2,
        total_timeout: int = 5,
        max_retries: int = 2,
    ):
        """
        Инициализирует HTTP клиент

        Args:
            server_url: URL сервера (например, https://5.180.145.9:14880)
            base_path: Базовый путь панели (например, /dqAdBNC47ZTHYBV)
            login: Логин для авторизации
            password: Пароль для авторизации
            connect_timeout: Таймаут подключения в секундах
            total_timeout: Общий таймаут запроса в секундах
            max_retries: Максимальное количество попыток
        """
        self._server_url = server_url.rstrip("/")
        self._base_path = base_path.rstrip("/")
        self._login = login
        self._password = password
        self._connect_timeout = connect_timeout
        self._total_timeout = total_timeout
        self._max_retries = max_retries
        self._session: ClientSession | None = None
        self._is_authenticated = False

    async def ping(self) -> bool:
        """
        Лёгкая проверка доступности сервера: GET на корень (не на /login —
        там может быть только POST). Достаточно убедиться, что хост:порт отвечают.
        """
        url = f"{self._server_url}/"
        timeout = ClientTimeout(connect=2, total=4)
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(url, ssl=False) as response:
                    # Любой ответ — сервер живой
                    await logger.info(
                        f"ping: {self._server_url} ответил статусом {response.status}"
                    )
                    return True
        except asyncio.TimeoutError:
            await logger.info(
                f"ping: timeout для {self._server_url} "
                f"(URL: {url}, connect_timeout=2, total_timeout=4)"
            )
            return False
        except aiohttp.ClientConnectorError as e:
            await logger.info(
                f"ping: connection error для {self._server_url} "
                f"(URL: {url}): {e}"
            )
            return False
        except aiohttp.ClientError as e:
            await logger.info(
                f"ping: client error для {self._server_url} "
                f"(URL: {url}): {e}"
            )
            return False
        except OSError as e:
            await logger.info(
                f"ping: OS error для {self._server_url} "
                f"(URL: {url}): {e}"
            )
            return False
        except Exception as e:
            await logger.info(
                f"ping: неожиданная ошибка для {self._server_url} "
                f"(URL: {url}): {type(e).__name__}: {e}"
            )
            return False

    async def _get_session(self) -> ClientSession:
        """Получает или создает HTTP сессию"""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(
                connect=self._connect_timeout,
                total=self._total_timeout,
            )
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = ClientSession(
                timeout=timeout,
                connector=connector,
                cookie_jar=aiohttp.CookieJar(unsafe=True),
            )
        return self._session

    async def _authenticate(self) -> bool:
        """Аутентифицируется на панели"""
        login_url = f"{self._server_url}{self._base_path}/login"
        payload = {
            "username": self._login,
            "password": self._password,
        }

        session = await self._get_session()

        for attempt in range(self._max_retries):
            try:
                async with session.post(login_url, data=payload, ssl=False) as response:
                    if response.status == 200:
                        self._is_authenticated = True
                        return True
                    self._is_authenticated = False
                    await logger.warning(
                        f"Неудачная аутентификация на {self._server_url}, статус: {response.status}"
                    )
            except asyncio.TimeoutError:
                await logger.warning(
                    f"Timeout при аутентификации на {self._server_url}, попытка {attempt + 1}"
                )
            except aiohttp.ClientError as e:
                await logger.warning(f"Ошибка при аутентификации на {self._server_url}: {e}")

            if attempt < self._max_retries - 1:
                await asyncio.sleep(0.5)

        await logger.error(
            f"Не удалось аутентифицироваться на {self._server_url} после {self._max_retries} попыток",
            None,
        )
        return False

    async def _ensure_authenticated(self) -> None:
        """Убеждается, что клиент аутентифицирован"""
        if not self._is_authenticated:
            if not await self._authenticate():
                raise ServerUnavailableError(f"Не удалось аутентифицироваться на {self._server_url}")

    async def _safe_json_parse(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Безопасно парсит JSON из ответа"""
        try:
            return await response.json()
        except ContentTypeError:
            text = await response.text()
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                await logger.error(f"Ошибка парсинга JSON. Ответ: {text[:200]}", e)
                raise ServerUnavailableError(f"Не удалось распарсить ответ от сервера: {text[:200]}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> dict[str, Any]:
        """Выполняет HTTP запрос к API"""
        url = f"{self._server_url}{self._base_path}{endpoint}"
        session = await self._get_session()

        await self._ensure_authenticated()

        for attempt in range(self._max_retries):
            try:
                kwargs: dict[str, Any] = {"ssl": False}
                if json_data:
                    kwargs["json"] = json_data
                elif data:
                    kwargs["data"] = data

                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await self._safe_json_parse(response)
                    elif response.status in (401, 403) and retry_auth:
                        await logger.warning(f"Получен {response.status}, пытаемся переаутентифицироваться")
                        self._is_authenticated = False
                        if await self._authenticate():
                            async with session.request(method, url, **kwargs) as retry_response:
                                if retry_response.status == 200:
                                    return await self._safe_json_parse(retry_response)
                                error_text = await retry_response.text()
                                await logger.error(
                                    f"Ошибка после переаутентификации {method} {url}: статус {retry_response.status}",
                                    None,
                                )
                        raise ServerUnavailableError(f"Не удалось аутентифицироваться для запроса {method} {url}")
                    else:
                        error_text = await response.text()
                        await logger.error(
                            f"Ошибка запроса {method} {url}: статус {response.status}, ответ: {error_text[:200]}",
                            None,
                        )
                        raise ServerUnavailableError(
                            f"Ошибка запроса: статус {response.status}, ответ: {error_text[:200]}"
                        )
            except ServerUnavailableError:
                raise
            except asyncio.TimeoutError:
                await logger.warning(f"Timeout при запросе {method} {url}, попытка {attempt + 1}")
            except aiohttp.ClientError as e:
                await logger.warning(f"Ошибка клиента при запросе {method} {url}: {e}")

            if attempt < self._max_retries - 1:
                await asyncio.sleep(0.5)

        raise ServerUnavailableError(f"Не удалось выполнить запрос {method} {url} после {self._max_retries} попыток")

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Выполняет GET запрос"""
        return await self._make_request("GET", endpoint)

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Выполняет POST запрос"""
        return await self._make_request("POST", endpoint, json_data=json_data, data=data)

    async def get_inbound_by_port(self, port: int) -> dict[str, Any] | None:
        """
        Получает инбаунд по порту

        Args:
            port: Порт инбаунда

        Returns:
            Словарь с данными инбаунда или None если не найден
        """
        try:
            response = await self.get("/panel/api/inbounds/list")

            if response.get("success"):
                inbounds = response.get("obj", [])
                if not isinstance(inbounds, list):
                    return None

                for inbound in inbounds:
                    if inbound.get("port") == port:
                        return inbound

                return None
            else:
                await logger.warning("Не удалось получить список инбаундов")
                return None
        except Exception as e:
            await logger.error(f"Исключение при получении инбаунда по порту {port}", e)
            return None

    async def add_client(
        self,
        inbound_id: int,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 1,
        expiry_time: int = 0,
        enable: bool = True,
        protocol: str = "vless",
    ) -> bool:
        """
        Добавляет клиента в инбаунд.
        Формат клиента зависит от протокола: VLESS (id, flow, ...), Trojan (password, ...).

        Args:
            inbound_id: ID инбаунда
            client_id: UUID клиента (для Trojan используется как password)
            email: Email клиента
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов
            expiry_time: Время истечения в миллисекундах (0 = без ограничений)
            enable: Включен ли клиент
            protocol: Протокол инбаунда (vless, trojan, vmess, ...)
        """
        client_data = _client_settings_by_protocol(
            protocol=protocol,
            client_id=client_id,
            email=email,
            tg_id=tg_id,
            sub_id=sub_id,
            limit_ip=limit_ip,
            total_gb=0,
            expiry_time=expiry_time,
            enable=enable,
        )

        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_data]}),
        }

        try:
            response = await self.post("/panel/api/inbounds/addClient", json_data=payload)

            if response.get("success"):
                await logger.info(f"Клиент {client_id} успешно добавлен в инбаунд {inbound_id}")
                return True
            error_msg = response.get("msg", "Неизвестная ошибка") or ""
            if "Duplicate email" in error_msg or "duplicate" in error_msg.lower():
                await logger.info(
                    f"Клиент с email уже есть в инбаунде {inbound_id}, пропускаем: {error_msg[:80]}"
                )
                return True
            await logger.error(f"Ошибка добавления клиента: {error_msg}", None)
            return False
        except Exception as e:
            await logger.error(f"Исключение при добавлении клиента {client_id}", e)
            return False

    async def update_client_enable(
        self,
        inbound_id: int,
        client_id: str,
        enable: bool,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 1,
        protocol: str = "vless",
    ) -> bool:
        """
        Обновляет статус включения/выключения клиента.
        Формат клиента зависит от протокола (VLESS vs Trojan).
        """
        client_data = _client_settings_by_protocol(
            protocol=protocol,
            client_id=client_id,
            email=email,
            tg_id=tg_id,
            sub_id=sub_id,
            limit_ip=limit_ip,
            total_gb=0,
            expiry_time=0,
            enable=enable,
        )

        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_data]}),
        }

        try:
            endpoint = f"/panel/api/inbounds/updateClient/{client_id}"
            response = await self.post(endpoint, json_data=payload)

            if response.get("success"):
                await logger.info(f"Статус клиента {client_id} успешно обновлен (enable={enable})")
                return True
            else:
                error_msg = response.get("msg", "Неизвестная ошибка")
                await logger.warning(f"Ошибка обновления статуса клиента: {error_msg}")
                return False
        except Exception as e:
            await logger.error(f"Исключение при обновлении статуса клиента {client_id}", e)
            return False

    async def close(self) -> None:
        """Закрывает HTTP сессию"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
