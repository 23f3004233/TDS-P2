"""Configuration management for the quiz solver application."""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    aipipe_token: str = os.getenv("AIPIPE_TOKEN", "")
    email: str = os.getenv("EMAIL", "")
    quiz_secret: str = os.getenv("QUIZ_SECRET", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Timeout Configuration (seconds)
    quiz_timeout: int = int(os.getenv("QUIZ_TIMEOUT", "180"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    browser_timeout: int = int(os.getenv("BROWSER_TIMEOUT", "60"))
    
    # AI Model Configuration
    primary_model: str = os.getenv("PRIMARY_MODEL", "openai/gpt-4o")
    verifier_model: str = os.getenv("VERIFIER_MODEL", "anthropic/claude-sonnet-4")
    fallback_models: List[str] = os.getenv(
        "FALLBACK_MODELS", 
        "google/gemini-2.0-flash-exp,openai/gpt-4-turbo"
    ).split(",")
    
    # Processing Configuration
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    enable_verification: bool = os.getenv("ENABLE_VERIFICATION", "true").lower() == "true"
    
    # AIPipe Configuration
    aipipe_base_url: str = "https://aipipe.org/openrouter/v1"
    aipipe_openai_url: str = "https://aipipe.org/openai/v1"
    
    # Working Directory
    work_dir: str = "/tmp/quiz_solver"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure work directory exists
os.makedirs(settings.work_dir, exist_ok=True)