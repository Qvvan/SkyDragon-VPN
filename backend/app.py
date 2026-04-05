import asyncio
import base64
import hashlib
from pathlib import Path
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from zoneinfo import ZoneInfo
from urllib.parse import quote, unquote

from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, Depends, Request
from yookassa import Configuration, Payment
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from cfg.config import (
    CRYPTO_KEY,
    HAPP_PROVIDER_ID,
    PUBLIC_BASE_URL,
    SHOP_ID,
    SHOP_API_TOKEN,
    SUBSCRIPTION_USERINFO_TOTAL_BYTES,
    TELEGRAM_SUPPORT_URL,
    TELEGRAM_YOOKASSA_RETURN_URL,
)
from db import methods
from db.db import get_db
from sub_fetcher import get_sub_from_server, fetch_external_subscription_keys

# Внешние подписки: ключи добавляются к нашим (таймаут 3 сек каждый)
EXTERNAL_SUB_URLS = [
    "https://sp.vpnlider.online/ndKFYzNwuk2ryHba",
    "https://link.1cdn.lol/QKLZy",
]
SUB_STATUS_ACTIVE = "активная"

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
if SHOP_ID and SHOP_API_TOKEN:
    Configuration.account_id = SHOP_ID
    Configuration.secret_key = SHOP_API_TOKEN

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cipher = Fernet(CRYPTO_KEY)


def _subscription_landing_template_extra() -> dict:
    """Ссылки на Telegram и публичный сайт для Jinja (без хардкода домена)."""
    from cfg.config import TELEGRAM_BOT_START_1, TELEGRAM_BOT_URL, TELEGRAM_SUPPORT_URL

    return {
        "telegram_support_url": TELEGRAM_SUPPORT_URL,
        "telegram_bot_url": TELEGRAM_BOT_URL,
        "telegram_bot_start_1_url": TELEGRAM_BOT_START_1,
        "public_base_url": PUBLIC_BASE_URL,
    }


def _decode_sub_to_keys(base64_text: str, server_ip: str, server_name: str) -> list[str]:
    """Декодирует base64 подписки в список ключей, подставляет server_ip и server_name."""
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


def _subscription_is_active(sub: Optional[dict]) -> bool:
    if not sub:
        return False
    if sub.get("status") != SUB_STATUS_ACTIVE:
        return False
    end = sub.get("end_date")
    if end is None:
        return True
    now = datetime.utcnow()
    return end.replace(tzinfo=None) >= now if hasattr(end, "replace") else end >= now


def _expire_unix(sub: Optional[dict]) -> int:
    if not sub or not sub.get("end_date"):
        return 0
    end = sub["end_date"]
    return int(end.timestamp()) if hasattr(end, "timestamp") else 0


def _build_userinfo(upload: int = 0, download: int = 0, total: int = 0, expire: int = 0) -> str:
    return f"upload={upload}; download={download}; total={total}; expire={expire}"


def _b64(text: str) -> str:
    """UTF-8 → base64:... одной строкой (без переносов в payload) для Happ и HTTP-заголовков."""
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    payload = base64.b64encode(normalized.encode("utf-8")).decode("ascii")
    return f"base64:{payload}"


def _subscription_download_headers(
    *,
    profile_page_url: str,
    support_url: str,
    profile_title_plain: str,
    expire_unix: int,
    traffic_total_bytes: int,
    announce_plain: str,
    response_body_bytes: bytes,
    provider_id: str,
) -> dict[str, str]:
    """Заголовки ответа подписки (Happ: Providerid + Support-Url + userinfo с total для шкалы трафика)."""
    safe_name = "SkyDragonVPN.txt"
    headers: dict[str, str] = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": _b64(profile_title_plain),
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": _build_userinfo(
            upload=0,
            download=0,
            total=traffic_total_bytes,
            expire=expire_unix,
        ),
        "Support-Url": support_url,
        "Profile-Web-Page-Url": profile_page_url,
        # HTTP-заголовки — только latin-1; эмодзи в названии — через base64 (как Profile-Title)
        "X-Subscription-Title": _b64(profile_title_plain),
        "Content-Disposition": f'inline; filename="{safe_name}"',
        "Cache-Control": "private, no-store",
        "Content-Length": str(len(response_body_bytes)),
    }
    if provider_id.strip():
        headers["Providerid"] = provider_id.strip()
    if announce_plain.strip():
        headers["Announce"] = _b64(announce_plain)
        headers["Announce-Url"] = profile_page_url
    return headers


# Короткое название подписки
PROFILE_TITLE = "SkyDragon🐉"
RU_MONTHS = (
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
)

CLIENT_USER_AGENTS = (
    "streisand",
    "happ",
    "hiddify",
    "v2raytun",
    "v2rayng",
    "nekobox",
    "sing-box",
    "singbox",
    "clash",
    "clashmeta",
    "flyfrog",  # Happ Desktop (FlyFrog LLC)
    "happ-proxy",
)

BROWSER_USER_AGENTS = (
    "mozilla",
    "chrome",
    "safari",
    "firefox",
    "edg/",
    "opera",
)

DEVICE_LABELS = {
    "iphone": "iPhone",
    "android": "Android",
    "windows": "Windows",
    "macos": "MacOS",
}

APPS_BY_PLATFORM = {
    "iphone": [
        {
            "app_name": "Happ (RU App Store)",
            "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
            "import_type": "route",
            "import_app": "happ",
        },
        {
            "app_name": "Happ (EU/US App Store)",
            "store_url": "https://apps.apple.com/us/app/happ-proxy-utility/id6504287215",
            "import_type": "route",
            "import_app": "happ",
        },
        {
            "app_name": "V2RayTun",
            "store_url": "https://apps.apple.com/ru/app/v2raytun/id6476628951",
            "import_type": "route",
            "import_app": "v2raytun",
        }
    ],
    "android": [
        {
            "app_name": "Happ (Google Play)",
            "store_url": "https://play.google.com/store/apps/details?id=com.happproxy",
            "import_type": "route",
            "import_app": "happ",
        },
        {
            "app_name": "V2RayTun",
            "store_url": "https://play.google.com/store/apps/details?id=com.v2raytun.android&hl=ru",
            "import_type": "route",
            "import_app": "v2raytun",
        }
    ],
    "windows": [
        {
            "app_name": "Happ",
            "store_url": "https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe",
            "import_type": "route",
            "import_app": "happ",
        }
    ],
    "macos": [
        {
            "app_name": "Happ",
            "store_url": "https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973",
            "import_type": "route",
            "import_app": "happ",
        }
    ],
}

ANNOUNCE_EXPIRED = "Подписка истекла. Нажмите, чтобы продлить. Если подписка оплачена, но статус ещё «истекла», нажмите кнопку 🔁."
ANNOUNCE_NOT_FOUND = "Подписка удалена или не найдена. Нажмите, чтобы оформить новую. Если подписка оплачена, но статус ещё «истекла», нажмите кнопку 🔁."

# sub-info: как у WhyPN — в теле подписки plain UTF-8 (не base64:). Кнопка ≤25 символов (док Happ).
SUB_INFO_COLOR = "blue"
SUB_INFO_ACTIVE = (
    "Поддержка SkyDragon работает 24/7. Напишите нам, если что-то не работает. "
    "Продлить подписку — на странице профиля (иконка ссылки слева)."
)
SUB_INFO_BUTTON_ACTIVE = "Написать в поддержку 💬"
SUB_INFO_EXPIRED = "Срок подписки закончился. Продлите на странице профиля, чтобы снова пользоваться VPN."
SUB_INFO_BUTTON_EXPIRED = "Продлить подписку"
SUB_INFO_NOT_FOUND = "Подписка не найдена. Оформите новую в боте или откройте страницу профиля."
SUB_INFO_BUTTON_NOT_FOUND = "Открыть страницу"


def _now_msk_time_str() -> str:
    """Метка времени для анонса: московское время, как в примере WhyPN."""
    try:
        return datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
    except Exception:
        msk = timezone(timedelta(hours=3))
        return datetime.now(msk).strftime("%d.%m.%Y %H:%M")


def _happ_subscription_extra_meta_lines() -> list[str]:
    """Доп. поля в духе WhyPN / Happ (#providerid задаётся отдельно сразу после sub-info)."""
    return [
        "#subscription-auto-update-open-enable: 0",
        "#subscriptions-collapse: 0",
        "#hide-settings: 1",
        "#ping-type tcp",
    ]


def _outer_base64_payload(inner_utf8: str) -> bytes:
    """Happ при импорте ожидает тело ответа как base64 от UTF-8 текста подписки."""
    return base64.b64encode(inner_utf8.encode("utf-8"))


def _is_known_client_request(user_agent: Optional[str]) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(client_ua in ua for client_ua in CLIENT_USER_AGENTS)


def _accept_prefers_html(accept: Optional[str]) -> bool:
    """Первый тип в Accept — text/html (типичный переход из браузера). *//* и text/plain — нет."""
    if not accept or not accept.strip():
        return False
    first = accept.split(",")[0].strip().split(";")[0].strip().lower()
    return first in ("text/html", "application/xhtml+xml")


def _force_raw_subscription(request: Request) -> bool:
    q = request.query_params
    return q.get("raw") in ("1", "true", "yes") or q.get("format") in ("raw", "subscription")


def _force_web_landing(request: Request) -> bool:
    """Явно открыть HTML-страницу (например, очень старый браузер без Sec-Fetch-Dest)."""
    return request.query_params.get("web") in ("1", "true", "yes")


def _should_return_html_landing(request: Request) -> bool:
    """
    HTML-лендинг только для реальной навигации вкладки (Sec-Fetch-Dest: document).
    Happ Desktop шлёт Chrome-like UA и иногда Accept с text/html, но без Sec-Fetch — ему нужен base64.
    """
    if _force_raw_subscription(request):
        return False
    ua = request.headers.get("user-agent", "")
    accept = request.headers.get("accept")
    if _force_web_landing(request):
        return _is_browser_request(ua) and _accept_prefers_html(accept)
    if _is_known_client_request(ua):
        return False
    if not _is_browser_request(ua):
        return False
    if not _accept_prefers_html(accept):
        return False
    dest_raw = request.headers.get("sec-fetch-dest")
    if dest_raw is None:
        # Встроенный браузер Telegram часто без Sec-Fetch-* — показываем лендинг
        if "telegram" in ua.lower():
            return True
        return False
    dest = dest_raw.lower()
    mode = (request.headers.get("sec-fetch-mode") or "").lower()
    if dest == "empty" or mode == "cors":
        return False
    return dest in ("document", "iframe", "frame")


def _sanitize_proxy_uri_line(line: str) -> str:
    """Убирает пустой sni= в query (у части клиентов ломает разбор URI)."""
    if "://" not in line or line.startswith("#"):
        return line
    main, sep, fragment = line.partition("#")
    cleaned = re.sub(r"([?&])sni=(?=[&#]|$)", r"\1", main)
    cleaned = re.sub(r"\?&+", "?", cleaned)
    cleaned = re.sub(r"&&+", "&", cleaned)
    cleaned = cleaned.rstrip("?&")
    if fragment:
        return f"{cleaned}#{fragment}"
    return cleaned


def _detect_platform_from_ua(user_agent: Optional[str]) -> str:
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


def _is_browser_request(user_agent: Optional[str]) -> bool:
    if not user_agent:
        return False
    ua = user_agent.lower()
    return any(token in ua for token in BROWSER_USER_AGENTS)


def _to_import_url(import_type: str, config_url: str) -> str:
    if import_type == "v2raytun":
        return f"v2raytun://import/{config_url}"
    return config_url


def _public_sub_url(encrypted_part: str) -> str:
    return f"{PUBLIC_BASE_URL}/sub/{encrypted_part}"


def _happ_add_subscription_deeplink(encrypted_part: str) -> str:
    """
    В Happ: «Добавить конфигурацию» — happ://add/{url}
    URL подписки кодируем, чтобы : и / не ломали разбор схемы.
    """
    sub_url = _public_sub_url(encrypted_part)
    return f"happ://add/{quote(sub_url, safe='')}"


def _build_import_route_url(platform: str, app_name: str, encrypted_part: str) -> str:
    return f"{PUBLIC_BASE_URL}/import/{platform}/{app_name}/{encrypted_part}"


def _format_date_ru(value: Optional[datetime]) -> str:
    if not value:
        return "—"
    month_name = RU_MONTHS[value.month - 1]
    return f"{value.day:02d} {month_name} {value.year}"


def _subscription_status_key(status: Optional[str]) -> str:
    status_map = {
        "активная": "active",
        "истекла": "expired",
        "отключена": "cancelled",
    }
    return status_map.get((status or "").strip().lower(), "pending")


def _days_remaining(end_date: Optional[datetime]) -> int:
    if not end_date:
        return 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = end_date.replace(tzinfo=None) - now
    return max(0, delta.days)


def _build_sub_info(subscription: Optional[dict]) -> Optional[dict]:
    if not subscription:
        return None
    status_key = _subscription_status_key(subscription.get("status"))
    price = subscription.get("service_price")
    service_id = subscription.get("service_id")
    is_trial = service_id == 0
    duration_days = subscription.get("service_duration_days")
    if is_trial and not duration_days:
        duration_days = 0
    price = "Бесплатно" if is_trial else (f"{price} ₽" if price is not None else "—")
    return {
        "service_name": "Пробный период" if is_trial else (subscription.get("service_name") or "SkyDragon VPN"),
        "status": subscription.get("status") or "неизвестно",
        "status_key": status_key,
        "duration_days": duration_days or 0,
        "price": price,
        "source": "Telegram Bot",
        "auto_renewal": bool(subscription.get("auto_renewal")),
        "start_date": _format_date_ru(subscription.get("start_date")),
        "end_date": _format_date_ru(subscription.get("end_date")),
        "days_remaining": _days_remaining(subscription.get("end_date")),
    }


async def _create_yookassa_payment(
    *,
    amount: int,
    service_id: int,
    service_name: str,
    user_id: int,
    subscription_id: int,
) -> dict:
    payload = {
        "amount": {
            "value": amount,
            "currency": "RUB",
        },
        "capture": True,
        "save_payment_method": True,
        "description": f"Оплата за услугу: {service_name}",
        "confirmation": {
            "type": "redirect",
            "return_url": TELEGRAM_YOOKASSA_RETURN_URL,
        },
        "metadata": {
            "service_id": service_id,
            "service_type": "old",
            "user_id": user_id,
            "username": "",
            "recipient_user_id": None,
            "subscription_id": subscription_id,
        },
    }

    def _create_payment_sync() -> dict:
        return Payment.create(payload)

    payment = await asyncio.to_thread(_create_payment_sync)
    return payment


def _build_subscription_body(
    keys: list[str],
    *,
    state: Literal["active", "expired", "not_found"],
    profile_url: str,
    support_url: str,
    msk_time: str,
    provider_id: str,
) -> tuple[str, str]:
    """
    Внутренний текст подписки (как у WhyPN): sub-info plain UTF-8; #announce — base64:.
    Без #providerid в теле Happ не включает Advanced Announcements (док happ-proxy).
    """
    extra = _happ_subscription_extra_meta_lines()
    prov = provider_id.strip()
    provider_line = [f"#providerid {prov}"] if prov else []

    if state == "active":
        announce_plain = (
            f"Обновлено {msk_time} МСК. Продление — на странице подписки.\n"
            "Потяните вниз, чтобы получить актуальный список серверов."
        )
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_ACTIVE}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_ACTIVE}",
            f"#sub-info-button-link: {support_url}",
            *provider_line,
            *extra,
            f"#profile-title: {PROFILE_TITLE}",
        ]
        announce_url = profile_url
    elif state == "expired":
        announce_plain = f"{ANNOUNCE_EXPIRED}\nВремя проверки: {msk_time} МСК."
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_EXPIRED}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_EXPIRED}",
            f"#sub-info-button-link: {profile_url}",
            *provider_line,
            *extra,
            f"#profile-title: {PROFILE_TITLE} — Истекла",
        ]
        announce_url = profile_url
    else:
        announce_plain = f"{ANNOUNCE_NOT_FOUND}\nПроверено: {msk_time} МСК."
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_NOT_FOUND}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_NOT_FOUND}",
            f"#sub-info-button-link: {profile_url}",
            *provider_line,
            *extra,
            f"#profile-title: {PROFILE_TITLE} — Не найдена",
        ]
        announce_url = profile_url

    announce_block = _b64(announce_plain)
    lines = meta + [""] + keys + ["", f"#announce: {announce_block}", f"#announce-url: {announce_url}"]
    return "\n".join(lines), announce_plain


@app.get("/sub/{encrypted_part}")
async def get_subscription(
    encrypted_part: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    subscription = await methods.get_subscription_by_user_and_sub_id(db, user_id, sub_id)
    is_active = _subscription_is_active(subscription)
    expire_unix = _expire_unix(subscription)
    config_url = _public_sub_url(encrypted_part)
    user_agent = request.headers.get("user-agent", "")

    if _should_return_html_landing(request):
        detected_platform = _detect_platform_from_ua(user_agent)
        apps_by_platform = {}
        for platform, apps in APPS_BY_PLATFORM.items():
            mapped_apps = []
            for app_cfg in apps:
                mapped_apps.append(
                    {
                        "app_name": app_cfg["app_name"],
                        "store_url": app_cfg["store_url"],
                        "import_url": (
                            _build_import_route_url(platform, app_cfg["import_app"], encrypted_part)
                            if app_cfg["import_type"] == "route"
                            else _to_import_url(app_cfg["import_type"], config_url)
                        ),
                    }
                )
            apps_by_platform[platform] = mapped_apps
        services_for_renewal = await methods.get_services_for_renewal(db)
        return templates.TemplateResponse(
            name="subscription_import.html",
            request=request,
            context={
                "config_url": config_url,
                "encrypted_part": encrypted_part,
                "telegram_user_id": user_id,
                "subscription_id": sub_id,
                "detected_platform": detected_platform,
                "devices": list(DEVICE_LABELS.items()),
                "apps_by_platform": apps_by_platform,
                "sub_info": _build_sub_info(subscription),
                "services_for_renewal": services_for_renewal,
                **_subscription_landing_template_extra(),
            },
        )

    # Подписка не найдена или удалена
    if subscription is None:
        stub_uuid = str(uuid.uuid4())
        stub_key = (
            f"vless://{stub_uuid}@127.0.0.1:8443"
            "?type=tcp&encryption=none&security=reality#Подписка не найдена"
        )
        msk_time = _now_msk_time_str()
        inner, announce_plain = _build_subscription_body(
            [stub_key],
            state="not_found",
            profile_url=config_url,
            support_url=TELEGRAM_SUPPORT_URL,
            msk_time=msk_time,
            provider_id=HAPP_PROVIDER_ID,
        )
        response_bytes = _outer_base64_payload(inner)
        headers = _subscription_download_headers(
            profile_page_url=config_url,
            support_url=TELEGRAM_SUPPORT_URL,
            profile_title_plain=f"{PROFILE_TITLE} — Не найдена",
            expire_unix=0,
            traffic_total_bytes=0,
            announce_plain=announce_plain,
            response_body_bytes=response_bytes,
            provider_id=HAPP_PROVIDER_ID,
        )
        return Response(content=response_bytes, headers=headers)

    # Подписка есть, но истекла
    if not is_active:
        stub_uuid = str(uuid.uuid4())
        stub_key = (
            f"vless://{stub_uuid}@127.0.0.1:8443"
            "?type=tcp&encryption=none&security=reality#ИСТЕКЛА😢"
        )
        msk_time = _now_msk_time_str()
        inner, announce_plain = _build_subscription_body(
            [stub_key],
            state="expired",
            profile_url=config_url,
            support_url=TELEGRAM_SUPPORT_URL,
            msk_time=msk_time,
            provider_id=HAPP_PROVIDER_ID,
        )
        response_bytes = _outer_base64_payload(inner)
        headers = _subscription_download_headers(
            profile_page_url=config_url,
            support_url=TELEGRAM_SUPPORT_URL,
            profile_title_plain=PROFILE_TITLE,
            expire_unix=expire_unix,
            traffic_total_bytes=SUBSCRIPTION_USERINFO_TOTAL_BYTES,
            announce_plain=announce_plain,
            response_body_bytes=response_bytes,
            provider_id=HAPP_PROVIDER_ID,
        )
        return Response(content=response_bytes, headers=headers)

    encoded_sub_id = encode_numbers(user_id, sub_id)
    servers = await methods.get_server(db)

    async def fetch_one(server):
        try:
            sub = await get_sub_from_server(server, encoded_sub_id)
            if sub is None:
                return []
            return _decode_sub_to_keys(
                sub, server.server_ip, server.name or server.server_ip
            )
        except Exception as e:
            print(f"Error getting subscription for server {server.server_ip}: {e}")
            return []

    # Параллельно: наши сервера + все внешние подписки (таймаут 3 сек каждая)
    server_tasks = [fetch_one(s) for s in servers]
    external_tasks = [fetch_external_subscription_keys(u) for u in EXTERNAL_SUB_URLS]
    server_results, *external_results = await asyncio.gather(
        asyncio.gather(*server_tasks),
        *external_tasks,
    )
    external_keys = [k for keys_list in external_results for k in keys_list]
    keys = [k for key_list in server_results for k in key_list] + external_keys
    keys = [_sanitize_proxy_uri_line(k) for k in keys]
    msk_time = _now_msk_time_str()
    inner, announce_plain = _build_subscription_body(
        keys,
        state="active",
        profile_url=config_url,
        support_url=TELEGRAM_SUPPORT_URL,
        msk_time=msk_time,
        provider_id=HAPP_PROVIDER_ID,
    )
    response_bytes = _outer_base64_payload(inner)

    headers = _subscription_download_headers(
        profile_page_url=config_url,
        support_url=TELEGRAM_SUPPORT_URL,
        profile_title_plain=PROFILE_TITLE,
        expire_unix=expire_unix,
        traffic_total_bytes=SUBSCRIPTION_USERINFO_TOTAL_BYTES,
        announce_plain=announce_plain,
        response_body_bytes=response_bytes,
        provider_id=HAPP_PROVIDER_ID,
    )
    return Response(content=response_bytes, headers=headers)


@app.get("/sub/{encrypted_part}/list")
async def get_subscription_list(encrypted_part: str, db: Session = Depends(get_db)):
    """
    Возвращает список ключей в JSON для тестирования.
    Ответ: {"keys": ["vless://...", ...], "servers": [{"server_ip": "...", "name": "..."}]}
    """
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    subscription = await methods.get_subscription_by_user_and_sub_id(db, user_id, sub_id)
    if subscription is None:
        return {
            "keys": [],
            "servers": [],
            "message": "Подписка не найдена или удалена. Оформите новую в боте.",
        }

    encoded_sub_id = encode_numbers(user_id, sub_id)
    servers = await methods.get_server(db)

    async def fetch_one(server):
        try:
            sub = await get_sub_from_server(server, encoded_sub_id)
            name = server.name or server.server_ip
            keys = (
                _decode_sub_to_keys(sub, server.server_ip, name)
                if sub else []
            )
            return {"server_ip": server.server_ip, "name": name, "keys": keys}
        except Exception as e:
            print(f"Error getting subscription for server {server.server_ip}: {e}")
            return {"server_ip": server.server_ip, "name": server.name or server.server_ip, "keys": []}

    server_results = await asyncio.gather(*[fetch_one(s) for s in servers])
    external_results = await asyncio.gather(*[fetch_external_subscription_keys(u) for u in EXTERNAL_SUB_URLS])
    external_keys = [k for keys_list in external_results for k in keys_list]
    all_keys = [k for r in server_results for k in r["keys"]] + list(external_keys)
    server_infos = [{"server_ip": r["server_ip"], "name": r["name"]} for r in server_results]
    return {
        "keys": all_keys,
        "servers": server_infos,
    }


@app.get("/import/iphone/{encrypted_part}")
async def import_iphone_legacy(encrypted_part: str):
    """Короткая ссылка из бота: импорт в Happ (как на iOS/Android с /happ/)."""
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/android/{encrypted_part}")
async def import_android_legacy(encrypted_part: str):
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/iphone/happ/{encrypted_part}")
async def import_iphone_happ(encrypted_part: str):
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/android/happ/{encrypted_part}")
async def import_android_happ(encrypted_part: str):
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/android/v2raytun/{encrypted_part}")
async def import_android_v2raytun(encrypted_part: str):
    return RedirectResponse(url=f"v2raytun://import/{_public_sub_url(encrypted_part)}", status_code=302)


@app.get("/import/iphone/v2raytun/{encrypted_part}")
async def import_iphone_v2raytun(encrypted_part: str):
    return RedirectResponse(url=f"v2raytun://import/{_public_sub_url(encrypted_part)}", status_code=302)


@app.get("/import/windows/happ/{encrypted_part}")
async def import_windows_happ(encrypted_part: str):
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/windows/v2raytun/{encrypted_part}")
async def import_windows_v2raytun(encrypted_part: str):
    return RedirectResponse(url=f"v2raytun://import/{_public_sub_url(encrypted_part)}", status_code=302)


@app.get("/import/macos/happ/{encrypted_part}")
async def import_macos_happ(encrypted_part: str):
    return RedirectResponse(url=_happ_add_subscription_deeplink(encrypted_part), status_code=302)


@app.get("/import/macos/v2raytun/{encrypted_part}")
async def import_macos_v2raytun(encrypted_part: str):
    return RedirectResponse(url=f"v2raytun://import/{_public_sub_url(encrypted_part)}", status_code=302)


def encode_numbers(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
    data = f"{user_id},{sub_id}"

    checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]

    combined = f"{data}|{checksum}"

    encoded = base64.b64encode(combined.encode()).decode()

    return encoded


def decrypt_part(encrypted_data: str) -> str:
    """Дешифрует токен из URL (Fernet). Учитываем unquote и + → пробел у части прокси/клиентов."""
    normalized = unquote((encrypted_data or "").strip()).replace(" ", "+")
    decrypted_data = cipher.decrypt(normalized.encode())
    return decrypted_data.decode("utf-8")


@app.post("/sub/{encrypted_part}/auto-renewal/disable")
async def disable_auto_renewal(
    encrypted_part: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    await methods.disable_auto_renewal_by_user_and_sub_id(db, user_id, sub_id)
    return RedirectResponse(url=f"/sub/{encrypted_part}", status_code=303)


@app.post("/sub/{encrypted_part}/auto-renewal/enable")
async def enable_auto_renewal(
    encrypted_part: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    await methods.enable_auto_renewal_by_user_and_sub_id(db, user_id, sub_id)
    return RedirectResponse(url=f"/sub/{encrypted_part}", status_code=303)


@app.post("/sub/{encrypted_part}/payments/create")
async def create_payment_for_renewal(
    encrypted_part: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        form_data = await request.form()
        service_id = int(str(form_data.get("service_id", "0")))
    except Exception:
        return Response(content="Invalid service_id", status_code=400)

    if service_id <= 0:
        return Response(content="Invalid service_id", status_code=400)

    if not SHOP_ID or not SHOP_API_TOKEN:
        return Response(content="Payment is not configured", status_code=503)

    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    service = await methods.get_service_by_id(db, service_id)
    if service is None:
        return Response(content="Service not found", status_code=404)

    payment = await _create_yookassa_payment(
        amount=int(service["price"]),
        service_id=service_id,
        service_name=str(service["name"]),
        user_id=user_id,
        subscription_id=sub_id,
    )
    payment_id = str(payment.id)
    payment_url = str(payment.confirmation.confirmation_url)

    await methods.create_pending_payment(
        db,
        payment_id=payment_id,
        user_id=user_id,
        service_id=service_id,
    )
    return RedirectResponse(url=payment_url, status_code=303)


@app.get("/sub/{encrypted_part}/services")
async def get_renewal_services(
    encrypted_part: str,
    db: Session = Depends(get_db),
):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    subscription = await methods.get_subscription_by_user_and_sub_id(db, user_id, sub_id)
    if subscription is None:
        return {"services": []}

    services_for_renewal = await methods.get_services_for_renewal(db)
    return {"services": services_for_renewal}
