import json
import os
from pathlib import Path
from typing import Annotated, get_args, get_origin

from typing_extensions import Self

import yaml
from dotenv import load_dotenv
from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


class PostgresConfig(ConfigBase):
    """PostgreSQL: либо DSN целиком (legacy DSN из .env), либо HOST/PORT/DATABASE/USER/PASSWORD."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", frozen=True)

    DSN: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DSN", "POSTGRES_DSN"),
    )
    HOST: str = "127.0.0.1"
    PORT: int = 5432
    DATABASE: str = "postgres"
    USER: str = "postgres"
    PASSWORD: SecretStr = SecretStr("")

    ECHO: bool = False
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10

    @model_validator(mode="after")
    def _dsn_or_password(self) -> Self:
        dsn = self.DSN.get_secret_value().strip() if self.DSN else ""
        if dsn:
            return self
        if not self.PASSWORD.get_secret_value():
            raise ValueError("Задайте POSTGRES_DSN/DSN или POSTGRES_PASSWORD и параметры подключения")
        return self


class LoggingConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="LOG_", frozen=True)

    LEVEL: str = "INFO"
    JSON_FORMAT: bool = True


class AppConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="APP_", frozen=True)

    NAME: str = "SkyDragon VPN API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 12345
    SECRET_KEY: SecretStr = SecretStr("dev-secret-change-in-production")
    PUBLIC_BASE_URL: str = ""
    FERNET_KEY: SecretStr = Field(
        ...,
        validation_alias=AliasChoices("CRYPTO_KEY", "APP_FERNET_KEY"),
        description="Ключ Fernet для ссылок /sub/...",
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
        ],
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            raw = v.strip()
            if not raw:
                return []
            if raw.startswith("["):
                return json.loads(raw)
            return [p.strip() for p in raw.split(",") if p.strip()]
        return v


class SubscriptionConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="SUBSCRIPTION_", frozen=True)

    SUB_PORT: int = 2096
    SUPPORT_URL_ACTIVE: str = "https://t.me/SkyDragonSupport"
    BOT_URL_EXPIRED: str = "https://t.me/SkyDragonVPNBot?start=1"
    STATUS_ACTIVE_LABEL: str = "активная"
    PROFILE_TITLE: str = "SkyDragon🐉"
    EXTERNAL_SUB_URLS: list[str] = Field(
        default_factory=lambda: [
            "https://sp.vpnlider.online/ndKFYzNwuk2ryHba",
            "https://link.1cdn.lol/QKLZy",
        ],
    )

    @field_validator("EXTERNAL_SUB_URLS", mode="before")
    @classmethod
    def _parse_external_urls(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            raw = v.strip()
            if not raw:
                return []
            if raw.startswith("["):
                return [str(x).strip() for x in json.loads(raw) if str(x).strip()]
            return [p.strip() for p in raw.split(",") if p.strip()]
        return v


class YookassaConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="YOOKASSA_", frozen=True)

    SHOP_ID: str = Field(default="", validation_alias=AliasChoices("YOOKASSA_SHOP_ID", "SHOP_ID"))
    SECRET_KEY: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("YOOKASSA_SECRET_KEY", "SHOP_API_TOKEN"),
    )


class JWTConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="JWT_", frozen=True)

    SECRET_KEY: SecretStr = SecretStr("jwt-not-used-in-vpn-sub-app")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class SsmsConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="SSMS_", frozen=True)

    API_URL: str = "http://api2.ssms.su"
    EMAIL: str = ""
    PASSWORD: SecretStr = SecretStr("")
    API_KEY: SecretStr = SecretStr("")
    CALL_PROTECTION_SECONDS: int = 200
    SMS_SENDER_NAME: str = "Flokify"
    SMS_PRIORITY: int = 2
    WEBHOOK_SECRET: SecretStr = SecretStr("")
    REDIS_KEY_TTL: int = 120
    SMS_CODE_TTL: int = 300


class AuthConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="AUTH_", frozen=True)

    MAX_VERIFICATION_ATTEMPTS: int = 5
    BLOCK_DURATION_MINUTES: int = 30
    EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS: int = 60
    PHONE_REGISTRATION_REQUIRE_CONFIRMATION: bool = True


class Config(ConfigBase):
    app: AppConfig = Field(default_factory=AppConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    subscription: SubscriptionConfig = Field(default_factory=SubscriptionConfig)
    yookassa: YookassaConfig = Field(default_factory=YookassaConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    ssms: SsmsConfig = Field(default_factory=SsmsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

    @classmethod
    def load(cls, env_file: str | Path = ".env", yaml_file: str | Path = "config.yaml") -> "Config":
        env_path = Path(env_file).resolve()
        yaml_path = Path(yaml_file).resolve()

        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

        if yaml_path.exists():
            with open(yaml_path, encoding="utf-8") as f:
                yaml_cfg: dict = yaml.safe_load(f) or {}
            for section, values in yaml_cfg.items():
                prefix = _yaml_section_env_prefixes().get(section, f"{section.upper()}_")
                if isinstance(values, dict):
                    for key, value in values.items():
                        env_key = f"{prefix}{key.upper()}"
                        if isinstance(value, (list, dict)):
                            os.environ.setdefault(env_key, json.dumps(value, ensure_ascii=False))
                        elif isinstance(value, bool):
                            os.environ.setdefault(env_key, "true" if value else "false")
                        else:
                            os.environ.setdefault(env_key, str(value))

        return cls()


def _yaml_section_env_prefixes() -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for section_name, field_info in Config.model_fields.items():
        ann = field_info.annotation
        if get_origin(ann) is Annotated:
            ann = get_args(ann)[0]
        if not isinstance(ann, type) or not issubclass(ann, ConfigBase):
            continue
        raw_cfg = ann.model_config
        env_prefix = (
            raw_cfg.get("env_prefix")
            if isinstance(raw_cfg, dict)
            else getattr(raw_cfg, "env_prefix", None)
        )
        prefixes[section_name] = str(env_prefix) if env_prefix else f"{section_name.upper()}_"
    return prefixes
