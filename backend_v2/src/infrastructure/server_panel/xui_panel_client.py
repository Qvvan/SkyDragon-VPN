"""3x-ui implementation of IServerPanelClient."""
from __future__ import annotations

import json

from loguru import logger

from src.domain.entities.server import ServerNode
from src.domain.services.key_identifier import client_uuid, sub_email_prefix
from src.infrastructure.xui.api_client import XuiApiClient
from src.infrastructure.xui.http_client import XuiHttpClient
from src.interfaces.clients.server_panel.client import IServerPanelClient


class XuiServerPanelClient(IServerPanelClient):
    """
    Manages VPN clients on 3x-ui panel servers.

    One XuiApiClient (with its cookie session) is cached per server
    (keyed by server_ip:panel_port) and reused across calls to avoid
    re-authentication on every operation.
    """

    __slots__ = ("_login", "_password", "_key_secret", "_timeout", "_api_clients")

    def __init__(
        self,
        login: str,
        password: str,
        key_secret: str,
        timeout: float = 10.0,
    ) -> None:
        self._login = login
        self._password = password
        self._key_secret = key_secret
        self._timeout = timeout
        self._api_clients: dict[str, XuiApiClient] = {}

    # ------------------------------------------------------------------
    # IServerPanelClient
    # ------------------------------------------------------------------

    async def provision(
        self,
        server: ServerNode,
        user_id: int,
        subscription_id: str,
        action: str,
        days: int | None = None,
    ) -> None:
        """
        Execute action on all ports of the given server.
        Raises RuntimeError if any port fails.
        """
        api = self._get_api_client(server)
        ports = _parse_ports(server.available_ports)

        # Fetch all inbounds once — avoids N HTTP calls for N ports
        inbounds_by_port: dict[int, dict] = {
            inb["port"]: inb
            for inb in await api.get_inbounds()
            if "port" in inb
        }

        cid = client_uuid(user_id, subscription_id)
        prefix = sub_email_prefix(user_id, subscription_id, self._key_secret)
        tg_id = str(user_id)

        errors: list[str] = []
        for port in ports:
            inbound = inbounds_by_port.get(port)
            if inbound is None:
                errors.append(f"port {port}: inbound not found on {server.server_ip}")
                continue
            try:
                await self._apply(
                    api=api,
                    action=action,
                    inbound=inbound,
                    client_id=cid,
                    email=f"{prefix}_port{port}",
                    tg_id=tg_id,
                    sub_id=prefix,
                    days=days,
                )
                logger.debug(
                    "xui.provision ok | server={} port={} action={} user={} sub={}",
                    server.server_ip, port, action, user_id, subscription_id,
                )
            except Exception as exc:
                errors.append(f"port {port}: {exc}")

        if errors:
            raise RuntimeError(
                f"provision({action}) on {server.server_ip} failed: {'; '.join(errors)}"
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_api_client(self, server: ServerNode) -> XuiApiClient:
        panel_port = server.panel_port or 443
        url_secret = (server.url_secret or "").strip("/")
        base_path = f"/{url_secret}" if url_secret else ""
        base_url = f"https://{server.server_ip}:{panel_port}{base_path}"
        cache_key = f"{server.server_ip}:{panel_port}"

        if cache_key not in self._api_clients:
            http = XuiHttpClient(
                base_url=base_url,
                login=self._login,
                password=self._password,
                timeout=self._timeout,
            )
            self._api_clients[cache_key] = XuiApiClient(http)
        return self._api_clients[cache_key]

    async def _apply(
        self,
        api: XuiApiClient,
        action: str,
        inbound: dict,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        days: int | None,
    ) -> None:
        inbound_id: int = inbound["id"]
        protocol: str = (inbound.get("protocol") or "vless").strip().lower()
        exists = _client_exists(inbound, email)

        if action == "create":
            await api.add_client(
                inbound_id=inbound_id,
                protocol=protocol,
                client_id=client_id,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                expiry_days=days or 0,
            )

        elif action in ("update", "enable"):
            if exists:
                await api.update_client(
                    inbound_id=inbound_id,
                    protocol=protocol,
                    client_id=client_id,
                    email=email,
                    tg_id=tg_id,
                    sub_id=sub_id,
                    enable=True,
                )
            else:
                # Client missing — create it (idempotent fallback)
                await api.add_client(
                    inbound_id=inbound_id,
                    protocol=protocol,
                    client_id=client_id,
                    email=email,
                    tg_id=tg_id,
                    sub_id=sub_id,
                    expiry_days=days or 0,
                )

        elif action == "disable":
            if not exists:
                return  # Nothing to disable — idempotent success
            await api.update_client(
                inbound_id=inbound_id,
                protocol=protocol,
                client_id=client_id,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                enable=False,
            )

        elif action == "delete":
            if not exists:
                return  # Already gone — idempotent success
            await api.delete_client(inbound_id=inbound_id, client_id=client_id)

        else:
            raise ValueError(f"Unknown action: {action!r}")


# ------------------------------------------------------------------
# Module-level helpers (no state, pure functions)
# ------------------------------------------------------------------

def _parse_ports(available_ports: str | None) -> list[int]:
    """Parse comma-separated port list. Falls back to [443] if empty."""
    if not available_ports:
        return [443]
    ports = [int(p.strip()) for p in str(available_ports).split(",") if p.strip().isdigit()]
    return ports or [443]


def _client_exists(inbound: dict, email: str) -> bool:
    """Check if a client with the given email is present in inbound.settings.clients."""
    settings_raw = inbound.get("settings")
    if not settings_raw:
        return False
    try:
        settings = json.loads(settings_raw) if isinstance(settings_raw, str) else settings_raw
        return any(
            isinstance(c, dict) and c.get("email") == email
            for c in settings.get("clients", [])
        )
    except (json.JSONDecodeError, TypeError):
        return False
