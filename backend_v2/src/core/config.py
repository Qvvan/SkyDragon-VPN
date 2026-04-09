from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


class PostgresConfig(ConfigBase):
    """Настройки базы данных"""
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", frozen=True)

    HOST: str
    PORT: int
    DATABASE: str
    USER: str
    PASSWORD: SecretStr

    ECHO: bool = False
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10


class LoggingConfig(ConfigBase):
    """Настройки логирования"""
    model_config = SettingsConfigDict(env_prefix="LOG_", frozen=True)

    LEVEL: str = "INFO"
    JSON_FORMAT: bool = True


class AppConfig(ConfigBase):
    """Основные настройки приложения"""
    model_config = SettingsConfigDict(env_prefix="APP_", frozen=True)

    NAME: str
    DEBUG: bool
    HOST: str
    PORT: int
    SECRET_KEY: SecretStr
    PUBLIC_BASE_URL: str = ""


class RedisConfig(ConfigBase):
    """Настройки Redis"""
    model_config = SettingsConfigDict(env_prefix="REDIS_", frozen=True)

    URL: str = "redis://b2b_redis:6379/0"


class SsmsConfig(ConfigBase):
    """
    Настройки SSMS API (авторизация входящим звонком wait_call).

    WEBHOOK_SECRET не передаётся в URL hook (не светится в access-логах).
    Ожидается заголовок X-Webhook-Secret на GET /phone-verify-hook, если секрет задан.
    Если провайдер не умеет кастомные заголовки — оставьте секрет пустым и ограничьте
    доступ по IP / на стороне сети.
    """
    model_config = SettingsConfigDict(env_prefix="SSMS_", frozen=True)

    API_URL: str = "http://api2.ssms.su"
    EMAIL: str = ""
    PASSWORD: SecretStr = SecretStr("")
    API_KEY: SecretStr = SecretStr("")
    CALL_PROTECTION_SECONDS: int = 200
    SMS_SENDER_NAME: str
    SMS_PRIORITY: int = 2
    WEBHOOK_SECRET: SecretStr = SecretStr("")
    REDIS_KEY_TTL: int = 120
    SMS_CODE_TTL: int = 300


class Config(ConfigBase):
    """Главный класс конфигурации"""

    app: AppConfig = Field(default_factory=AppConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    ssms: SsmsConfig = Field(default_factory=SsmsConfig)

    @classmethod
    def load(cls, env_file: str | Path = ".env") -> "Config":
        env_path = Path(env_file).resolve()

        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


        return cls()

