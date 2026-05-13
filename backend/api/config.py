"""Application settings loaded from environment / .env file."""

from __future__ import annotations

import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""

    # Sensing
    snapshot_interval_seconds: int = 600
    snapshot_interval_min: int = 300
    snapshot_interval_max: int = 900

    # Privacy
    edge_ai_only: bool = True
    retain_raw_image_seconds: int = 0

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/focus_guardian.db"

    # Serverless (Vercel): disables background scheduler
    is_serverless: bool = False

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    def model_post_init(self, __context: object) -> None:
        if isinstance(self.cors_origins, str):
            object.__setattr__(self, "cors_origins", json.loads(self.cors_origins))


settings = Settings()
