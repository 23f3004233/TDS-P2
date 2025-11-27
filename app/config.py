"""Configuration management for the quiz solver application."""
import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    aipipe_token: str = ""
    email: str = ""
    quiz_secret: str = ""
    github_repo: str = ""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # Timeout Configuration (seconds)
    quiz_timeout: int = 180
    request_timeout: int = 30
    browser_timeout: int = 60
    
    # AI Model Configuration
    primary_model: str = "openai/gpt-4o"
    verifier_model: str = "anthropic/claude-sonnet-4"
    fallback_models: List[str] = Field(
        default=["google/gemini-2.0-flash-exp", "openai/gpt-4-turbo"]
    )
    
    # Processing Configuration
    max_file_size_mb: int = 50
    max_retries: int = 3
    enable_verification: bool = True
    
    # AIPipe Configuration
    aipipe_base_url: str = "https://aipipe.org/openrouter/v1"
    aipipe_openai_url: str = "https://aipipe.org/openai/v1"
    
    # Working Directory
    work_dir: str = "/tmp/quiz_solver"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

# Ensure work directory exists
os.makedirs(settings.work_dir, exist_ok=True)