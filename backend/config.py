"""Application configuration loaded from environment.

Single source of truth for every env var referenced anywhere in the backend.
Fails fast at import time if DATABASE_URL or SECRET_KEY is missing — running
the app with bad config is worse than not starting (PRD NFR-005).
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str = Field(min_length=16)
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    GRAPH_TENANT_ID: str = ""
    GRAPH_CLIENT_ID: str = ""
    GRAPH_CLIENT_SECRET: str = ""
    GRAPH_SENDER_EMAIL: str = ""

    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def graph_configured(self) -> bool:
        return bool(self.GRAPH_TENANT_ID and self.GRAPH_CLIENT_ID and self.GRAPH_CLIENT_SECRET)


@lru_cache
def get_settings() -> Settings:
    return Settings()
