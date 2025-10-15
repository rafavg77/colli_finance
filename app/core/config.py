from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    app_name: str = Field(alias="APP_NAME")
    service_name: str = Field(alias="SERVICE_NAME")
    environment: str = Field(alias="ENVIRONMENT")
    database_use: Literal["dev", "prod"] = Field(alias="DATABASE_USE")
    database_url_dev: str = Field(alias="DATABASE_URL_DEV")
    database_url_prod: str = Field(alias="DATABASE_URL_PROD")
    database_echo: bool = Field(alias="DATABASE_ECHO", default=False)
    migrate_on_start: bool = Field(alias="MIGRATE_ON_START", default=True)
    reset_db_on_start: bool = Field(alias="RESET_DB_ON_START", default=False)
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
    loki_url: str = Field(alias="LOKI_URL")
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return self.database_url_prod if self.database_use == "prod" else self.database_url_dev


class LogContext(BaseModel):
    user: str | None = None
    event: str | None = None
    duration_ms: int | None = None
    status_code: int | None = None
    extra: dict | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
