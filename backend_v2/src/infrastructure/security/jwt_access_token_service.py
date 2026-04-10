from datetime import datetime, timedelta, timezone

import jwt

from src.core.exceptions import AuthenticationError
from src.interfaces.services.jwt_tokens import IJwtAccessTokenService


class JwtAccessTokenService(IJwtAccessTokenService):
    __slots__ = ("_secret", "_expire_minutes", "_algorithm")

    def __init__(self, secret: str, expire_minutes: int) -> None:
        self._secret = secret
        self._expire_minutes = expire_minutes
        self._algorithm = "HS256"

    def issue(self, account_id: int) -> str:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(account_id),
            "typ": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def parse_account_id(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Недействительный токен") from exc
        if payload.get("typ") != "access":
            raise AuthenticationError("Недействительный токен")
        sub = payload.get("sub")
        if sub is None:
            raise AuthenticationError("Недействительный токен")
        try:
            return int(sub)
        except (TypeError, ValueError) as exc:
            raise AuthenticationError("Недействительный токен") from exc
