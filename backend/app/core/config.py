"""
CatalogIQ â€“ Application Settings
Uses pydantic-settings for typed, env-driven configuration.
"""
from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "CatalogIQ"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "sqlite+aiosqlite:///./catalogiq.db"

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Pipeline
    confidence_threshold: float = 0.85
    batch_concurrency: int = 10
    max_upload_bytes: int = 50 * 1_048_576  # 50 MB

    # Rate limiting (requests per minute per IP)
    rate_limit_rpm: int = 60


settings = Settings()

