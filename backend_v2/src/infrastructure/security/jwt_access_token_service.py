import re
from datetime import datetime, timedelta, timezone

import jwt

from src.core.exceptions import AuthenticationError
from src.interfaces.services.jwt_tokens import IJwtAccessTokenService

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class JwtAccessTokenService(IJwtAccessTokenService):
    __slots__ = ("_secret", "_expire_minutes", "_algorithm")

    def __init__(self, secret: str, expire_minutes: int) -> None:
        self._secret = secret
        self._expire_minutes = expire_minutes
        self._algorithm = "HS256"

    def issue(self, account_id: str) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": account_id,
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def parse_account_id(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Недействительный токен") from exc
        if payload.get("typ") != "access":
            raise AuthenticationError("Недействительный токен")
        sub = payload.get("sub")
        if not sub or not _UUID_RE.match(str(sub)):
            raise AuthenticationError("Недействительный токен")
        return str(sub)
