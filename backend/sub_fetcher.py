"""
Получение подписки (ключей) с серверов по HTTPS.
Таймаут 3 секунды. Поддержка sub_port из БД.
"""
import asyncio
import logging
from typing import Optional

import aiohttp
from aiohttp import ClientTimeout

from cfg.config import SUB_PORT
from models.models import Servers

SUB_TIMEOUT = 3
logger = logging.getLogger(__name__)


def _sub_port(server: Servers) -> int:
    """Порт, на котором на сервере отдаётся /sub/ (обычно 2096, не panel_port 14880)."""
    p = getattr(server, "sub_port", None)
    return int(p) if p is not None else SUB_PORT


async def _fetch_via_http(server_ip: str, port: int, encoded_sub_id: str) -> Optional[str]:
    """Один GET по HTTPS: https://server_ip:port/sub/encoded_id (без url_secret в пути)."""
    url = f"https://{server_ip}:{port}/sub/{encoded_sub_id}"
    timeout = ClientTimeout(connect=SUB_TIMEOUT, total=SUB_TIMEOUT)
    logger.info("Подписка: пробуем HTTP для %s:%s (таймаут %s с)", server_ip, port, SUB_TIMEOUT)
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Подписка: HTTP для %s:%s вернул статус %s",
                        server_ip, port, resp.status,
                    )
                    return None
                logger.info("Подписка: получено по HTTP с %s:%s", server_ip, port)
                return (await resp.text()).strip()
    except asyncio.TimeoutError:
        logger.warning(
            "Подписка: HTTPS таймаут для %s:%s (%s с)",
            server_ip, port, SUB_TIMEOUT,
        )
        return None
    except (aiohttp.ClientError, OSError) as e:
        logger.warning(
            "Подписка: HTTPS недоступен для %s:%s (%s)",
            server_ip, port, type(e).__name__,
        )
        return None


async def get_sub_from_server(server: Servers, encoded_sub_id: str) -> Optional[str]:
    """
    Получает подписку (base64 ключей) с одного сервера по HTTPS.
    URL: https://server_ip:sub_port/sub/encoded_id (sub_port обычно 2096). Таймаут 3 сек.
    """
    server_ip = server.server_ip
    port = _sub_port(server)
    return await _fetch_via_http(server_ip, port, encoded_sub_id)
