"""
Получение подписки (ключей) с серверов по HTTPS.
Таймаут 3 секунды. Поддержка sub_port из БД.
"""
import asyncio
import base64
import re
import logging
from typing import Optional
from urllib.parse import unquote

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


# Таймаут для внешней подписки (секунды)
EXTERNAL_SUB_TIMEOUT = 3

# Страны/города, которые не включаем во внешнюю подписку (резерв)
EXTERNAL_EXCLUDED_NAMES = (
    "Италия", "Украина", "Румыния", "Израиль", "Чехия", "Армения", "Милан"
)

# Регулярка: только цифры (убираем из токенов)
_RE_DIGITS = re.compile(r"\d+")


def _decode_fragment(name: str) -> str:
    """Декодирует fragment из URL (%D0%A3... -> буквы), иначе исключения не найдутся."""
    try:
        return unquote(name)
    except Exception:
        return name


def _is_excluded_reserve_name(name: str) -> bool:
    """True, если в названии есть исключённая страна/город (Италия, Украина и т.д.)."""
    name_decoded = _decode_fragment(name)
    name_lower = name_decoded.lower()
    for excluded in EXTERNAL_EXCLUDED_NAMES:
        if excluded.lower() in name_lower:
            return True
    return False


def _first_two_tokens_no_digits(name: str) -> str:
    """Первые два токена (по пробелу), из каждого убраны цифры. Нумерацию ставим свою потом."""
    name_decoded = _decode_fragment(name)
    tokens = name_decoded.split()
    first_two = tokens[:2]
    # Убираем цифры из каждого токена (чтобы не тащить их номер)
    cleaned = [_RE_DIGITS.sub("", t).strip() for t in first_two]
    cleaned = [t for t in cleaned if t]
    return " ".join(cleaned)


async def fetch_external_subscription_keys(url: str) -> list[str]:
    """
    Загружает подписку с внешнего URL (ожидает base64 строку в теле ответа).
    Таймаут 3 секунды. Возвращает список строк-ключей (vless://, vmess:// и т.д.);
    при таймауте или ошибке возвращает пустой список.
    """
    timeout = ClientTimeout(connect=EXTERNAL_SUB_TIMEOUT, total=EXTERNAL_SUB_TIMEOUT)
    keys = []
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                raw = (await resp.text()).strip()
    except (asyncio.TimeoutError, aiohttp.ClientError, OSError) as e:
        logger.warning("Внешняя подписка %s: таймаут или ошибка (%s)", url, type(e).__name__)
        return []

    try:
        decoded = base64.b64decode(raw).decode("utf-8")
    except Exception:
        decoded = raw

    # Группируем по стране/региону (base); нумеруем внутри каждой группы: США 1, США 2, Франция 1, ...
    by_base: dict[str, list[str]] = {}
    for line in decoded.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "://" not in line:
            continue
        if "#" not in line:
            by_base.setdefault("Резерв", []).append(line)
            continue
        before_hash, _, name = line.partition("#")
        if _is_excluded_reserve_name(name):
            continue
        base = _first_two_tokens_no_digits(name)
        if not base:
            base = "Резерв"
        by_base.setdefault(base, []).append(before_hash)

    for base, before_hashes in by_base.items():
        for i, before_hash in enumerate(before_hashes, start=1):
            label = f"РЕЗЕРВ {base} {i}".strip()
            keys.append(f"{before_hash}#{label}")
    return keys
