"""
Configuration module for AMEGA-AI

This module handles configuration loading from environment variables and provides
type-safe configuration objects.
"""
from typing import List, Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    # App settings
    APP_NAME: str = "AMEGA-AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database settings
    DATABASE_URL: Optional[PostgresDsn] = None
    
    # Redis settings
    REDIS_URL: Optional[RedisDsn] = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # Model settings
    MODEL_NAME: str = "microsoft/DialoGPT-medium"
    
    # JWT settings
    SECRET_KEY: str = Field(default="your-secret-key-please-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate limiting settings
    RATE_LIMIT_DEFAULT_RPM: int = Field(default=100, description="Default requests per minute")
    RATE_LIMIT_AUTH_RPM: int = Field(default=1000, description="Authenticated requests per minute")
    RATE_LIMIT_CHAT_RPM: int = Field(default=50, description="Chat requests per minute")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_prefix="AMEGA_"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates the database URL, returning it if it is a string or None otherwise.
        
        This method ensures that the database URL is either a valid string or None, allowing for optional configuration.
        """
        if isinstance(v, str):
        return v
        return None

# Global settings instance
settings = Settings()