"""Application configuration, loaded from environment / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Upstream providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Redis / cache
    redis_url: str = "redis://localhost:6379/0"
    cache_similarity_threshold: float = 0.95

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3000"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # App
    log_level: str = "INFO"
    environment: str = "local"


def get_settings() -> Settings:
    """Return application settings. A function so tests can override it cleanly."""
    return Settings()
