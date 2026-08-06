"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with Docker-friendly local defaults."""

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

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
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "LEGAL_MONITOR_OPENAI_API_KEY"),
    )
    openai_model: str = Field(
        default="gpt-5.6-luna",
        validation_alias=AliasChoices("LEGAL_MONITOR_OPENAI_MODEL", "OPENAI_MODEL"),
    )
    openai_reasoning_effort: Literal[
        "none", "low", "medium", "high", "xhigh", "max"
    ] = Field(
        default="low",
        validation_alias=AliasChoices(
            "LEGAL_MONITOR_OPENAI_REASONING_EFFORT", "OPENAI_REASONING_EFFORT"
        ),
    )
    openai_analysis_instructions: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENAI_ANALYSIS_INSTRUCTIONS", "LEGAL_MONITOR_OPENAI_ANALYSIS_INSTRUCTIONS"
        ),
    )
    openai_evidence_protocol: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "OPENAI_ANALYSIS_EVIDENCE_PROTOCOL",
            "LEGAL_MONITOR_OPENAI_EVIDENCE_PROTOCOL",
        ),
    )


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings instance per process."""
    return Settings()
