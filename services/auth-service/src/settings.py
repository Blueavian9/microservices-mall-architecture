"""Environment — all config from process env (PRD: no hardcoded service URLs)."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    port: int = 3001
    database_url: str | None = None
    jwt_secret: str
    jwt_refresh_secret: str
    nats_url: str | None = None
    allowed_origins: str | None = None
    skip_db: bool = False

    @property
    def cors_origins(self) -> list[str] | None:
        if not self.allowed_origins:
            return None
        parts = [s.strip() for s in self.allowed_origins.split(",") if s.strip()]
        return parts if parts else None

    @model_validator(mode="after")
    def require_database_when_not_skipped(self):
        if not self.skip_db and not self.database_url:
            raise ValueError("DATABASE_URL is required unless SKIP_DB=1")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
