import asyncio
import base64
import hashlib
import re

from cryptography.fernet import Fernet
from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from cfg.config import CRYPTO_KEY
from db import methods
from db.db import get_db
from sub_fetcher import get_sub_from_server

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


@app.get("/sub/{encrypted_part}")
async def get_subscription(encrypted_part: str, db: Session = Depends(get_db)):
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
            if sub is None:
                return []
            return _decode_sub_to_keys(
                sub, server.server_ip, server.name or server.server_ip
            )
        except Exception as e:
            print(f"Error getting subscription for server {server.server_ip}: {e}")
            return []

    results = await asyncio.gather(*[fetch_one(s) for s in servers])
    keys = [k for key_list in results for k in key_list]
    encoded_subscription = base64.b64encode("\n".join(keys).encode()).decode()

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": "SkyDragon",
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
        "Content-Length": str(len(encoded_subscription))
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

    results = await asyncio.gather(*[fetch_one(s) for s in servers])
    all_keys = [k for r in results for k in r["keys"]]
    server_infos = [{"server_ip": r["server_ip"], "name": r["name"]} for r in results]
    return {
        "keys": all_keys,
        "servers": server_infos,
    }


@app.get("/import/iphone/{encrypted_part}")
async def get_subscription(encrypted_part: str):
    redirect_url = f"streisand://import/https://skydragonvpn.ru/sub/{encrypted_part}"

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
