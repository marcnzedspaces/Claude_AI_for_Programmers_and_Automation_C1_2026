from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application configuration loaded from environment variables.

    app_name: str = "SupportOps AI"
    app_env: str = "development"

    # These remain optional until the Claude integration phase.
    anthropic_api_key: SecretStr | None = None
    claude_model: str | None = None
    claude_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=120,
    )
    claude_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
    )
    claude_input_cost_per_million_usd: float = Field(
        default=3.0,
        ge=0,
    )
    claude_output_cost_per_million_usd: float = Field(
        default=15.0,
        ge=0,
    )
    log_level: str = "INFO"
    faq_cache_enabled: bool = True
    faq_cache_ttl_seconds: float = Field(
        default=60.0,
        gt=0,
        le=3600,
    )
    faq_cache_max_entries: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    # MongoDB configuration enters the application in Phase 4.
    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongodb_database: str = "supportops_ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    # Return one cached settings object for the process.
    return Settings()
