"""Единый фасад для работы с панелью 3x-ui через новую API (HTTP) или старую (SSH)"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp

from config_data.config import LOGIN_X_UI_PANEL, PASSWORD_X_UI_PANEL, MY_SECRET_URL, PORT_X_UI
from handlers.services.xui_http_client import XuiPanelHttpClient, ServerUnavailableError as HttpServerUnavailableError
from handlers.services.xui_ssh_client import XuiPanelSshClient
from logger.logging_config import logger
from models.models import Servers

# Кэш HTTP-клиентов с куками: ключ = (server_ip, panel_port, base_path), значение = (client, timestamp)
# Переиспользуем клиентов до истечения TTL, чтобы не авторизоваться каждый раз
_http_client_cache: dict[str, tuple[XuiPanelHttpClient, float]] = {}
HTTP_CACHE_TTL_SEC = 30 * 60  # 30 минут


def _server_cache_key(server: Servers) -> str:
    """Ключ кэша по данным сервера."""
    port = server.panel_port or PORT_X_UI or 443
    path = (server.url_secret or MY_SECRET_URL or "").strip("/")
    return f"{server.server_ip}:{port}:{path}"


class PanelGateway:
    """Единый фасад для работы с панелью 3x-ui с автоматическим fallback HTTP -> SSH"""

    def __init__(self, server: Servers):
        """
        Инициализирует gateway для работы с сервером

        Args:
            server: Объект сервера из БД
        """
        self._server = server
        self._http_client: Optional[XuiPanelHttpClient] = None
        self._ssh_client: Optional[XuiPanelSshClient] = None

    def _get_server_url(self) -> str:
        """Формирует URL сервера для HTTP клиента"""
        panel_port = self._server.panel_port or PORT_X_UI or 443
        return f"https://{self._server.server_ip}:{panel_port}"

    def _get_base_path(self) -> str:
        """Получает базовый путь панели"""
        # Если url_secret пустой или None, используем значение из конфига
        url_secret = self._server.url_secret if self._server.url_secret else MY_SECRET_URL
        if url_secret:
            # Убираем ведущий слэш если есть, потом добавляем один
            url_secret = url_secret.lstrip('/')
            return f"/{url_secret}" if url_secret else ""
        return ""

    def _get_http_client(self) -> XuiPanelHttpClient:
        """Возвращает HTTP клиент: из кэша (с куками) или создаёт новый и кэширует."""
        if self._http_client is not None:
            return self._http_client
        key = _server_cache_key(self._server)
        now = time.monotonic()
        if key in _http_client_cache:
            client, cached_at = _http_client_cache[key]
            if now - cached_at < HTTP_CACHE_TTL_SEC:
                self._http_client = client
                return client
            # Истёк TTL — убираем из кэша, ниже создадим новый клиент
            del _http_client_cache[key]
        client = XuiPanelHttpClient(
            server_url=self._get_server_url(),
            base_path=self._get_base_path(),
            login=LOGIN_X_UI_PANEL,
            password=PASSWORD_X_UI_PANEL,
            connect_timeout=2,
            total_timeout=5,
            max_retries=2,
        )
        _http_client_cache[key] = (client, now)
        self._http_client = client
        return client

    def _get_ssh_client(self) -> XuiPanelSshClient:
        """Создает или возвращает SSH клиент"""
        if self._ssh_client is None:
            self._ssh_client = XuiPanelSshClient(self._server.server_ip)
        return self._ssh_client

    async def ping_only(self) -> bool:
        """
        Лёгкая проверка «жив ли сервер»: только пинг без авторизации.
        Сначала HTTP GET, при неудаче — проверка через SSH.
        Для периодической проверки (раз в 1–3 мин).
        """
        server_url = self._get_server_url()
        base_path = self._get_base_path()
        ping_url = f"{server_url}/"
        
        try:
            # Временный клиент только для пинга: GET на корень сервера (не /login — там POST)
            ping_client = XuiPanelHttpClient(
                server_url=server_url,
                base_path=base_path,
                login=LOGIN_X_UI_PANEL,
                password=PASSWORD_X_UI_PANEL,
                connect_timeout=2,
                total_timeout=4,
                max_retries=1,
            )
            if await ping_client.ping():
                await logger.info(
                    f"ping_only: {self._server.server_ip} доступен по HTTP"
                )
                await ping_client.close()
                return True
            await logger.warning(
                f"ping_only: HTTP ping вернул False для {self._server.server_ip} "
                f"(URL: {ping_url})"
            )
            await ping_client.close()
        except asyncio.TimeoutError as e:
            await logger.warning(
                f"ping_only: HTTP timeout для {self._server.server_ip} "
                f"(URL: {ping_url}, connect_timeout=2, total_timeout=4): {e}"
            )
        except aiohttp.ClientConnectorError as e:
            await logger.warning(
                f"ping_only: HTTP connection error для {self._server.server_ip} "
                f"(URL: {ping_url}): {e}"
            )
        except aiohttp.ClientError as e:
            await logger.warning(
                f"ping_only: HTTP client error для {self._server.server_ip} "
                f"(URL: {ping_url}): {e}"
            )
        except Exception as e:
            await logger.warning(
                f"ping_only: Неожиданная ошибка HTTP для {self._server.server_ip} "
                f"(URL: {ping_url}): {type(e).__name__}: {e}"
            )
        
        # Fallback на SSH
        await logger.info(
            f"ping_only: Переход на SSH fallback для {self._server.server_ip} "
            f"(HTTP недоступен)"
        )
        try:
            ssh_client = self._get_ssh_client()
            ssh_result = await ssh_client.check_reachable()
            if ssh_result:
                await logger.info(
                    f"ping_only: {self._server.server_ip} доступен по SSH "
                    f"(после HTTP неудачи)"
                )
            else:
                await logger.warning(
                    f"ping_only: {self._server.server_ip} недоступен и по SSH "
                    f"(после HTTP неудачи)"
                )
            return ssh_result
        except Exception as e:
            await logger.warning(
                f"ping_only: SSH fallback ошибка для {self._server.server_ip}: "
                f"{type(e).__name__}: {e}"
            )
            return False

    async def check_reachable(self) -> bool:
        """
        Проверяет доступность панели: сначала HTTP (с авторизацией), при неудаче — SSH.
        Для разовых проверок (например, в админке «показать серверы»).
        """
        server_url = self._get_server_url()
        base_path = self._get_base_path()
        auth_url = f"{server_url}{base_path}/login"
        
        try:
            http_client = self._get_http_client()
            if await http_client._authenticate():
                await logger.info(
                    f"check_reachable: {self._server.server_ip} доступен по HTTP "
                    f"(URL: {auth_url}, метод: POST /login)"
                )
                return True
            else:
                await logger.warning(
                    f"check_reachable: HTTP аутентификация вернула False для {self._server.server_ip} "
                    f"(URL: {auth_url}, метод: POST /login)"
                )
        except asyncio.TimeoutError as e:
            await logger.warning(
                f"check_reachable: HTTP timeout для {self._server.server_ip} "
                f"(URL: {auth_url}, метод: POST /login): {e}"
            )
        except aiohttp.ClientConnectorError as e:
            await logger.warning(
                f"check_reachable: HTTP connection error для {self._server.server_ip} "
                f"(URL: {auth_url}, метод: POST /login): {e}"
            )
        except aiohttp.ClientError as e:
            await logger.warning(
                f"check_reachable: HTTP client error для {self._server.server_ip} "
                f"(URL: {auth_url}, метод: POST /login): {e}"
            )
        except HttpServerUnavailableError as e:
            await logger.warning(
                f"check_reachable: HTTP ServerUnavailableError для {self._server.server_ip} "
                f"(URL: {auth_url}, метод: POST /login): {e}"
            )
        except Exception as e:
            await logger.warning(
                f"check_reachable: Неожиданная ошибка HTTP для {self._server.server_ip} "
                f"(URL: {auth_url}, метод: POST /login): {type(e).__name__}: {e}"
            )
        
        # Fallback на SSH
        await logger.info(
            f"check_reachable: Переход на SSH fallback для {self._server.server_ip} "
            f"(HTTP недоступен)"
        )
        try:
            ssh_client = self._get_ssh_client()
            if await ssh_client.check_reachable():
                await logger.info(
                    f"check_reachable: {self._server.server_ip} доступен по SSH "
                    f"(после HTTP неудачи)"
                )
                return True
            else:
                await logger.warning(
                    f"check_reachable: {self._server.server_ip} недоступен и по SSH "
                    f"(после HTTP неудачи)"
                )
        except Exception as e:
            await logger.warning(
                f"check_reachable: SSH fallback ошибка для {self._server.server_ip}: "
                f"{type(e).__name__}: {e}"
            )
        return False

    async def get_inbound_by_port(self, port: int) -> dict | None:
        """
        Получает инбаунд по порту (сначала HTTP, потом SSH)

        Args:
            port: Порт инбаунда

        Returns:
            Словарь с данными инбаунда или None если не найден
        """
        # Попытка через HTTP
        try:
            http_client = self._get_http_client()
            inbound = await http_client.get_inbound_by_port(port)
            if inbound:
                await logger.info(
                    f"HTTP: инбаунд с портом {port} найден на {self._server.server_ip}"
                )
                return inbound
        except HttpServerUnavailableError as e:
            await logger.warning(
                f"HTTP недоступен для {self._server.server_ip}, пробуем SSH: {e}"
            )
        except Exception as e:
            await logger.warning(
                f"HTTP ошибка при получении инбаунда для {self._server.server_ip}: {e}"
            )

        # Fallback на SSH
        try:
            ssh_client = self._get_ssh_client()
            inbound = await ssh_client.get_inbound_by_port(port)
            if inbound:
                await logger.info(
                    f"SSH: инбаунд с портом {port} найден на {self._server.server_ip}"
                )
                return inbound
        except Exception as e:
            await logger.error(
                f"SSH ошибка при получении инбаунда для {self._server.server_ip}: {e}"
            )

        return None

    async def add_client(
        self,
        port: int,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 1,
        expiry_days: int = 0,
        enable: bool = True,
    ) -> bool:
        """
        Добавляет клиента в инбаунд (сначала HTTP, потом SSH)

        Args:
            port: Порт инбаунда
            client_id: UUID клиента
            email: Email клиента
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов
            expiry_days: Количество дней до истечения (0 = без ограничений)
            enable: Включен ли клиент

        Returns:
            True если клиент успешно добавлен
        """
        # Вычисляем expiry_time
        expiry_time = 0
        if expiry_days > 0:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=expiry_days)
            expiry_time = int(expiry_date.timestamp() * 1000)

        # Попытка через HTTP
        try:
            http_client = self._get_http_client()
            inbound = await http_client.get_inbound_by_port(port)
            if not inbound:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не найден")

            inbound_id = inbound.get("id")
            if not inbound_id:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не содержит ID")
            protocol = (inbound.get("protocol") or "vless").strip().lower()

            # Проверяем, нет ли уже клиента с таким email в инбаунде (избегаем Duplicate email)
            settings_raw = inbound.get("settings")
            if settings_raw:
                try:
                    settings = json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
                    for c in settings.get("clients", []):
                        if c.get("email") == email:
                            await logger.info(
                                f"HTTP: клиент с email {email} уже есть на порту {port} "
                                f"сервера {self._server.server_ip}, пропускаем"
                            )
                            return True
                except (json.JSONDecodeError, TypeError):
                    pass

            result = await http_client.add_client(
                inbound_id=inbound_id,
                client_id=client_id,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                limit_ip=limit_ip,
                expiry_time=expiry_time,
                enable=enable,
                protocol=protocol,
            )

            if result:
                await logger.info(
                    f"HTTP: клиент {client_id} успешно добавлен на порт {port} "
                    f"сервера {self._server.server_ip}"
                )
                return True

        except HttpServerUnavailableError as e:
            await logger.warning(
                f"HTTP недоступен для {self._server.server_ip}, пробуем SSH: {e}"
            )
        except Exception as e:
            await logger.warning(
                f"HTTP ошибка при добавлении клиента для {self._server.server_ip}: {e}"
            )

        # Fallback на SSH
        try:
            ssh_client = self._get_ssh_client()
            result = await ssh_client.add_client(
                port=port,
                client_id=client_id,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                limit_ip=limit_ip,
                expiry_time=expiry_time,
                enable=enable,
            )

            if result:
                await logger.info(
                    f"SSH: клиент {client_id} успешно добавлен на порт {port} "
                    f"сервера {self._server.server_ip}"
                )
                return True

        except Exception as e:
            await logger.error(
                f"SSH ошибка при добавлении клиента для {self._server.server_ip}: {e}"
            )

        return False

    async def update_client_enable(
        self,
        port: int,
        client_id: str,
        enable: bool,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 1,
    ) -> bool:
        """
        Обновляет статус включения/выключения клиента (сначала HTTP, потом SSH)

        Args:
            port: Порт инбаунда
            client_id: UUID клиента
            enable: True для включения, False для выключения
            email: Email клиента
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов

        Returns:
            True если статус успешно обновлен
        """
        # Попытка через HTTP
        try:
            http_client = self._get_http_client()
            inbound = await http_client.get_inbound_by_port(port)
            if not inbound:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не найден")

            inbound_id = inbound.get("id")
            if not inbound_id:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не содержит ID")
            protocol = (inbound.get("protocol") or "vless").strip().lower()

            result = await http_client.update_client_enable(
                inbound_id=inbound_id,
                client_id=client_id,
                enable=enable,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                limit_ip=limit_ip,
                protocol=protocol,
            )

            if result:
                await logger.info(
                    f"HTTP: статус клиента {client_id} успешно обновлен (enable={enable}) "
                    f"на порт {port} сервера {self._server.server_ip}"
                )
                return True

        except HttpServerUnavailableError as e:
            await logger.warning(
                f"HTTP недоступен для {self._server.server_ip}, пробуем SSH: {e}"
            )
        except Exception as e:
            await logger.warning(
                f"HTTP ошибка при обновлении статуса клиента для {self._server.server_ip}: {e}"
            )

        # Fallback на SSH
        try:
            ssh_client = self._get_ssh_client()
            result = await ssh_client.update_client_enable(
                port=port,
                client_id=client_id,
                enable=enable,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                limit_ip=limit_ip,
            )

            if result:
                await logger.info(
                    f"SSH: статус клиента {client_id} успешно обновлен (enable={enable}) "
                    f"на порт {port} сервера {self._server.server_ip}"
                )
                return True

        except Exception as e:
            await logger.error(
                f"SSH ошибка при обновлении статуса клиента для {self._server.server_ip}: {e}"
            )

        return False

    async def close(self) -> None:
        """
        Отпускает ссылки на клиентов. HTTP-клиент из кэша не закрываем —
        он переиспользуется с уже сохранёнными куками до истечения TTL.
        """
        self._http_client = None
        self._ssh_client = None
