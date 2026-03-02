"""
config.py — Centralised settings loaded from environment / .env file.
Single source of truth for all tuneable parameters.
"""
from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── LLM ──────────────────────────────────────────────────────────────
    llm_api_key: str = Field(
        validation_alias=AliasChoices("GROQ_API_KEY", "GROK_API_KEY")
    )
    llm_model: str = Field(
        default="openai/gpt-oss-120b",
        validation_alias=AliasChoices("GROQ_MODEL", "GROK_MODEL"),
    )
    llm_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("GROQ_BASE_URL", "GROK_BASE_URL"),
    )
    llm_temperature: float = 0.2
    llm_max_retries: int = 3

    # ── Search ───────────────────────────────────────────────────────────
    serper_api_key: str
    serper_search_url: str = "https://google.serper.dev/search"
    search_results_per_query: int = 5
    search_cache_ttl_hours: int = 24
    result_freshness_months: int = 24

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # ── Cache ─────────────────────────────────────────────────────────────
    redis_url: str = ""

    # ── Embedding ─────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    cache_similarity_threshold: float = 0.92

    # ── App ───────────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = "change-me"

    # ── CORS ──────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:3001"],
        validation_alias=AliasChoices("ALLOWED_ORIGINS"),
    )

    # ── Rate limiting ─────────────────────────────────────────────────────
    max_concurrent_analyses: int = 2
    analysis_timeout_seconds: int = 120

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — reads .env once at startup."""
    return Settings()