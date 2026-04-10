import base64
import re
from urllib.parse import unquote

import httpx

from src.domain.entities.server import ServerNode
from src.interfaces.clients.subscription.client import ISubscriptionClient


class HttpSubscriptionClient(ISubscriptionClient):
    __slots__ = ("_timeout_seconds", "_default_sub_port", "_excluded_names")

    def __init__(
        self,
        timeout_seconds: int = 3,
        default_sub_port: int = 2096,
        excluded_names: tuple[str, ...] = ("Италия", "Украина", "Румыния", "Израиль", "Чехия", "Армения", "Милан"),
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._default_sub_port = default_sub_port
        self._excluded_names = excluded_names

    async def fetch_server_subscription(self, server: ServerNode, encoded_sub_id: str) -> str | None:
        port = server.sub_port if server.sub_port is not None else self._default_sub_port
        url = f"https://{server.server_ip}:{port}/sub/{encoded_sub_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds, verify=False) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return None
                return response.text.strip()
        except httpx.HTTPError:
            return None

    async def fetch_external_subscription_keys(self, url: str) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return []
                raw = response.text.strip()
        except httpx.HTTPError:
            return []

        try:
            decoded = base64.b64decode(raw).decode("utf-8")
        except Exception:
            decoded = raw

        keys: list[str] = []
        for line in decoded.strip().split("\n"):
            normalized = line.strip()
            if not normalized or normalized.startswith("#") or "://" not in normalized:
                continue
            if "#" in normalized:
                uri, _, raw_name = normalized.partition("#")
                name = unquote(raw_name)
                if any(excluded.lower() in name.lower() for excluded in self._excluded_names):
                    continue
                cleaned_name = re.sub(r"\s+", " ", re.sub(r"\d+", "", name)).strip() or "Резерв"
                keys.append(f"{uri}#РЕЗЕРВ {cleaned_name}")
            else:
                keys.append(normalized)
        return keys
