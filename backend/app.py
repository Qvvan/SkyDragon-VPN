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
from get_sub import BaseKeyManager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cipher = Fernet(CRYPTO_KEY)


@app.get("/sub/{encrypted_part}")
async def get_subscription(encrypted_part: str, db: Session = Depends(get_db)):
    try:
        data = decrypt_part(encrypted_part)
        user_id = int(data.split("|")[0])
        sub_id = int(data.split("|")[1])
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    encrypted_part = encode_numbers(user_id, sub_id)
    servers = await methods.get_server(db)
    keys = []

    for server in servers:
        try:
            base = BaseKeyManager(server.server_ip)
            sub = await base._get_sub_3x_ui(encrypted_part)
            if sub is None:
                continue
            sub = sub.replace("localhost", server.server_ip)
            sub = sub.replace(sub[sub.find("#") + 1:], server.name + " - VLESS")
            sub = re.sub(r'&spx=[^&]*', '', sub)
            keys.append(sub)
        except Exception as e:
            print(f"Error getting subscription for server {server.server_ip}: {e}")

    encoded_subscription = base64.b64encode("\n".join(keys).encode()).decode()

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": "SkyDragon",
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
        "Content-Length": str(len(encoded_subscription))
    }

    return Response(content=encoded_subscription, headers=headers)


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
