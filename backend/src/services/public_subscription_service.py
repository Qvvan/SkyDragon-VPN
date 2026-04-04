from __future__ import annotations

import asyncio
import base64
import hashlib
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet

from core.config import Config
from core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from domain.entities.server import Server
from domain.entities.subscription import Subscription
from interfaces.clients.payment_gateway import IPaymentGateway
from interfaces.clients.vpn_subscription_transport import IVpnSubscriptionTransport
from interfaces.repositories.payment_repository import IPaymentRepository
from interfaces.repositories.server_repository import IServerRepository
from interfaces.repositories.service_tariff_repository import IServiceTariffRepository
from interfaces.repositories.subscription_repository import ISubscriptionRepository
from services import subscription_formatting as fmt


@dataclass(frozen=True, slots=True)
class SubscriptionClientPayload:
    content_b64: str
    headers: dict[str, str]


class PublicSubscriptionService:
    __slots__ = (
        "_cfg",
        "_subs",
        "_servers",
        "_tariffs",
        "_payments",
        "_transport",
        "_yookassa",
        "_fernet",
        "_public_base",
        "_profile_title",
    )

    def __init__(
        self,
        config: Config,
        subscription_repo: ISubscriptionRepository,
        server_repo: IServerRepository,
        tariff_repo: IServiceTariffRepository,
        payment_repo: IPaymentRepository,
        transport: IVpnSubscriptionTransport,
        yookassa: IPaymentGateway,
    ) -> None:
        self._cfg = config
        self._subs = subscription_repo
        self._servers = server_repo
        self._tariffs = tariff_repo
        self._payments = payment_repo
        self._transport = transport
        self._yookassa = yookassa
        self._fernet = Fernet(config.app.FERNET_KEY.get_secret_value().encode())
        self._public_base = (config.app.PUBLIC_BASE_URL or "").strip() or "https://skydragonvpn.ru"
        self._profile_title = config.subscription.PROFILE_TITLE

    def parse_encrypted_link(self, encrypted_part: str) -> tuple[int, int]:
        try:
            raw = self._fernet.decrypt(encrypted_part.encode()).decode("utf-8")
            parts = raw.split("|")
            return int(parts[0]), int(parts[1])
        except Exception as e:
            raise ValidationError("Invalid encryption") from e

    @staticmethod
    def encode_panel_subscription_id(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
        data = f"{user_id},{sub_id}"
        checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]
        combined = f"{data}|{checksum}"
        return base64.b64encode(combined.encode()).decode()

    async def build_import_page_context(
        self,
        *,
        encrypted_part: str,
        user_agent: str | None,
    ) -> dict[str, Any]:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        sub = await self._subs.get_by_user_and_subscription_id(user_id, sub_id)
        config_url = fmt.public_sub_url(self._public_base, encrypted_part)
        detected = fmt.detect_platform_from_ua(user_agent)
        apps_by_platform: dict[str, list[dict[str, str]]] = {}
        for platform, apps in fmt.APPS_BY_PLATFORM.items():
            mapped = []
            for app_cfg in apps:
                mapped.append({
                    "app_name": app_cfg["app_name"],
                    "store_url": app_cfg["store_url"],
                    "import_url": (
                        fmt.build_import_route_url(self._public_base, platform, app_cfg["import_app"], encrypted_part)
                        if app_cfg["import_type"] == "route"
                        else fmt.to_import_url(app_cfg["import_type"], config_url)
                    ),
                })
            apps_by_platform[platform] = mapped
        tariffs = await self._tariffs.list_for_renewal()
        return {
            "config_url": config_url,
            "encrypted_part": encrypted_part,
            "telegram_user_id": user_id,
            "subscription_id": sub_id,
            "detected_platform": detected,
            "devices": list(fmt.DEVICE_LABELS.items()),
            "apps_by_platform": apps_by_platform,
            "sub_info": fmt.build_sub_info_dict(sub),
            "services_for_renewal": fmt.renewal_services_as_dicts(tariffs),
        }

    async def build_client_subscription_payload(
        self,
        *,
        encrypted_part: str,
    ) -> SubscriptionClientPayload:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        subscription = await self._subs.get_by_user_and_subscription_id(user_id, sub_id)
        active_label = self._cfg.subscription.STATUS_ACTIVE_LABEL
        is_active = fmt.subscription_is_active(subscription, active_status_label=active_label)
        ex = fmt.expire_unix(subscription)
        config_url = fmt.public_sub_url(self._public_base, encrypted_part)

        if subscription is None:
            body = fmt.build_subscription_body(
                [fmt.stub_not_found_key()],
                state="not_found",
                profile_url=config_url,
                profile_title=self._profile_title,
            )
            enc = base64.b64encode(body.encode()).decode()
            return SubscriptionClientPayload(
                content_b64=enc,
                headers=fmt.encoded_response_headers(
                    profile_title_b64=fmt.b64_header(f"{self._profile_title} — Не найдена"),
                    expire_unix=0,
                    support_url=config_url,
                    announce_text=fmt.ANNOUNCE_NOT_FOUND,
                    body_len=len(enc),
                ),
            )

        if not is_active:
            body = fmt.build_subscription_body(
                [fmt.stub_expired_key()],
                state="expired",
                profile_url=config_url,
                profile_title=self._profile_title,
            )
            enc = base64.b64encode(body.encode()).decode()
            return SubscriptionClientPayload(
                content_b64=enc,
                headers=fmt.encoded_response_headers(
                    profile_title_b64=fmt.b64_header(self._profile_title),
                    expire_unix=ex,
                    support_url=config_url,
                    announce_text=fmt.ANNOUNCE_EXPIRED,
                    body_len=len(enc),
                ),
            )

        encoded_sub_id = self.encode_panel_subscription_id(user_id, sub_id)
        servers = await self._servers.list_visible()
        sub_port_default = self._cfg.subscription.SUB_PORT
        urls = self._cfg.subscription.EXTERNAL_SUB_URLS or []

        async def fetch_one(server: Server) -> list[str]:
            try:
                text = await self._transport.fetch_panel_subscription(
                    server, encoded_sub_id, sub_port_default,
                )
                if text is None:
                    return []
                return fmt.decode_sub_to_keys(
                    text, server.server_ip, server.name or server.server_ip,
                )
            except Exception:
                return []

        server_tasks = [fetch_one(s) for s in servers]
        external_tasks = [self._transport.fetch_external_subscription_keys(u) for u in urls]
        server_results, *external_results = await asyncio.gather(
            asyncio.gather(*server_tasks),
            *external_tasks,
        )
        external_keys = [k for keys_list in external_results for k in keys_list]
        keys = [k for key_list in server_results for k in key_list] + external_keys
        body = fmt.build_subscription_body(
            keys, state="active", profile_url=config_url, profile_title=self._profile_title,
        )
        enc = base64.b64encode(body.encode()).decode()
        return SubscriptionClientPayload(
            content_b64=enc,
            headers=fmt.encoded_response_headers(
                profile_title_b64=fmt.b64_header(self._profile_title),
                expire_unix=ex,
                support_url=config_url,
                announce_text=fmt.ANNOUNCE_ACTIVE,
                body_len=len(enc),
            ),
        )

    async def list_subscription_keys_json(
        self,
        *,
        encrypted_part: str,
    ) -> dict[str, Any]:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        subscription = await self._subs.get_by_user_and_subscription_id(user_id, sub_id)
        if subscription is None:
            return {
                "keys": [],
                "servers": [],
                "message": "Подписка не найдена или удалена. Оформите новую в боте.",
            }

        encoded_sub_id = self.encode_panel_subscription_id(user_id, sub_id)
        servers = await self._servers.list_visible()
        sub_port_default = self._cfg.subscription.SUB_PORT
        urls = self._cfg.subscription.EXTERNAL_SUB_URLS or []

        async def fetch_one(server: Server) -> dict[str, Any]:
            try:
                text = await self._transport.fetch_panel_subscription(
                    server, encoded_sub_id, sub_port_default,
                )
                name = server.name or server.server_ip
                keys_list = fmt.decode_sub_to_keys(text, server.server_ip, name) if text else []
                return {"server_ip": server.server_ip, "name": name, "keys": keys_list}
            except Exception:
                return {"server_ip": server.server_ip, "name": server.name or server.server_ip, "keys": []}

        server_results = await asyncio.gather(*[fetch_one(s) for s in servers])
        external_results = await asyncio.gather(*[
            self._transport.fetch_external_subscription_keys(u) for u in urls
        ])
        external_keys = [k for keys_list in external_results for k in keys_list]
        all_keys = [k for r in server_results for k in r["keys"]] + list(external_keys)
        server_infos = [{"server_ip": r["server_ip"], "name": r["name"]} for r in server_results]
        return {"keys": all_keys, "servers": server_infos}

    async def disable_auto_renewal(self, *, encrypted_part: str) -> None:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        await self._subs.set_auto_renewal(user_id, sub_id, enabled=False)

    async def enable_auto_renewal(self, *, encrypted_part: str) -> None:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        await self._subs.set_auto_renewal(user_id, sub_id, enabled=True)

    async def list_renewal_services_for_link(self, *, encrypted_part: str) -> list[dict[str, Any]]:
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        subscription = await self._subs.get_by_user_and_subscription_id(user_id, sub_id)
        if subscription is None:
            return []
        tariffs = await self._tariffs.list_for_renewal()
        return fmt.renewal_services_as_dicts(tariffs)

    async def create_renewal_payment_redirect(
        self,
        *,
        encrypted_part: str,
        service_id: int,
    ) -> str:
        if service_id <= 0:
            raise ValidationError("Invalid service_id")
        user_id, sub_id = self.parse_encrypted_link(encrypted_part)
        tariff = await self._tariffs.get_by_id(service_id)
        if tariff is None:
            raise NotFoundError("Service not found")
        try:
            payment_id, confirmation_url = await self._yookassa.create_renewal_payment(
                amount_rub=tariff.price,
                service_id=service_id,
                service_name=tariff.name,
                user_id=user_id,
                subscription_id=sub_id,
            )
        except RuntimeError as e:
            raise ServiceUnavailableError("Payment is not configured") from e
        await self._payments.create_pending(
            payment_id=payment_id,
            user_id=user_id,
            service_id=service_id,
        )
        return confirmation_url
