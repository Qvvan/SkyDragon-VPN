"""Low-level httpx wrapper for 3x-ui panel — session, cookie auth, retries."""
from __future__ import annotations

import httpx
from loguru import logger


class XuiAuthError(Exception):
    """Raised when authentication to 3x-ui panel fails permanently."""


class XuiHttpClient:
    """
    Cookie-based httpx session for one 3x-ui panel instance.

    Auth flow: POST /login → session cookie saved by httpx CookieJar.
    On 401/403 re-authenticates once before failing.
    """

    __slots__ = (
        "_base_url",
        "_login",
        "_password",
        "_timeout",
        "_client",
        "_authenticated",
    )

    def __init__(
        self,
        base_url: str,
        login: str,
        password: str,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._login = login
        self._password = password
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._authenticated = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def get(self, path: str) -> dict:
        return await self._request("GET", path)

    async def post(self, path: str, json: dict | None = None) -> dict:
        return await self._request("POST", path, json=json)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._authenticated = False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=False,
                timeout=self._timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "application/json, text/plain, */*",
                },
            )
        return self._client

    async def _authenticate(self) -> None:
        client = self._ensure_client()
        url = f"{self._base_url}/login"
        try:
            resp = await client.post(url, data={"username": self._login, "password": self._password})
        except httpx.TransportError as exc:
            raise XuiAuthError(f"Network error authenticating {self._base_url}: {exc}") from exc

        if resp.status_code != 200:
            raise XuiAuthError(f"Auth failed for {self._base_url}: HTTP {resp.status_code}")

        body = resp.json()
        if not body.get("success"):
            raise XuiAuthError(
                f"Auth rejected for {self._base_url}: {body.get('msg', 'unknown')}"
            )
        self._authenticated = True
        logger.debug("xui auth ok: {}", self._base_url)

    async def _request(self, method: str, path: str, json: dict | None = None) -> dict:
        if not self._authenticated:
            await self._authenticate()

        client = self._ensure_client()
        url = f"{self._base_url}{path}"

        try:
            resp = await client.request(method, url, json=json)
        except httpx.TransportError as exc:
            raise RuntimeError(f"Network error {method} {url}: {exc}") from exc

        if resp.status_code in (401, 403):
            # Session expired — re-authenticate once and retry
            logger.debug("xui session expired ({}), re-authing {}", resp.status_code, self._base_url)
            self._authenticated = False
            await self._authenticate()
            try:
                resp = await client.request(method, url, json=json)
            except httpx.TransportError as exc:
                raise RuntimeError(f"Network error {method} {url} (retry): {exc}") from exc

        resp.raise_for_status()
        return resp.json()
