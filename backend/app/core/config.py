"""从环境变量载入 API 配置，集中提供 Settings 入口。"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, Set

from pydantic import Field, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url


ASYNC_DRIVER_MAPPING = {
    "sqlite+aiosqlite": "sqlite",
    "postgresql+asyncpg": "postgresql+psycopg",
    "mysql+aiomysql": "mysql+pymysql",
}

class Settings(BaseSettings):
    """FastAPI 后端的统一配置容器。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development")
    app_name: str = Field(default="Safefood Platform API")
    app_version: str = Field(default="1.0.0")

    database_url: str = Field(default="sqlite+aiosqlite:///./dev.db")
    sql_echo: bool = Field(default=False)

    jwt_secret_key: str = Field(default="change-me-change-me-change-me-change-me")
    jwt_algorithm: str = Field(default="HS256")

    access_token_expire_minutes: int = Field(default=60, ge=5)
    refresh_token_expire_days: int = Field(default=7, ge=1)

    allowed_app_clients: List[str] = Field(default_factory=lambda: ["exec_app", "exec_web", "reg_app", "reg_web"])

    default_tenant_id: int = Field(default=1, ge=1)
    default_org_id: int = Field(default=1, ge=1)

    oidc_issuer: Optional[str] = None
    oidc_jwks_url: Optional[str] = None
    oidc_client_id: Optional[str] = None

    image_upload_dir: str = Field(default="storage/uploads")
    public_base_url: Optional[str] = None
    file_public_token_expire_seconds: int = Field(default=3600, ge=60)

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: Optional[str] = None

    hikvision_client_id: Optional[str] = None
    hikvision_client_secret: Optional[str] = None
    hikvision_oauth_url: str = Field(default="https://api2.hik-cloud.com/oauth/token")
    hikvision_oauth_scope: str = Field(default="app")
    hikvision_oauth_timeout_seconds: int = Field(default=10, ge=1)

    mqtt_broker: str = Field(default="localhost")
    mqtt_port: int = Field(default=1883)
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_client_id: str = Field(default="food_safety_backend")
    mqtt_topic: str = Field(default="aibox/+/alarm")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        if value not in {"development", "staging", "production"}:
            raise ValueError("environment 仅支持 development/staging/production")
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, value: str, info: ValidationInfo) -> str:
        env = info.data.get("environment", "development")
        if len(value) < 32:
            raise ValueError("jwt_secret_key 至少需要 32 个字符")
        if env == "production" and value.startswith("change-me"):
            raise ValueError("production 环境必须提供自定义 JWT 密钥")
        return value

    @field_validator("allowed_app_clients", mode="after")
    @classmethod
    def normalize_app_clients(cls, values: List[str]) -> List[str]:
        normalized = [item.strip() for item in values if item and item.strip()]
        if not normalized:
            raise ValueError("allowed_app_clients 至少需要一个客户端标识")
        return normalized

    @computed_field  # type: ignore[misc]
    @property
    def allowed_app_clients_set(self) -> Set[str]:
        return set(self.allowed_app_clients)

    @computed_field  # type: ignore[misc]
    @property
    def has_oidc(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_jwks_url)

    @computed_field  # type: ignore[misc]
    @property
    def sync_database_url(self) -> str:
        url = make_url(self.database_url)
        driver = url.drivername
        sync_driver = ASYNC_DRIVER_MAPPING.get(driver)
        if not sync_driver and "+" in driver:
            sync_driver = driver.split("+", 1)[0]
        if not sync_driver:
            sync_driver = driver
        sync_url = url.set(drivername=sync_driver)
        return str(sync_url)

    # 兼容旧代码中的大写配置访问
    @property
    def APP_NAME(self) -> str:  # noqa: N802
        return self.app_name

    @property
    def APP_VERSION(self) -> str:  # noqa: N802
        return self.app_version

    @property
    def DEBUG(self) -> bool:  # noqa: N802
        return self.environment == "development"

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return self.database_url

    @property
    def JWT_SECRET_KEY(self) -> str:  # noqa: N802
        return self.jwt_secret_key

    @property
    def JWT_ALGORITHM(self) -> str:  # noqa: N802
        return self.jwt_algorithm

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:  # noqa: N802
        return self.access_token_expire_minutes

    @property
    def JWT_REFRESH_TOKEN_EXPIRE_MINUTES(self) -> int:  # noqa: N802
        return self.refresh_token_expire_days * 24 * 60

    @property
    def IMAGE_UPLOAD_DIR(self) -> str:  # noqa: N802
        return self.image_upload_dir


@lru_cache
def get_settings() -> Settings:
    """返回缓存的 Settings，避免重复解析环境变量。"""
    return Settings()


settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
