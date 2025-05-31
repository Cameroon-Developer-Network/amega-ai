"""Tests for the configuration module."""
import os
import pytest
from backend.config import Settings, LLMConfig, BackendConfig

def test_default_settings():
    """Test default settings are loaded correctly."""
    settings = Settings()
    
    # Test app settings
    assert settings.APP_NAME == "AMEGA-AI"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEBUG is False
    
    # Test LLM settings
    assert settings.ACTIVE_LLM_BACKEND == "huggingface"
    assert settings.LLM_CONFIG.temperature == 0.7
    assert settings.LLM_CONFIG.max_length == 1000

def test_llm_config_validation():
    """Test LLM configuration validation."""
    # Test valid values
    config = LLMConfig(
        temperature=0.8,
        max_length=500,
        top_p=0.95,
        repetition_penalty=1.5,
        top_k=40,
        presence_penalty=1.0,
        frequency_penalty=-1.0
    )
    assert config.temperature == 0.8
    assert config.max_length == 500
    
    # Test invalid values
    with pytest.raises(ValueError):
        LLMConfig(temperature=1.5)  # Above max
    
    with pytest.raises(ValueError):
        LLMConfig(temperature=-0.1)  # Below min
    
    with pytest.raises(ValueError):
        LLMConfig(presence_penalty=2.5)  # Above max

def test_backend_config():
    """Test backend configuration."""
    config = BackendConfig(
        api_key="test-key",
        api_base="https://api.example.com",
        organization_id="org-123",
        model_name="test-model",
        timeout=45
    )
    
    assert config.api_key == "test-key"
    assert config.model_name == "test-model"
    assert config.timeout == 45

def test_active_backend_config():
    """Test getting active backend configuration."""
    settings = Settings()
    
    # Test default (HuggingFace)
    active_config = settings.get_active_backend_config()
    assert active_config.model_name == "microsoft/DialoGPT-medium"
    
    # Test switching backend
    settings.ACTIVE_LLM_BACKEND = "openai"
    active_config = settings.get_active_backend_config()
    assert active_config.model_name == "gpt-3.5-turbo"

def test_environment_variables():
    """Test loading settings from environment variables."""
    # Set test environment variables
    os.environ["AMEGA_APP_NAME"] = "Test App"
    os.environ["AMEGA_ACTIVE_LLM_BACKEND"] = "openai"
    os.environ["AMEGA_OPENAI_CONFIG__MODEL_NAME"] = "gpt-4"
    os.environ["AMEGA_OPENAI_CONFIG__API_KEY"] = "test-openai-key"
    os.environ["AMEGA_LLM_CONFIG__TEMPERATURE"] = "0.9"
    
    settings = Settings()
    
    assert settings.APP_NAME == "Test App"
    assert settings.ACTIVE_LLM_BACKEND == "openai"
    assert settings.OPENAI_CONFIG.model_name == "gpt-4"
    assert settings.OPENAI_CONFIG.api_key == "test-openai-key"
    assert settings.LLM_CONFIG.temperature == 0.9
    
    # Clean up environment variables
    del os.environ["AMEGA_APP_NAME"]
    del os.environ["AMEGA_ACTIVE_LLM_BACKEND"]
    del os.environ["AMEGA_OPENAI_CONFIG__MODEL_NAME"]
    del os.environ["AMEGA_OPENAI_CONFIG__API_KEY"]
    del os.environ["AMEGA_LLM_CONFIG__TEMPERATURE"]

def test_yaml_config(tmp_path):
    """Test loading configuration from YAML file."""
    # Create a test YAML file
    yaml_content = """
app:
  name: YAML Test App
  version: 1.0.0
  debug: true

llm:
  active_backend: anthropic
  backends:
    anthropic:
      model_name: claude-test
      api_key: test-key
  generation:
    temperature: 0.5
    max_length: 2000
    """
    
    yaml_file = tmp_path / "test_config.yml"
    yaml_file.write_text(yaml_content)
    
    settings = Settings.from_yaml(yaml_file)
    
    assert settings.APP_NAME == "YAML Test App"
    assert settings.ACTIVE_LLM_BACKEND == "anthropic"
    assert settings.ANTHROPIC_CONFIG.model_name == "claude-test"
    assert settings.LLM_CONFIG.temperature == 0.5

def test_settings_env_override():
    """Test environment variables override default settings."""
    os.environ["AMEGA_APP_NAME"] = "Override Test"
    os.environ["AMEGA_DEBUG"] = "true"
    
    settings = Settings()
    assert settings.APP_NAME == "Override Test"
    assert settings.DEBUG is True
    
    del os.environ["AMEGA_APP_NAME"]
    del os.environ["AMEGA_DEBUG"]

def test_database_url_validation():
    """Test database URL validation."""
    valid_url = "postgresql://user:pass@localhost:5432/db"
    settings = Settings(DATABASE_URL=valid_url)
    assert str(settings.DATABASE_URL) == valid_url

def test_allowed_origins():
    """Test ALLOWED_ORIGINS configuration."""
    custom_origins = ["https://example.com", "http://localhost:8080"]
    settings = Settings(ALLOWED_ORIGINS=custom_origins)
    assert settings.ALLOWED_ORIGINS == custom_origins