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
        login: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> tuple[Account, str]:
        login_norm = login.strip().lower()
        if not login_norm:
            raise ConflictError("Логин не может быть пустым")
        if await self._accounts.get_by_login(login_norm):
            raise ConflictError("Аккаунт с таким логином уже существует")

        password_hash = self._passwords.hash_password(password)
        account = await self._accounts.create(
            login=login_norm,
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
        )
        token = self._jwt.issue(account.id)
        return account, token

    async def login(self, login: str, password: str) -> tuple[Account, str]:
        login_norm = login.strip().lower()
        if not login_norm:
            raise AuthenticationError("Неверные учётные данные")
        account = await self._accounts.get_by_login(login_norm)
        if account is None or not self._passwords.verify(account.password_hash, password):
            raise AuthenticationError("Неверные учётные данные")
        token = self._jwt.issue(account.id)
        return account, token

    async def update_profile(
        self,
        account_id: str,
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
