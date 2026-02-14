"""Адаптер для работы с 3x-ui панелью через старую SSH API"""
import json

from handlers.services.key_create import BaseKeyManager, ServerUnavailableError as SSHServerUnavailableError
from logger.logging_config import logger


class XuiPanelSshClient:
    """Адаптер для работы с 3x-ui панелью через SSH туннель (старая API)"""

    def __init__(self, server_ip: str):
        """
        Инициализирует SSH клиент

        Args:
            server_ip: IP адрес сервера
        """
        self._server_ip = server_ip
        self._base_manager = BaseKeyManager(server_ip)

    async def check_reachable(self) -> bool:
        """
        Проверяет доступность панели через SSH (используется только как fallback после HTTP).
        Returns:
            True если удалось получить cookies через SSH туннель
        """
        cookies = await self._base_manager._get_ssh_session_cookie()
        return cookies is not None

    async def get_inbound_by_port(self, port: int) -> dict | None:
        """
        Получает инбаунд по порту через SSH туннель

        Args:
            port: Порт инбаунда

        Returns:
            Словарь с данными инбаунда или None если не найден
        """
        try:
            inbounds_data = await self._base_manager.get_inbounds()
            if inbounds_data and inbounds_data.get("success"):
                for inbound in inbounds_data.get("obj", []):
                    if inbound.get("port") == port:
                        await logger.info(
                            f"SSH найден инбаунд с портом {port} для {self._server_ip}, ID: {inbound['id']}"
                        )
                        return inbound
            return None
        except Exception as e:
            await logger.error(f"SSH ошибка получения инбаунда по порту {port} для {self._server_ip}", e)
            return None

    async def add_client(
        self,
        port: int,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 1,
        expiry_time: int = 0,
        enable: bool = True,
    ) -> bool:
        """
        Добавляет клиента в инбаунд через SSH туннель

        Args:
            port: Порт инбаунда
            client_id: UUID клиента
            email: Email клиента (не используется в старой API, но нужен для совместимости)
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов (не используется в старой API)
            expiry_time: Время истечения (не используется в старой API)
            enable: Включен ли клиент (не используется в старой API)

        Returns:
            True если клиент успешно добавлен
        """
        try:
            # Для старой API нужно получить или создать инбаунд с нужным портом
            # Если порт 443, используем существующий метод get_or_create_port_443_inbound
            # Для других портов пытаемся найти существующий инбаунд
            if port == 443:
                inbound = await self._base_manager.get_or_create_port_443_inbound()
            else:
                inbound = await self.get_inbound_by_port(port)
                if not inbound:
                    await logger.warning(
                        f"SSH инбаунд с портом {port} не найден для {self._server_ip}, "
                        f"создание инбаундов через SSH поддерживается только для порта 443"
                    )
                    return False

            inbound_id = inbound.get("id")
            if not inbound_id:
                await logger.error(f"SSH инбаунд с портом {port} не содержит ID для {self._server_ip}", None)
                return False

            # Используем существующий метод add_client_to_inbound
            client_uuid, email_result, url_config = await self._base_manager.add_client_to_inbound(
                tg_id=tg_id,
                sub_id=sub_id,
                client_id=client_id
            )

            if client_uuid is not None:
                await logger.info(
                    f"SSH клиент {client_id} успешно добавлен в инбаунд {inbound_id} "
                    f"(порт {port}) на {self._server_ip}"
                )
                return True
            else:
                await logger.error(f"SSH не удалось добавить клиента {client_id} на {self._server_ip}", None)
                return False

        except Exception as e:
            await logger.error(f"SSH исключение при добавлении клиента {client_id} на {self._server_ip}", e)
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
        Обновляет статус включения/выключения клиента через SSH туннель

        Args:
            port: Порт инбаунда
            client_id: UUID клиента
            enable: True для включения, False для выключения
            email: Email клиента (не используется)
            tg_id: Telegram ID пользователя
            sub_id: ID подписки (encoded)
            limit_ip: Лимит IP адресов (не используется)

        Returns:
            True если статус успешно обновлен
        """
        try:
            # Для старой API используем существующий метод update_key_enable
            # Он работает только с портом 443, но мы можем попробовать для других портов
            result = await self._base_manager.update_key_enable(
                user_id=int(tg_id),
                sub_id=sub_id,
                status=enable,
                client_id=client_id
            )

            if result:
                await logger.info(
                    f"SSH статус клиента {client_id} успешно обновлен (enable={enable}) "
                    f"на {self._server_ip}"
                )
                return True
            else:
                await logger.warning(f"SSH не удалось обновить статус клиента {client_id} на {self._server_ip}")
                return False

        except Exception as e:
            await logger.error(f"SSH исключение при обновлении статуса клиента {client_id} на {self._server_ip}", e)
            return False
