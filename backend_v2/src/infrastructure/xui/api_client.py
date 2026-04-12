"""Typed 3x-ui REST API client — operations on inbounds and clients."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from src.infrastructure.xui.http_client import XuiHttpClient


def _build_client_settings(
    protocol: str,
    client_id: str,
    email: str,
    tg_id: str,
    sub_id: str,
    limit_ip: int,
    expiry_time: int,
    enable: bool,
) -> dict[str, Any]:
    """
    Build the client object for settings.clients.
    VLESS/VMess: uses 'id' + 'flow'.
    Trojan: uses 'password' instead of 'id', no 'flow'.
    """
    proto = (protocol or "vless").strip().lower()
    base: dict[str, Any] = {
        "email": email,
        "limitIp": limit_ip,
        "totalGB": 0,
        "expiryTime": expiry_time,
        "enable": enable,
        "tgId": tg_id,
        "subId": sub_id,
        "comment": f"TgID: {tg_id}",
        "reset": 0,
    }
    if proto == "trojan":
        return {"password": client_id, **base}
    return {"id": client_id, "flow": "xtls-rprx-vision", **base}


class XuiApiClient:
    """
    Typed wrapper around XuiHttpClient.
    Each method maps to one 3x-ui REST endpoint.
    Idempotency: add_client treats 'Duplicate email' as success.
    """

    __slots__ = ("_http",)

    def __init__(self, http: XuiHttpClient) -> None:
        self._http = http

    async def get_inbounds(self) -> list[dict]:
        """GET /panel/api/inbounds/list → list of inbound dicts."""
        resp = await self._http.get("/panel/api/inbounds/list")
        if not resp.get("success"):
            return []
        return resp.get("obj") or []

    async def add_client(
        self,
        inbound_id: int,
        protocol: str,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 2,
        expiry_days: int = 0,
    ) -> None:
        """
        POST /panel/api/inbounds/addClient
        Idempotent: 'Duplicate email' response is treated as success.
        """
        expiry_time = 0
        if expiry_days > 0:
            expiry_time = int(
                (datetime.now(timezone.utc) + timedelta(days=expiry_days)).timestamp() * 1000
            )
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [_build_client_settings(
                    protocol, client_id, email, tg_id, sub_id, limit_ip, expiry_time, True,
                )]
            }),
        }
        resp = await self._http.post("/panel/api/inbounds/addClient", json=payload)
        if resp.get("success"):
            return
        msg: str = resp.get("msg") or ""
        if "duplicate" in msg.lower():
            return  # already exists — idempotent
        raise RuntimeError(f"add_client inbound={inbound_id}: {msg}")

    async def update_client(
        self,
        inbound_id: int,
        protocol: str,
        client_id: str,
        email: str,
        tg_id: str,
        sub_id: str,
        limit_ip: int = 2,
        enable: bool = True,
    ) -> None:
        """POST /panel/api/inbounds/updateClient/{client_id}"""
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [_build_client_settings(
                    protocol, client_id, email, tg_id, sub_id, limit_ip, 0, enable,
                )]
            }),
        }
        resp = await self._http.post(f"/panel/api/inbounds/updateClient/{client_id}", json=payload)
        if not resp.get("success"):
            raise RuntimeError(f"update_client client={client_id}: {resp.get('msg', '')}")

    async def delete_client(self, inbound_id: int, client_id: str) -> None:
        """POST /panel/api/inbounds/{inbound_id}/delClient/{client_id}"""
        resp = await self._http.post(f"/panel/api/inbounds/{inbound_id}/delClient/{client_id}")
        if not resp.get("success"):
            raise RuntimeError(f"delete_client client={client_id}: {resp.get('msg', '')}")

    async def close(self) -> None:
        await self._http.close()
