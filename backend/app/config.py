from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    database_url: str = "postgresql+asyncpg://civicpulse:civicpulse@database:5432/civicpulse"
    redis_url: str = "redis://cache:6379/0"
    environment: str = "development"

    # Triage
    triage_provider: str = "simulated"  # simulated | llm | ollama | rules
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.1-8b-instant"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:1b"
    triage_timeout_seconds: float = 10.0
    triage_cache_ttl_seconds: int = 24 * 60 * 60

    # Cache / rate limit
    stats_cache_ttl_seconds: int = 30
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 10

    # CORS
    cors_allow_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
