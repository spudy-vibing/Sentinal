"""
SENTINEL V2 — Configuration
Environment variables and settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # API Keys
    anthropic_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent

    # Agent Settings
    default_model: str = "claude-3-haiku-20240307"
    coordinator_model: str = "claude-3-haiku-20240307"

    # WebSocket
    ws_heartbeat_interval: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
