from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me"
    # Comma-separated origins accepted; override via ALLOWED_ORIGINS env var
    backend_cors_origins: list[str] = ["http://localhost:3000"]
    allowed_origins: str = ""  # e.g. "https://foo.vercel.app,https://bar.com"

    @property
    def CORS_ORIGINS(self) -> list[str]:  # type: ignore[override]
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        return self.backend_cors_origins

    database_url: str = "postgresql+asyncpg://lecturelens:lecturelens_dev@localhost:5432/lecturelens"

    @property
    def async_database_url(self) -> str:
        """Always returns the asyncpg variant regardless of what Railway injects."""
        url = self.database_url
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Directory where generated audio files are stored
    audio_storage_path: str = "/tmp/lecturelens_audio"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
