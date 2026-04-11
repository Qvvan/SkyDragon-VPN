"""Прикладные сервисы (зависят от репозиториев и инфраструктуры)."""

from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.core.container.repositories import RepositoryContainer
from src.core.logger import AppLogger
from src.infrastructure.payment import YooKassaPaymentGatewayClient
from src.infrastructure.security import FernetTokenCodec
from src.infrastructure.security.argon2_password_hasher import Argon2PasswordHasher
from src.infrastructure.security.bot_api_secret_verifier import BotApiSecretVerifier
from src.infrastructure.security.jwt_access_token_service import JwtAccessTokenService
from src.infrastructure.subscription import HttpSubscriptionClient
from src.interfaces.clients.payment.client import IPaymentGatewayClient
from src.interfaces.services.bot_api_secret_verifier import IBotApiSecretVerifier
from src.interfaces.services.jwt_tokens import IJwtAccessTokenService
from src.interfaces.services.password_hasher import IPasswordHasher
from src.interfaces.services.token_codec import ITokenCodec
from src.services import ImportService, PaymentService, ServicePlanService, SubscriptionService
from src.services.auth_service import AuthService
from src.services.telegram_account_link_service import TelegramAccountLinkService


class ServiceContainer:
    """Ленивая инициализация сервисов."""

    __slots__ = (
        "_config",
        "_logger",
        "_infra",
        "_repos",
        "_token_codec",
        "_subscription_client",
        "_payment_gateway",
        "_subscription_service",
        "_import_service",
        "_payment_service",
        "_service_plan_service",
        "_password_hasher",
        "_jwt_access_token_service",
        "_auth_service",
        "_telegram_account_link_service",
        "_bot_api_secret_verifier",
    )

    def __init__(
            self,
            config: Config,
            logger: AppLogger,
            infra: InfrastructureContainer,
            repos: RepositoryContainer,
    ) -> None:
        self._config = config
        self._logger = logger
        self._infra = infra
        self._repos = repos
        self._token_codec: ITokenCodec | None = None
        self._subscription_client: HttpSubscriptionClient | None = None
        self._payment_gateway: IPaymentGatewayClient | None = None
        self._subscription_service: SubscriptionService | None = None
        self._import_service: ImportService | None = None
        self._payment_service: PaymentService | None = None
        self._service_plan_service: ServicePlanService | None = None
        self._password_hasher: IPasswordHasher | None = None
        self._jwt_access_token_service: IJwtAccessTokenService | None = None
        self._auth_service: AuthService | None = None
        self._telegram_account_link_service: TelegramAccountLinkService | None = None
        self._bot_api_secret_verifier: IBotApiSecretVerifier | None = None

    @property
    def token_codec(self) -> ITokenCodec:
        if not self._token_codec:
            crypto_key = self._config.app.CRYPTO_KEY.get_secret_value() or self._config.app.SECRET_KEY.get_secret_value()
            self._token_codec = FernetTokenCodec(crypto_key)
        return self._token_codec

    @property
    def subscription_client(self) -> HttpSubscriptionClient:
        if not self._subscription_client:
            self._subscription_client = HttpSubscriptionClient(default_sub_port=self._config.app.SUB_PORT)
        return self._subscription_client

    @property
    def payment_gateway(self) -> IPaymentGatewayClient | None:
        if self._payment_gateway is None:
            shop_id = self._config.app.YOOKASSA_SHOP_ID.strip()
            secret = self._config.app.YOOKASSA_SECRET_KEY.get_secret_value().strip()
            if shop_id and secret:
                self._payment_gateway = YooKassaPaymentGatewayClient(account_id=shop_id, secret_key=secret)
        return self._payment_gateway

    @property
    def subscription_service(self) -> SubscriptionService:
        if not self._subscription_service:
            self._subscription_service = SubscriptionService(
                config=self._config,
                subscription_repo=self._repos.subscription_repository,
                server_repo=self._repos.server_repository,
                service_repo=self._repos.service_plan_repository,
                subscription_client=self.subscription_client,
                token_codec=self.token_codec,
            )
        return self._subscription_service

    @property
    def import_service(self) -> ImportService:
        if not self._import_service:
            self._import_service = ImportService(config=self._config)
        return self._import_service

    @property
    def payment_service(self) -> PaymentService:
        if not self._payment_service:
            self._payment_service = PaymentService(
                telegram_yookassa_return_url=self._config.app.TELEGRAM_YOOKASSA_RETURN_URL,
                service_repo=self._repos.service_plan_repository,
                payment_repo=self._repos.payment_repository,
                gateway=self.payment_gateway,
                token_codec=self.token_codec,
            )
        return self._payment_service

    @property
    def service_plan_service(self) -> ServicePlanService:
        if not self._service_plan_service:
            self._service_plan_service = ServicePlanService(
                service_plan_repo=self._repos.service_plan_repository,
            )
        return self._service_plan_service

    @property
    def password_hasher(self) -> IPasswordHasher:
        if not self._password_hasher:
            self._password_hasher = Argon2PasswordHasher()
        return self._password_hasher

    @property
    def jwt_access_token_service(self) -> IJwtAccessTokenService:
        if not self._jwt_access_token_service:
            self._jwt_access_token_service = JwtAccessTokenService(
                secret=self._config.app.SECRET_KEY.get_secret_value(),
                expire_minutes=self._config.app.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            )
        return self._jwt_access_token_service

    @property
    def auth_service(self) -> AuthService:
        if not self._auth_service:
            self._auth_service = AuthService(
                account_repo=self._repos.account_repository,
                password_hasher=self.password_hasher,
                jwt_service=self.jwt_access_token_service,
            )
        return self._auth_service

    @property
    def telegram_account_link_service(self) -> TelegramAccountLinkService:
        if not self._telegram_account_link_service:
            self._telegram_account_link_service = TelegramAccountLinkService(
                link_repo=self._repos.account_telegram_link_repository,
            )
        return self._telegram_account_link_service

    @property
    def bot_api_secret_verifier(self) -> IBotApiSecretVerifier:
        if not self._bot_api_secret_verifier:
            self._bot_api_secret_verifier = BotApiSecretVerifier(self._config.app.BOT_API_SECRET)
        return self._bot_api_secret_verifier
