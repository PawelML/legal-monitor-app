"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with Docker-friendly local defaults."""

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = Field(
        default=(
            "postgresql+asyncpg://legal_monitor:legal_monitor@localhost:5432/"
            "legal_monitor"
        ),
        validation_alias=AliasChoices("LEGAL_MONITOR_DATABASE_URL", "DATABASE_URL"),
    )
    eli_base_url: str = Field(
        default="https://api.sejm.gov.pl/eli",
        validation_alias=AliasChoices("LEGAL_MONITOR_ELI_BASE_URL", "ELI_BASE_URL"),
    )


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings instance per process."""
    return Settings()
