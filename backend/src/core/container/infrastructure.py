"""Инфраструктурные клиенты: Postgres, HTTP."""

from core.config import Config
from core.logger import AppLogger
from infrastructure.http.vpn_subscription_transport import AiohttpVpnSubscriptionTransport
from infrastructure.http.yookassa_gateway import YookassaPaymentGateway
from infrastructure.postgres.connection import PostgresConnectionPool
from infrastructure.postgres.query_executor import PostgresQueryExecutor
from interfaces.clients.db.query_executor import IQueryExecutor


class InfrastructureContainer:
    __slots__ = (
        "_config",
        "_logger",
        "_postgres",
        "_query_executor",
        "_vpn_transport",
        "_yookassa",
    )

    def __init__(self, config: Config, logger: AppLogger) -> None:
        self._config = config
        self._logger = logger
        self._postgres: PostgresConnectionPool | None = None
        self._query_executor: PostgresQueryExecutor | None = None
        self._vpn_transport: AiohttpVpnSubscriptionTransport | None = None
        self._yookassa: YookassaPaymentGateway | None = None

    @property
    def postgres_db(self) -> PostgresConnectionPool:
        if not self._postgres:
            pc = self._config.postgres
            dsn = pc.DSN.get_secret_value().strip() if pc.DSN else ""
            if dsn:
                self._postgres = PostgresConnectionPool(
                    dsn=dsn,
                    echo=pc.ECHO,
                    pool_size=pc.POOL_SIZE,
                    max_overflow=pc.MAX_OVERFLOW,
                    app_logger=self._logger,
                )
            else:
                self._postgres = PostgresConnectionPool(
                    host=pc.HOST,
                    port=pc.PORT,
                    database=pc.DATABASE,
                    user=pc.USER,
                    password=pc.PASSWORD.get_secret_value(),
                    echo=pc.ECHO,
                    pool_size=pc.POOL_SIZE,
                    max_overflow=pc.MAX_OVERFLOW,
                    app_logger=self._logger,
                )
        return self._postgres

    @property
    def query_executor(self) -> IQueryExecutor:
        if not self._query_executor:
            self._query_executor = PostgresQueryExecutor(connection_pool=self.postgres_db)
        return self._query_executor

    @property
    def vpn_subscription_transport(self) -> AiohttpVpnSubscriptionTransport:
        if not self._vpn_transport:
            self._vpn_transport = AiohttpVpnSubscriptionTransport()
        return self._vpn_transport

    @property
    def yookassa_gateway(self) -> YookassaPaymentGateway:
        if not self._yookassa:
            self._yookassa = YookassaPaymentGateway(self._config.yookassa)
        return self._yookassa

    async def close(self) -> None:
        if self._postgres:
            await self._postgres.close()
