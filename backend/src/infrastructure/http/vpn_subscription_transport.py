"""
HTTPS-загрузка подписок с панелей и внешних URL (aiohttp).
Единственное место с aiohttp для этого сценария.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import re
from urllib.parse import unquote

import aiohttp
from aiohttp import ClientTimeout

from domain.entities.server import Server
from interfaces.clients.vpn_subscription_transport import IVpnSubscriptionTransport

SUB_TIMEOUT = 3
EXTERNAL_SUB_TIMEOUT = 3
EXTERNAL_EXCLUDED_NAMES = (
    "Италия", "Украина", "Румыния", "Израиль", "Чехия", "Армения", "Милан"
)
_RE_DIGITS = re.compile(r"\d+")
_RE_WHYPN = re.compile(r"\bwhypn\b", re.IGNORECASE)
_RE_EMOJI = re.compile(
    r"[*\u2600-\u26FF\u2700-\u27BF\U0001F1E0-\U0001F1FF\U0001F300-\U0001F9FF\uFE00-\uFE0F]+",
    re.UNICODE,
)
_RE_RESERVE = re.compile(r"\s*\(?\s*[Зз]апасной\s*\)?\s*", re.IGNORECASE)

logger = logging.getLogger(__name__)


def _sub_port(server: Server, default_sub_port: int) -> int:
    p = server.sub_port
    return int(p) if p is not None else default_sub_port


class AiohttpVpnSubscriptionTransport(IVpnSubscriptionTransport):
    async def fetch_panel_subscription(
        self,
        server: Server,
        encoded_sub_id: str,
        default_sub_port: int,
    ) -> str | None:
        server_ip = server.server_ip
        port = _sub_port(server, default_sub_port)
        url = f"https://{server_ip}:{port}/sub/{encoded_sub_id}"
        timeout = ClientTimeout(connect=SUB_TIMEOUT, total=SUB_TIMEOUT)
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(url, ssl=False) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Подписка: HTTP %s:%s статус %s",
                            server_ip, port, resp.status,
                        )
                        return None
                    return (await resp.text()).strip()
        except asyncio.TimeoutError:
            logger.warning("Подписка: таймаут %s:%s", server_ip, port)
            return None
        except (aiohttp.ClientError, OSError) as e:
            logger.warning(
                "Подписка: ошибка %s:%s (%s)",
                server_ip, port, type(e).__name__,
            )
            return None

    async def fetch_external_subscription_keys(self, url: str) -> list[str]:
        timeout = ClientTimeout(connect=EXTERNAL_SUB_TIMEOUT, total=EXTERNAL_SUB_TIMEOUT)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return []
                    raw = (await resp.text()).strip()
        except (asyncio.TimeoutError, aiohttp.ClientError, OSError) as e:
            logger.warning("Внешняя подписка %s: %s", url, type(e).__name__)
            return []

        try:
            decoded = base64.b64decode(raw).decode("utf-8")
        except Exception:
            decoded = raw

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
            name = _normalize_external_name(name)
            if _is_excluded_reserve_name(name):
                continue
            base = _first_two_tokens_no_digits(name)
            if not base:
                base = "Резерв"
            by_base.setdefault(base, []).append(before_hash)

        keys: list[str] = []
        for base, before_hashes in by_base.items():
            for i, before_hash in enumerate(before_hashes, start=1):
                label = f"РЕЗЕРВ {base} {i}".strip()
                keys.append(f"{before_hash}#{label}")
        return keys


def _decode_fragment(name: str) -> str:
    try:
        return unquote(name)
    except Exception:
        return name


def _normalize_external_name(name: str) -> str:
    s = _decode_fragment(name)
    s = _RE_WHYPN.sub(" ", s)
    s = _RE_RESERVE.sub(" ", s)
    s = _RE_EMOJI.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_excluded_reserve_name(name: str) -> bool:
    name_decoded = _decode_fragment(name)
    name_lower = name_decoded.lower()
    for excluded in EXTERNAL_EXCLUDED_NAMES:
        if excluded.lower() in name_lower:
            return True
    return False


def _first_two_tokens_no_digits(name: str) -> str:
    name_decoded = _decode_fragment(name)
    tokens = name_decoded.split()
    first_two = tokens[:2]
    cleaned = [_RE_DIGITS.sub("", t).strip() for t in first_two]
    cleaned = [t for t in cleaned if t]
    return " ".join(cleaned)
