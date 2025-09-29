"""
Core configuration and settings for the AI Homework Reviewer.
"""
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

    # Google Gemini Settings
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL") # Updated default

    # GitHub Configuration
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")

    # Google Cloud & SendGrid Configuration
    gcp_project_id: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    gcs_bucket_name: Optional[str] = Field(default=None, env="GCS_BUCKET_NAME")
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    sender_email: Optional[str] = Field(default=None, env="SENDER_EMAIL")
    recipient_email: Optional[str] = Field(default=None, env="RECIPIENT_EMAIL")

    # Review Settings
    max_concurrent_reviews: int = Field(default=5, env="MAX_CONCURRENT_REVIEWS")
    review_timeout: int = Field(default=300, env="REVIEW_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings