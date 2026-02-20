import asyncio
import base64
import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from cfg.config import CRYPTO_KEY
from db import methods
from db.db import get_db
from sub_fetcher import get_sub_from_server, fetch_external_subscription_keys

SUPPORT_URL_ACTIVE = "https://t.me/SkyDragonSupport"
# Внешняя подписка: ключи добавляются к нашим (таймаут 3 сек)
EXTERNAL_SUB_URL = "https://sp.vpnlider.online/ndKFYzNwuk2ryHba"
BOT_URL_EXPIRED = "https://t.me/SkyDragonVPNBot?start=1"
SUB_STATUS_ACTIVE = "активная"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cipher = Fernet(CRYPTO_KEY)


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
    """Текст в base64 для заголовков (profile-title, announce)."""
    return f"base64:{base64.b64encode(text.encode('utf-8')).decode('ascii')}"


# Короткое название подписки
PROFILE_TITLE = "SkyDragon🐉"

ANNOUNCE_ACTIVE = "⚠️ ВЫБЕРИТЕ ДРУГОЙ СЕРВЕР, ЕСЛИ ТЕКУЩИЙ ПЛОХО РАБОТАЕТ 🔄 Поддержка — Нажмите сюда"
ANNOUNCE_EXPIRED = "❌ ПОДПИСКА ИСТЕКЛА! ПРОДЛИТЕ В БОТЕ — ЖМИ СЮДА, ЧТОБЫ ПРОДЛИТЬ🐉"

SUB_INFO_COLOR = "blue"
SUB_INFO_ACTIVE = "⚠️ ВЫБЕРИТЕ ДРУГОЙ СЕРВЕР, ЕСЛИ ТЕКУЩИЙ ПЛОХО РАБОТАЕТ 🔄"
SUB_INFO_BUTTON_ACTIVE = "Поддержка 💬"
SUB_INFO_EXPIRED = "❌ ПОДПИСКА ИСТЕКЛА. ПРОДЛИТЕ В БОТЕ 🐉"
SUB_INFO_BUTTON_EXPIRED = "Продлить в боте 🐉"


def _build_subscription_body(keys: list[str], *, is_active: bool) -> str:
    """Собирает тело подписки: #-мета сверху, ключи, #announce и #announce-url в конце."""
    if is_active:
        announce_url = SUPPORT_URL_ACTIVE
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_ACTIVE}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_ACTIVE}",
            f"#sub-info-button-link: {SUPPORT_URL_ACTIVE}",
            f"#profile-title: {PROFILE_TITLE}",
        ]
        announce = ANNOUNCE_ACTIVE
    else:
        announce_url = BOT_URL_EXPIRED
        meta = [
            f"#sub-info-color: {SUB_INFO_COLOR}",
            f"#sub-info-text: {SUB_INFO_EXPIRED}",
            f"#sub-info-button-text: {SUB_INFO_BUTTON_EXPIRED}",
            f"#sub-info-button-link: {BOT_URL_EXPIRED}",
            f"#profile-title: {PROFILE_TITLE} — Истекла",
        ]
        announce = ANNOUNCE_EXPIRED

    lines = meta + [""] + keys + [
        "",
        f"#announce: {_b64(announce)}",
        f"#announce-url: {announce_url}",
    ]
    return "\n".join(lines)


@app.get("/sub/{encrypted_part}")
async def get_subscription(encrypted_part: str, db: Session = Depends(get_db)):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    subscription = await methods.get_subscription_by_user_and_sub_id(db, user_id, sub_id)
    is_active = _subscription_is_active(subscription)
    expire_unix = _expire_unix(subscription)

    if not is_active:
        stub_uuid = str(uuid.uuid4())
        stub_key = (
            f"vless://{stub_uuid}@127.0.0.1:8443"
            "?type=tcp&encryption=none&security=reality#ИСТЕКЛА😢"
        )
        body = _build_subscription_body([stub_key], is_active=False)
        encoded_subscription = base64.b64encode(body.encode()).decode()
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "Profile-Title": _b64(PROFILE_TITLE),
            "Profile-Update-Interval": "1",
            "Subscription-Userinfo": _build_userinfo(expire=expire_unix),
            "Support-Url": BOT_URL_EXPIRED,
            "Announce": _b64(ANNOUNCE_EXPIRED),
            "Announce-Url": BOT_URL_EXPIRED,
            "Content-Length": str(len(encoded_subscription)),
        }
        return Response(content=encoded_subscription, headers=headers)

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

    # Параллельно: наши сервера + внешняя подписка (таймаут 3 сек)
    server_tasks = [fetch_one(s) for s in servers]
    external_task = fetch_external_subscription_keys(EXTERNAL_SUB_URL)
    server_results, external_keys = await asyncio.gather(
        asyncio.gather(*server_tasks),
        external_task,
    )
    keys = [k for key_list in server_results for k in key_list] + list(external_keys)
    body = _build_subscription_body(keys, is_active=True)
    encoded_subscription = base64.b64encode(body.encode()).decode()

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": _b64(PROFILE_TITLE),
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": _build_userinfo(expire=expire_unix),
        "Support-Url": SUPPORT_URL_ACTIVE,
        "Announce": _b64(ANNOUNCE_ACTIVE),
        "Announce-Url": SUPPORT_URL_ACTIVE,
        "Content-Length": str(len(encoded_subscription)),
    }
    return Response(content=encoded_subscription, headers=headers)


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
    external_keys = await fetch_external_subscription_keys(EXTERNAL_SUB_URL)
    all_keys = [k for r in server_results for k in r["keys"]] + list(external_keys)
    server_infos = [{"server_ip": r["server_ip"], "name": r["name"]} for r in server_results]
    return {
        "keys": all_keys,
        "servers": server_infos,
    }


@app.get("/import/iphone/{encrypted_part}")
async def get_subscription(encrypted_part: str):
    redirect_url = f"v2raytun://import/https://skydragonvpn.ru/sub/{encrypted_part}"

    # Возвращаем редирект
    return RedirectResponse(url=redirect_url, status_code=302)


@app.get("/import/android/{encrypted_part}")
async def get_subscription(encrypted_part: str):
    # Формируем ссылку для редиректа
    redirect_url = f"v2raytun://import/https://skydragonvpn.ru/sub/{encrypted_part}"

    # Возвращаем редирект
    return RedirectResponse(url=redirect_url, status_code=302)


def encode_numbers(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
    data = f"{user_id},{sub_id}"

    checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]

    combined = f"{data}|{checksum}"

    encoded = base64.b64encode(combined.encode()).decode()

    return encoded


def decrypt_part(encrypted_data: str) -> str:
    """Дешифрует данные."""
    decrypted_data = cipher.decrypt(encrypted_data.encode())
    return decrypted_data.decode('utf-8')
