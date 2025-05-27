"""
Tests for configuration module.
"""
from pydantic import PostgresDsn
from backend.config import Settings

def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    assert settings.APP_NAME == "AMEGA-AI"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEBUG is False
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.MODEL_NAME == "microsoft/DialoGPT-medium"
    assert settings.SECRET_KEY == "your-secret-key-please-change-in-production"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

def test_settings_env_override(monkeypatch):
    """Test environment variable overrides."""
    monkeypatch.setenv("AMEGA_APP_NAME", "Test App")
    monkeypatch.setenv("AMEGA_DEBUG", "true")
    monkeypatch.setenv("AMEGA_PORT", "9000")
    
    settings = Settings()
    assert settings.APP_NAME == "Test App"
    assert settings.DEBUG is True
    assert settings.PORT == 9000

def test_database_url_validation():
    """Test database URL validation."""
    valid_url = "postgresql://user:pass@localhost:5432/db"
    settings = Settings(DATABASE_URL=valid_url)
    assert isinstance(settings.DATABASE_URL, PostgresDsn)
    assert str(settings.DATABASE_URL) == valid_url

def test_allowed_origins():
    """Test ALLOWED_ORIGINS setting."""
    settings = Settings()
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) > 0
    assert all(isinstance(origin, str) for origin in settings.ALLOWED_ORIGINS)