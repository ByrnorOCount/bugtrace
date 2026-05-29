from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "bugtrace"
    database_url: str = Field(default="", alias="DATABASE_URL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    seed_record_count: int = Field(default=50, alias="SEED_RECORD_COUNT")
    enable_mock_fallback: bool = Field(default=True, alias="ENABLE_MOCK_FALLBACK")
    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_allow_download: bool = Field(default=False, alias="EMBEDDING_ALLOW_DOWNLOAD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
