"""Прикладные сервисы (зависят от репозиториев и инфраструктуры)."""

from src.core.config import Config
from src.core.container.infrastructure import InfrastructureContainer
from src.core.container.repositories import RepositoryContainer
from src.core.logger import AppLogger
from src.infrastructure.payment import YooKassaPaymentGatewayClient
from src.infrastructure.security import FernetTokenCodec
from src.infrastructure.subscription import HttpSubscriptionClient
from src.interfaces.clients.payment.client import IPaymentGatewayClient
from src.interfaces.services.token_codec import ITokenCodec
from src.services import ImportService, PaymentService, SubscriptionService


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
