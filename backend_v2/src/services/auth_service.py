import re

from src.core.exceptions import AuthenticationError, ConflictError
from src.domain.entities.account import Account
from src.interfaces.repositories.account import IAccountRepository
from src.interfaces.services.jwt_tokens import IJwtAccessTokenService
from src.interfaces.services.password_hasher import IPasswordHasher


class AuthService:
    __slots__ = ("_accounts", "_passwords", "_jwt")

    def __init__(
        self,
        account_repo: IAccountRepository,
        password_hasher: IPasswordHasher,
        jwt_service: IJwtAccessTokenService,
    ) -> None:
        self._accounts = account_repo
        self._passwords = password_hasher
        self._jwt = jwt_service

    async def register(
        self,
        *,
        email: str | None,
        phone: str | None,
        password: str,
        first_name: str,
        last_name: str,
    ) -> tuple[Account, str]:
        email_norm = email.strip().lower() if email else None
        phone_norm = _normalize_phone(phone)
        if email_norm and await self._accounts.get_by_email_lower(email_norm):
            raise ConflictError("Аккаунт с таким email уже существует")
        if phone_norm and await self._accounts.get_by_phone(phone_norm):
            raise ConflictError("Аккаунт с таким телефоном уже существует")

        password_hash = self._passwords.hash_password(password)
        account = await self._accounts.create(
            email=email_norm,
            phone=phone_norm,
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
        )
        token = self._jwt.issue(account.id)
        return account, token

    async def login(self, login: str, password: str) -> tuple[Account, str]:
        raw = login.strip()
        if not raw:
            raise AuthenticationError("Неверные учётные данные")
        account: Account | None
        if "@" in raw:
            account = await self._accounts.get_by_email_lower(raw.lower())
        else:
            phone = _normalize_phone(raw)
            account = await self._accounts.get_by_phone(phone) if phone else None
        if account is None or not self._passwords.verify(account.password_hash, password):
            raise AuthenticationError("Неверные учётные данные")
        token = self._jwt.issue(account.id)
        return account, token

    async def update_profile(
        self,
        account_id: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> Account:
        return await self._accounts.update_profile(
            account_id=account_id,
            first_name=first_name,
            last_name=last_name,
        )

    async def require_account(self, access_token: str) -> Account:
        account_id = self._jwt.parse_account_id(access_token)
        account = await self._accounts.get_by_id(account_id)
        if account is None:
            raise AuthenticationError("Недействительный токен")
        return account


def _normalize_phone(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    digits = re.sub(r"\D", "", s)
    if not digits:
        return None
    if s.startswith("+") or s.startswith("00"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+7{digits}"
    if len(digits) == 11 and digits.startswith("8"):
        return f"+7{digits[1:]}"
    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits}"
    return f"+{digits}" if not s.startswith("+") else f"+{digits}"
