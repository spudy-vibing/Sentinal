"""
SENTINEL V2 — Configuration
Environment variables and settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import model_validator
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
    default_model: str = "claude-3-5-haiku-20241022"
    coordinator_model: str = "claude-3-5-haiku-20241022"
    agent_model: str = "claude-3-5-haiku-20241022"
    use_real_agents: bool = True

    # WebSocket
    ws_heartbeat_interval: int = 30

    @model_validator(mode='after')
    def derive_real_agents(self):
        """Auto-disable real agents when no API key is provided."""
        if not self.anthropic_api_key:
            self.use_real_agents = False
        return self

    class Config:
        # Look for .env in both backend/ and parent sentinel-web/ directories
        env_file = [".env", "../.env"]
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra env vars not defined in Settings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
