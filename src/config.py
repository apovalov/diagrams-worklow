"""Configuration management for the diagrams workflow service."""

import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API key")

    # Application Configuration
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # File Management
    temp_dir: Path = Field(
        default_factory=lambda: Path("/tmp/diagrams-workflow"),
        description="Directory for temporary diagram files",
    )
    max_file_age_minutes: int = Field(
        default=60, description="Maximum age of temporary files in minutes"
    )

    # API Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind the server to")
    port: int = Field(default=8000, description="Port to bind the server to")
    reload: bool = Field(
        default=False, description="Enable auto-reload for development"
    )

    # LLM Configuration
    max_tokens: int = Field(
        default=2048, description="Maximum tokens for LLM responses"
    )
    temperature: float = Field(default=0.3, description="LLM temperature setting")
    mock_mode: bool = Field(
        default=False, description="Use mock responses instead of real LLM calls"
    )

    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
            ],
        )

        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)

    def ensure_temp_dir(self) -> None:
        """Ensure the temporary directory exists."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return not self.debug_mode and not self.reload


# Global settings instance
settings = Settings()
