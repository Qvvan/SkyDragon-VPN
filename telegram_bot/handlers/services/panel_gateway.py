"""Единый фасад для работы с панелью 3x-ui через HTTPS API."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp

from config_data.config import LOGIN_X_UI_PANEL, PASSWORD_X_UI_PANEL, MY_SECRET_URL, PORT_X_UI
from handlers.services.xui_http_client import XuiPanelHttpClient, ServerUnavailableError as HttpServerUnavailableError
from logger.logging_config import logger
from models.models import Servers

# Кэш HTTP-клиентов с куками: ключ = (server_ip, panel_port, base_path), значение = (client, timestamp)
_http_client_cache: dict[str, tuple[XuiPanelHttpClient, float]] = {}
HTTP_CACHE_TTL_SEC = 30 * 60  # 30 минут


def _server_cache_key(server: Servers) -> str:
    """Ключ кэша по данным сервера."""
    port = server.panel_port or PORT_X_UI or 443
    path = (server.url_secret or MY_SECRET_URL or "").strip("/")
    return f"{server.server_ip}:{port}:{path}"


class PanelGateway:
    """Единый фасад для работы с панелью 3x-ui по HTTPS."""

    def __init__(self, server: Servers):
        """
        Инициализирует gateway для работы с сервером

        Args:
            server: Объект сервера из БД
        """
        self._server = server
        self._http_client: Optional[XuiPanelHttpClient] = None

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

    async def ping_only(self) -> bool:
        """
        Простая проверка «жив ли сервер»: один GET на корень, таймаут 5 сек.
        Любой ответ (в т.ч. 404) — считаем доступным.
        """
        server_url = self._get_server_url()
        base_path = self._get_base_path()
        ping_client = XuiPanelHttpClient(
            server_url=server_url,
            base_path=base_path,
            login=LOGIN_X_UI_PANEL,
            password=PASSWORD_X_UI_PANEL,
            connect_timeout=5,
            total_timeout=5,
            max_retries=1,
        )
        try:
            return await ping_client.ping()
        finally:
            await ping_client.close()

    async def check_reachable(self) -> bool:
        """
        Проверяет доступность панели по HTTPS (с авторизацией).
        """
        try:
            http_client = self._get_http_client()
            if await http_client._authenticate():
                await logger.info(
                    f"check_reachable: {self._server.server_ip} доступен по HTTPS"
                )
                return True
            await logger.warning(
                f"check_reachable: аутентификация вернула False для {self._server.server_ip}"
            )
        except Exception as e:
            await logger.warning(
                f"check_reachable: ошибка для {self._server.server_ip}: {type(e).__name__}: {e}"
            )
        return False

    async def get_online_users(self) -> dict | None:
        """
        Получает список онлайн пользователей по HTTPS.
        Returns:
            Словарь с полем success и obj (список client_id) или None при ошибке.
        """
        try:
            http_client = self._get_http_client()
            return await http_client.get_online_users()
        except Exception as e:
            await logger.warning(
                f"get_online_users: ошибка для {self._server.server_ip}: {type(e).__name__}: {e}"
            )
        return None

    async def get_client_ips(self, client_id: str) -> list[str]:
        """
        Получает список IP адресов для онлайн-клиента на этом сервере.
        """
        try:
            http_client = self._get_http_client()
            return await http_client.get_client_ips(client_id)
        except Exception as e:
            await logger.warning(
                f"get_client_ips: ошибка для {self._server.server_ip}, client_id={client_id[:40]}: {e}"
            )
        return []

    async def get_inbound_by_port(self, port: int) -> dict | None:
        """
        Получает инбаунд по порту по HTTPS.

        Args:
            port: Порт инбаунда

        Returns:
            Словарь с данными инбаунда или None если не найден
        """
        try:
            http_client = self._get_http_client()
            inbound = await http_client.get_inbound_by_port(port)
            if inbound:
                await logger.info(
                    f"Инбаунд с портом {port} найден на {self._server.server_ip}"
                )
            return inbound
        except Exception as e:
            await logger.warning(
                f"Ошибка при получении инбаунда для {self._server.server_ip}: {e}"
            )
        return None

    def _client_exists_in_inbound(self, inbound: dict, email: str) -> bool:
        """
        Проверяет, есть ли в инбаунде клиент с указанным email.

        Args:
            inbound: Словарь инбаунда (с полем settings)
            email: Email клиента

        Returns:
            True если клиент найден в settings.clients
        """
        settings_raw = inbound.get("settings")
        if not settings_raw:
            return False
        try:
            settings = json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
            if not isinstance(settings, dict):
                return False
            for c in settings.get("clients", []):
                if isinstance(c, dict) and c.get("email") == email:
                    return True
        except (json.JSONDecodeError, TypeError):
            pass
        return False

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
        Добавляет клиента в инбаунд по HTTPS

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
                    f"Клиент {client_id} успешно добавлен на порт {port} "
                    f"сервера {self._server.server_ip}"
                )
                return True

        except HttpServerUnavailableError as e:
            await logger.warning(
                f"HTTPS недоступен для {self._server.server_ip}: {e}"
            )
        except Exception as e:
            await logger.warning(
                f"Ошибка при добавлении клиента для {self._server.server_ip}: {e}"
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
        Обновляет статус включения/выключения клиента по HTTPS.
        Сначала проверяет наличие ключа в инбаунде:
        - Включение (enable=True): если ключ есть — обновляет, если нет — создаёт.
        - Выключение (enable=False): если ключа нет — ничего не делает, если есть — выключает.

        Args:
            port: Порт инбаунда
            client_id: UUID клиента
            enable: True для включения, False для выключения
            email: Email клиента
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов

        Returns:
            True если операция успешна (обновлён/создан/пропущен при выключении несуществующего)
        """
        try:
            http_client = self._get_http_client()
            inbound = await http_client.get_inbound_by_port(port)
            if not inbound:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не найден")

            inbound_id = inbound.get("id")
            if not inbound_id:
                raise HttpServerUnavailableError(f"Инбаунд с портом {port} не содержит ID")
            protocol = (inbound.get("protocol") or "vless").strip().lower()

            client_exists = self._client_exists_in_inbound(inbound, email)

            if enable:
                if client_exists:
                    result = await http_client.update_client_enable(
                        inbound_id=inbound_id,
                        client_id=client_id,
                        enable=True,
                        email=email,
                        tg_id=tg_id,
                        sub_id=sub_id,
                        limit_ip=limit_ip,
                        protocol=protocol,
                    )
                    if result:
                        await logger.info(
                            f"Статус клиента {client_id} успешно обновлен (включён) "
                            f"на порт {port} сервера {self._server.server_ip}"
                        )
                    return result
                else:
                    result = await self.add_client(
                        port=port,
                        client_id=client_id,
                        email=email,
                        tg_id=tg_id,
                        sub_id=sub_id,
                        limit_ip=limit_ip,
                        expiry_days=0,
                        enable=True,
                    )
                    return result
            else:
                if not client_exists:
                    await logger.info(
                        f"Ключ в инбаунде порт {port} ({self._server.server_ip}) не найден, "
                        f"выключение не требуется"
                    )
                    return True
                result = await http_client.update_client_enable(
                    inbound_id=inbound_id,
                    client_id=client_id,
                    enable=False,
                    email=email,
                    tg_id=tg_id,
                    sub_id=sub_id,
                    limit_ip=limit_ip,
                    protocol=protocol,
                )
                if result:
                    await logger.info(
                        f"Статус клиента {client_id} успешно обновлен (выключен) "
                        f"на порт {port} сервера {self._server.server_ip}"
                    )
                return result

        except HttpServerUnavailableError as e:
            await logger.warning(
                f"HTTPS недоступен для {self._server.server_ip}: {e}"
            )
        except Exception as e:
            await logger.warning(
                f"Ошибка при обновлении статуса клиента для {self._server.server_ip}: {e}"
            )

        return False

    async def close(self) -> None:
        """
        Отпускает ссылки на клиентов. HTTP-клиент из кэша не закрываем —
        он переиспользуется с уже сохранёнными куками до истечения TTL.
        """
        self._http_client = None
