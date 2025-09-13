"""
Core configuration and settings for the AI Homework Reviewer.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    app_name: str = "AI Homework Reviewer"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # OpenAI Settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # File Paths
    homework_dir: Path = Field(default=Path("homework"), env="HOMEWORK_DIR")
    results_dir: Path = Field(default=Path("results"), env="RESULTS_DIR")
    
    # Review Settings
    max_concurrent_reviews: int = Field(default=5, env="MAX_CONCURRENT_REVIEWS")
    review_timeout: int = Field(default=300, env="REVIEW_TIMEOUT")  # 5 minutes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
