import asyncio
import base64
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.core.config import Config
from src.core.exceptions import NotFoundError, ValidationError
from src.domain.entities.service_plan import ServicePlan
from src.domain.entities.subscription import Subscription
from src.interfaces.clients.subscription.client import ISubscriptionClient
from src.interfaces.repositories.server import IServerRepository
from src.interfaces.repositories.service_plan import IServicePlanRepository
from src.interfaces.repositories.subscription import ISubscriptionRepository
from src.interfaces.services.token_codec import ITokenCodec

SUB_STATUS_ACTIVE = "активная"


class SubscriptionService:
    __slots__ = ("_config", "_subscription_repo", "_server_repo", "_service_repo", "_subscription_client", "_token_codec")

    def __init__(
        self,
        config: Config,
        subscription_repo: ISubscriptionRepository,
        server_repo: IServerRepository,
        service_repo: IServicePlanRepository,
        subscription_client: ISubscriptionClient,
        token_codec: ITokenCodec,
    ) -> None:
        self._config = config
        self._subscription_repo = subscription_repo
        self._server_repo = server_repo
        self._service_repo = service_repo
        self._subscription_client = subscription_client
        self._token_codec = token_codec

    def decode_user_and_sub(self, encrypted_part: str) -> tuple[int, int]:
        try:
            return self._token_codec.decrypt(encrypted_part)
        except Exception as exc:
            raise ValidationError("Invalid encryption") from exc

    async def get_subscription_content(self, encrypted_part: str, user_agent: str | None) -> tuple[bytes, dict[str, str]]:
        user_id, sub_id = self.decode_user_and_sub(encrypted_part)
        subscription = await self._subscription_repo.get_by_principal_and_subscription_id(user_id, sub_id)
        config_url = self._public_sub_url(encrypted_part)

        if subscription is None:
            body = self._build_stub_body("Подписка не найдена", state="not_found", profile_url=config_url, user_agent=user_agent)
            response_bytes = base64.b64encode(body.encode("utf-8"))
            return response_bytes, self._subscription_download_headers(config_url, "SkyDragon - Не найдена", 0, response_bytes)

        if not subscription.is_active():
            body = self._build_stub_body("ИСТЕКЛА", state="expired", profile_url=config_url, user_agent=user_agent)
            response_bytes = base64.b64encode(body.encode("utf-8"))
            return (
                response_bytes,
                self._subscription_download_headers(
                    config_url, "SkyDragon", subscription.expire_unix(), response_bytes, announce="Срок подписки истек",
                ),
            )

        encoded_sub_id = self._encode_numbers(user_id, sub_id)
        servers = await self._server_repo.list_visible()

        async def fetch_server(server) -> list[str]:
            raw = await self._subscription_client.fetch_server_subscription(server, encoded_sub_id)
            if not raw:
                return []
            return self._decode_sub_to_keys(raw, server.server_ip, server.name or server.server_ip)

        external_urls = [item.strip() for item in self._config.app.EXTERNAL_SUB_URLS.split(",") if item.strip()]
        server_tasks = [fetch_server(server) for server in servers]
        external_tasks = [self._subscription_client.fetch_external_subscription_keys(url) for url in external_urls]
        server_results = await asyncio.gather(*server_tasks) if server_tasks else []
        external_results = await asyncio.gather(*external_tasks) if external_tasks else []
        keys = [k for key_list in server_results for k in key_list] + [k for key_list in external_results for k in key_list]
        keys = [self._sanitize_proxy_uri_line(item) for item in keys]
        if not keys:
            keys = [self._stub_uri("Нет активных узлов")]

        msk_time = self._now_msk_time_str()
        renewal_hint = self._renewal_hint_for_client(user_agent)
        announce_plain = f"Обновлено {msk_time} МСК. {renewal_hint}".strip()
        body = self._build_subscription_body(keys, profile_url=config_url, announce_plain=announce_plain)
        response_bytes = base64.b64encode(body.encode("utf-8"))
        return (
            response_bytes,
            self._subscription_download_headers(
                config_url,
                "SkyDragon",
                subscription.expire_unix(),
                response_bytes,
                announce=announce_plain,
            ),
        )

    async def get_subscription_list(self, encrypted_part: str) -> dict:
        user_id, sub_id = self.decode_user_and_sub(encrypted_part)
        subscription = await self._subscription_repo.get_by_principal_and_subscription_id(user_id, sub_id)
        if not subscription:
            return {"keys": [], "servers": [], "message": "Подписка не найдена или удалена. Оформите новую в боте."}

        encoded_sub_id = self._encode_numbers(user_id, sub_id)
        servers = await self._server_repo.list_visible()
        results = []
        for server in servers:
            raw = await self._subscription_client.fetch_server_subscription(server, encoded_sub_id)
            keys = self._decode_sub_to_keys(raw, server.server_ip, server.name or server.server_ip) if raw else []
            results.append({"server_ip": server.server_ip, "name": server.name, "keys": keys})
        return {
            "keys": [k for item in results for k in item["keys"]],
            "servers": [{"server_ip": item["server_ip"], "name": item["name"]} for item in results],
        }

    async def set_auto_renewal(self, encrypted_part: str, enabled: bool) -> None:
        user_id, sub_id = self.decode_user_and_sub(encrypted_part)
        updated = await self._subscription_repo.set_auto_renewal(user_id, sub_id, enabled)
        if not updated:
            raise NotFoundError("Подписка не найдена")

    async def get_services_for_renewal(self, encrypted_part: str) -> list[ServicePlan]:
        user_id, sub_id = self.decode_user_and_sub(encrypted_part)
        subscription = await self._subscription_repo.get_by_principal_and_subscription_id(user_id, sub_id)
        if not subscription:
            return []
        return await self._service_repo.list_active()

    async def get_subscription_info(self, encrypted_part: str) -> Subscription | None:
        user_id, sub_id = self.decode_user_and_sub(encrypted_part)
        return await self._subscription_repo.get_by_principal_and_subscription_id(user_id, sub_id)

    async def list_subscriptions_for_account(self, account_id: str) -> list[Subscription]:
        return await self._subscription_repo.list_for_account_owner(account_id)

    async def list_service_plans(self) -> list[ServicePlan]:
        return await self._service_repo.list_active()

    async def set_auto_renewal_for_account(self, account_id: str, subscription_id: str, enabled: bool) -> None:
        updated = await self._subscription_repo.set_auto_renewal(account_id, subscription_id, enabled)
        if not updated:
            raise NotFoundError("Подписка не найдена")

    def _public_sub_url(self, encrypted_part: str) -> str:
        return f"{self._config.app.PUBLIC_BASE_URL.rstrip('/')}/sub/{encrypted_part}"

    @staticmethod
    def _encode_numbers(user_id: int, sub_id: int) -> str:
        return base64.b64encode(f"{user_id},{sub_id}|checksum".encode("utf-8")).decode("utf-8")

    @staticmethod
    def _decode_sub_to_keys(base64_text: str, server_ip: str, server_name: str) -> list[str]:
        try:
            decoded = base64.b64decode(base64_text).decode("utf-8")
        except Exception:
            decoded = base64_text
        keys = []
        for line in decoded.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            line = line.replace("localhost", server_ip)
            if "#" in line:
                line = line.split("#")[0] + "#" + server_name
            line = re.sub(r"&spx=[^&]*", "", line)
            keys.append(line)
        return keys

    @staticmethod
    def _sanitize_proxy_uri_line(line: str) -> str:
        if "://" not in line or line.startswith("#"):
            return line
        main, _, fragment = line.partition("#")
        cleaned = re.sub(r"([?&])sni=(?=[&#]|$)", r"\1", main)
        cleaned = re.sub(r"\?&+", "?", cleaned)
        cleaned = re.sub(r"&&+", "&", cleaned)
        cleaned = cleaned.rstrip("?&")
        return f"{cleaned}#{fragment}" if fragment else cleaned

    def _subscription_download_headers(
        self,
        profile_page_url: str,
        profile_title_plain: str,
        expire_unix: int,
        response_body_bytes: bytes,
        announce: str = "",
    ) -> dict[str, str]:
        total_bytes = self._config.app.SUBSCRIPTION_USERINFO_TOTAL_BYTES
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "Profile-Title": self._b64(profile_title_plain),
            "Profile-Update-Interval": "1",
            "Subscription-Userinfo": f"upload=0; download=0; total={total_bytes}; expire={expire_unix}",
            "Support-Url": self._config.app.TELEGRAM_SUPPORT_URL,
            "Profile-Web-Page-Url": profile_page_url,
            "X-Subscription-Title": self._b64(profile_title_plain),
            "Content-Disposition": 'inline; filename="SkyDragonVPN.txt"',
            "Cache-Control": "private, no-store",
            "Content-Length": str(len(response_body_bytes)),
        }
        provider_id = self._config.app.HAPP_PROVIDER_ID.strip()
        if provider_id:
            headers["Providerid"] = provider_id
        if announce:
            headers["Announce"] = self._b64(announce)
            headers["Announce-Url"] = profile_page_url
        return headers

    def _build_subscription_body(self, keys: list[str], profile_url: str, announce_plain: str) -> str:
        provider_id = self._config.app.HAPP_PROVIDER_ID.strip()
        title = "🚀 SkyDragon🐉"
        meta = []
        if provider_id:
            meta.append(f"#providerid {provider_id}")
        new_url = self._config.app.HAPP_NEW_URL.strip() or profile_url
        if new_url:
            meta.append(f"#new-url {new_url}")
        meta.extend(
            [
                "#subscription-auto-update-open-enable: 0",
                "#subscription-always-hwid-enable: 1",
                "#subscriptions-collapse: 0",
                f"#profile-title: {title}",
                "#hide-settings: 1",
                "#ping-type tcp",
            ]
        )
        announce_block = self._b64(announce_plain)
        lines = meta + [""] + keys + ["", f"#announce: {announce_block}", f"#announce-url: {profile_url}"]
        return "\n".join(lines)

    def _build_stub_body(self, title: str, state: str, profile_url: str, user_agent: str | None) -> str:
        marker = "Не найдена" if state == "not_found" else "Истекла"
        hint = self._renewal_hint_for_client(user_agent)
        announce = f"{self._now_msk_time_str()} МСК. {hint}"
        return self._build_subscription_body([self._stub_uri(title)], profile_url, f"{marker}. {announce}")

    @staticmethod
    def _stub_uri(label: str) -> str:
        return f"vless://{uuid.uuid4()}@127.0.0.1:8443?type=tcp&encryption=none&security=reality#{label}"

    @staticmethod
    def _b64(text: str) -> str:
        payload = base64.b64encode((text or "").encode("utf-8")).decode("ascii")
        return f"base64:{payload}"

    @staticmethod
    def _renewal_hint_for_client(user_agent: str | None) -> str:
        ua = (user_agent or "").lower()
        if "v2raytun" in ua:
            return "Нажмите сюда, чтобы оплатить подписку."
        if any(token in ua for token in ("happ", "flyfrog", "happ-proxy")):
            return "Нажмите на кнопку продления в профиле, чтобы оплатить подписку."
        return "Нажмите кнопку продления в профиле."

    @staticmethod
    def _now_msk_time_str() -> str:
        try:
            return datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
        except Exception:
            msk = timezone(timedelta(hours=3))
            return datetime.now(msk).strftime("%d.%m.%Y %H:%M")
