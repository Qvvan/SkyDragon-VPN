from src.core.config import Config
from src.core.logger import AppLogger
from src.infrastructure.postgres.connection import PostgresConnectionPool
from src.infrastructure.postgres.query_executor import PostgresQueryExecutor
from src.infrastructure.redis.client import RedisClient
from src.infrastructure.ssms import SsmsClient
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.clients.redis.client import IRedisClient
from src.interfaces.clients.sms.client import ISmsVerificationClient


class InfrastructureContainer:
    __slots__ = (
        "_config",
        "_logger",
        "_postgres",
        "_query_executor",
        "_redis_client",
        "_ssms_client",
    )

    def __init__(self, config: Config, logger: AppLogger) -> None:
        self._config = config
        self._logger = logger
        self._postgres: PostgresConnectionPool | None = None
        self._query_executor: PostgresQueryExecutor | None = None
        self._redis_client: RedisClient | None = None
        self._ssms_client: ISmsVerificationClient | None = None

    @property
    def postgres_db(self) -> PostgresConnectionPool:
        if not self._postgres:
            self._postgres = PostgresConnectionPool(
                host=self._config.postgres.HOST,
                port=self._config.postgres.PORT,
                database=self._config.postgres.DATABASE,
                user=self._config.postgres.USER,
                password=self._config.postgres.PASSWORD.get_secret_value(),
                echo=self._config.postgres.ECHO,
                pool_size=self._config.postgres.POOL_SIZE,
                max_overflow=self._config.postgres.MAX_OVERFLOW,
                app_logger=self._logger,
            )
        return self._postgres

    @property
    def query_executor(self) -> IQueryExecutor:
        if not self._query_executor:
            self._query_executor = PostgresQueryExecutor(
                connection_pool=self.postgres_db
            )
        return self._query_executor

    @property
    def redis_client(self) -> IRedisClient:
        if not self._redis_client:
            self._redis_client = RedisClient(url=self._config.redis.URL)
        return self._redis_client

    @property
    def ssms_client(self) -> ISmsVerificationClient:
        if not self._ssms_client:
            ss = self._config.ssms
            self._ssms_client = SsmsClient(
                api_url=ss.API_URL,
                email=ss.EMAIL,
                password=ss.PASSWORD.get_secret_value(),
                api_key=ss.API_KEY.get_secret_value(),
                call_protection_seconds=ss.CALL_PROTECTION_SECONDS,
                logger=self._logger,
            )
        return self._ssms_client

    async def close(self) -> None:
        if self._postgres:
            await self._postgres.close()
        if self._redis_client:
            await self._redis_client.close()
        if self._ssms_client is not None:
            await self._ssms_client.close()
