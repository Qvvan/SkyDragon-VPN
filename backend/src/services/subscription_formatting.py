"""
Чистые функции форматирования подписки (без БД и HTTP).
"""
from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import quote

from domain.entities.service_tariff import ServiceTariff
from domain.entities.subscription import Subscription

RU_MONTHS = (
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
)

CLIENT_USER_AGENTS = (
    "streisand", "happ", "hiddify", "v2raytun",
)

BROWSER_USER_AGENTS = (
    "mozilla", "chrome", "safari", "firefox", "edg/", "opera",
)

DEVICE_LABELS = {
    "iphone": "iPhone",
    "android": "Android",
    "windows": "Windows",
    "macos": "MacOS",
}

APPS_BY_PLATFORM = {
    "iphone": [
        {"app_name": "Happ (RU App Store)", "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973", "import_type": "route", "import_app": "happ"},
        {"app_name": "Happ (EU/US App Store)", "store_url": "https://apps.apple.com/us/app/happ-proxy-utility/id6504287215", "import_type": "route", "import_app": "happ"},
        {"app_name": "V2RayTun", "store_url": "https://apps.apple.com/ru/app/v2raytun/id6476628951", "import_type": "route", "import_app": "v2raytun"},
    ],
    "android": [
        {"app_name": "Happ (Google Play)", "store_url": "https://play.google.com/store/apps/details?id=com.happproxy", "import_type": "route", "import_app": "happ"},
        {"app_name": "V2RayTun", "store_url": "https://play.google.com/store/apps/details?id=com.v2raytun.android&hl=ru", "import_type": "route", "import_app": "v2raytun"},
    ],
    "windows": [
        {"app_name": "Happ", "store_url": "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe", "import_type": "route", "import_app": "happ"},
    ],
    "macos": [
        {"app_name": "Happ", "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973", "import_type": "route", "import_app": "happ"},
    ],
}

ANNOUNCE_ACTIVE = "Если VPN работает нестабильно, смените страну подключения. Для продления нажмите сюда."
ANNOUNCE_EXPIRED = "Подписка истекла. Нажмите, чтобы продлить. Если подписка оплачена, но статус ещё «истекла», нажмите кнопку 🔁."
ANNOUNCE_NOT_FOUND = "Подписка удалена или не найдена. Нажмите, чтобы оформить новую. Если подписка оплачена, но статус ещё «истекла», нажмите кнопку 🔁."

SUB_INFO_COLOR = "blue"
SUB_INFO_ACTIVE = "Если VPN работает нестабильно, смените страну подключения."
SUB_INFO_BUTTON_ACTIVE = "Для продления нажмите сюда"
SUB_INFO_EXPIRED = "Подписка истекла. Нажмите, чтобы продлить."
SUB_INFO_BUTTON_EXPIRED = "Нажмите, чтобы продлить"
SUB_INFO_NOT_FOUND = "Подписка удалена или не найдена. Нажмите, чтобы оформить новую."
SUB_INFO_BUTTON_NOT_FOUND = "Оформить новую подписку"


def public_sub_url(public_base_url: str, encrypted_part: str) -> str:
    return f"{public_base_url.rstrip('/')}/sub/{encrypted_part}"


def happ_add_subscription_deeplink(public_base_url: str, encrypted_part: str) -> str:
    sub_url = public_sub_url(public_base_url, encrypted_part)
    return f"happ://add/{quote(sub_url, safe='')}"


def build_import_route_url(public_base_url: str, platform: str, app_name: str, encrypted_part: str) -> str:
    base = public_base_url.rstrip("/")
    return f"{base}/import/{platform}/{app_name}/{encrypted_part}"


def is_known_client_request(user_agent: str | None) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(c in ua for c in CLIENT_USER_AGENTS)


def detect_platform_from_ua(user_agent: str | None) -> str:
    if not user_agent:
        return "android"
    ua = user_agent.lower()
    if "iphone" in ua or "ipad" in ua or "ios" in ua:
        return "iphone"
    if "mac os" in ua or "macintosh" in ua:
        return "macos"
    if "windows" in ua:
        return "windows"
    if "android" in ua:
        return "android"
    return "android"


def is_browser_request(user_agent: str | None) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(t in ua for t in BROWSER_USER_AGENTS)


def to_import_url(import_type: str, config_url: str) -> str:
    if import_type == "v2raytun":
        return f"v2raytun://import/{config_url}"
    return config_url


def decode_sub_to_keys(base64_text: str, server_ip: str, server_name: str) -> list[str]:
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


def subscription_is_active(sub: Subscription | None, *, active_status_label: str) -> bool:
    if not sub:
        return False
    now = datetime.utcnow()
    return sub.is_active(active_status_label=active_status_label, now=now)


def expire_unix(sub: Subscription | None) -> int:
    if not sub:
        return 0
    return sub.expire_unix()


def build_userinfo(upload: int = 0, download: int = 0, total: int = 0, expire: int = 0) -> str:
    return f"upload={upload}; download={download}; total={total}; expire={expire}"


def b64_header(text: str) -> str:
    return f"base64:{base64.b64encode(text.encode('utf-8')).decode('ascii')}"


def build_subscription_body(
    keys: list[str],
    *,
    state: Literal["active", "expired", "not_found"],
    profile_url: str,
    profile_title: str,
) -> str:
    if state == "active":
        announce_url = profile_url
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_ACTIVE}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_ACTIVE}",
            f"#sub-info-button-link: {profile_url}",
            f"#profile-title: {profile_title}",
        ]
        announce = ANNOUNCE_ACTIVE
    elif state == "expired":
        announce_url = profile_url
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_EXPIRED}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_EXPIRED}",
            f"#sub-info-button-link: {profile_url}",
            f"#profile-title: {profile_title} — Истекла",
        ]
        announce = ANNOUNCE_EXPIRED
    else:
        announce_url = profile_url
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_NOT_FOUND}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_NOT_FOUND}",
            f"#sub-info-button-link: {profile_url}",
            f"#profile-title: {profile_title} — Не найдена",
        ]
        announce = ANNOUNCE_NOT_FOUND

    lines = meta + [""] + keys + [
        "",
        f"#announce: {b64_header(announce)}",
        f"#announce-url: {announce_url}",
    ]
    return "\n".join(lines)


def format_date_ru(value: datetime | None) -> str:
    if not value:
        return "—"
    month_name = RU_MONTHS[value.month - 1]
    return f"{value.day:02d} {month_name} {value.year}"


def subscription_status_key(status: str | None) -> str:
    status_map = {
        "активная": "active",
        "истекла": "expired",
        "отключена": "cancelled",
    }
    return status_map.get((status or "").strip().lower(), "pending")


def days_remaining(end_date: datetime | None) -> int:
    if not end_date:
        return 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
    delta = end - now
    return max(0, delta.days)


def build_sub_info_dict(subscription: Subscription | None) -> dict | None:
    if not subscription:
        return None
    status_key = subscription_status_key(subscription.status)
    price = subscription.service_price
    service_id = subscription.service_id
    is_trial = service_id == 0
    duration_days = subscription.service_duration_days
    if is_trial and not duration_days:
        duration_days = 0
    price_s = "Бесплатно" if is_trial else (f"{price} ₽" if price is not None else "—")
    return {
        "service_name": "Пробный период" if is_trial else (subscription.service_name or "SkyDragon VPN"),
        "status": subscription.status or "неизвестно",
        "status_key": status_key,
        "duration_days": duration_days or 0,
        "price": price_s,
        "source": "Telegram Bot",
        "auto_renewal": bool(subscription.auto_renewal),
        "start_date": format_date_ru(subscription.start_date),
        "end_date": format_date_ru(subscription.end_date),
        "days_remaining": days_remaining(subscription.end_date),
    }


def renewal_services_as_dicts(tariffs: list[ServiceTariff]) -> list[dict]:
    return [
        {
            "service_id": t.service_id,
            "name": t.name,
            "duration_days": t.duration_days,
            "price": t.price,
        }
        for t in tariffs
    ]


def stub_not_found_key() -> str:
    u = str(uuid.uuid4())
    return f"vless://{u}@127.0.0.1:8443?type=tcp&encryption=none&security=reality#Подписка не найдена"


def stub_expired_key() -> str:
    u = str(uuid.uuid4())
    return f"vless://{u}@127.0.0.1:8443?type=tcp&encryption=none&security=reality#ИСТЕКЛА😢"


def encoded_response_headers(
    *,
    profile_title_b64: str,
    expire_unix: int,
    support_url: str,
    announce_text: str,
    body_len: int,
) -> dict[str, str]:
    return {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": profile_title_b64,
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": build_userinfo(expire=expire_unix),
        "Support-Url": support_url,
        "Announce": b64_header(announce_text),
        "Announce-Url": support_url,
        "Content-Length": str(body_len),
    }
