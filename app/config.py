"""Configuration management for the quiz solver application."""
import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    aipipe_token: str
    email: str
    quiz_secret: str
    github_repo: str
    
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
    fallback_models: str = "google/gemini-2.0-flash-exp,openai/gpt-4-turbo"
    
    # Processing Configuration
    max_file_size_mb: int = 50
    max_retries: int = 3
    enable_verification: bool = True
    
    # AIPipe Configuration
    aipipe_base_url: str = "https://aipipe.org/openrouter/v1"
    aipipe_openai_url: str = "https://aipipe.org/openai/v1"
    
    # Working Directory
    work_dir: str = "/tmp/quiz_solver"
    
    @field_validator('fallback_models', mode='after')
    @classmethod
    def parse_fallback_models(cls, v) -> List[str]:
        """Convert comma-separated string to list."""
        if isinstance(v, str):
            return [model.strip() for model in v.split(",") if model.strip()]
        return v
    
    @field_validator('enable_verification', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Parse boolean from string."""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
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