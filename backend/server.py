import base64
from fastapi import FastAPI, Depends, Response
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from backend.db import methods
from backend.db.db import get_db
from cfg.config import CRYPTO_KEY

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cipher = Fernet(CRYPTO_KEY)


async def decrypt_part(encrypted_data: str) -> str:
    """Дешифрует данные."""
    decrypted_data = cipher.decrypt(encrypted_data.encode())
    return decrypted_data.decode('utf-8')


@app.get("/sub/{encrypted_part}")
async def get_subscription(encrypted_part: str, db: Session = Depends(get_db)):
    try:
        user_id = int(await decrypt_part(encrypted_part))
    except Exception:
        return Response(content="Invalid encryption", status_code=400)

    keys = await methods.get_user_keys(db, user_id)

    if not keys:
        return Response(content="No keys found", status_code=404)

    encoded_subscription = base64.b64encode("\n".join(keys).encode()).decode()

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Title": "SkyDragon",
        "Profile-Update-Interval": "2",
        "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
        "Content-Length": str(len(encoded_subscription))
    }

    return Response(content=encoded_subscription, headers=headers)

