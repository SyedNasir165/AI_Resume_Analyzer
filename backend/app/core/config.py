from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env.

    Gemini fields are still optional — a later phase depends on them. Supabase fields are
    now required for the app to be useful: supabase_url is used to build the JWKS URL that
    verifies login tokens (asymmetric keys, so no shared secret needed), database_url is the
    Postgres connection, and supabase_service_role_key is reserved for a future phase that
    needs Supabase's Auth Admin API (e.g. account deletion).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    cors_origins: str = "http://localhost:5175"

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

    database_url: str | None = None

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"

    # Per-user AI request budget per rolling minute (analysis + coach endpoints).
    ai_rate_limit_per_minute: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
