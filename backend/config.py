"""
Configuration module for AMEGA-AI

This module handles configuration loading from environment variables and provides
type-safe configuration objects.
"""
from typing import List, Optional, Literal, Dict, Any
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, field_validator, RedisDsn, BaseModel, model_validator

class LLMConfig(BaseModel):
    """Configuration for LLM generation parameters."""
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Controls randomness in generation. Higher values make output more random."
    )
    max_length: int = Field(
        default=1000,
        gt=0,
        description="Maximum length of generated text in tokens."
    )
    top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter. Controls diversity of generated text."
    )
    repetition_penalty: float = Field(
        default=1.2,
        ge=0.0,
        description="Penalty for repeating tokens. Higher values discourage repetition."
    )
    top_k: int = Field(
        default=50,
        ge=0,
        description="Number of highest probability tokens to consider for generation."
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on their presence in the text so far."
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on their frequency in the text so far."
    )

class BackendConfig(BaseModel):
    """Configuration for different LLM backends."""
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the LLM service"
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Base URL for API requests"
    )
    organization_id: Optional[str] = Field(
        default=None,
        description="Organization ID for the LLM service"
    )
    model_name: str = Field(
        description="Name of the model to use"
    )
    timeout: int = Field(
        default=30,
        gt=0,
        description="Timeout for API requests in seconds"
    )

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
    REDIS_URL: Optional[RedisDsn] = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    # LLM Backend Selection
    ACTIVE_LLM_BACKEND: Literal["huggingface", "openai", "anthropic", "ollama"] = Field(
        default="huggingface",
        description="The active LLM backend to use"
    )

    # LLM Backend Configurations
    HUGGINGFACE_CONFIG: BackendConfig = Field(
        default_factory=lambda: BackendConfig(
            model_name="microsoft/DialoGPT-medium"
        ),
        description="HuggingFace models configuration"
    )

    OPENAI_CONFIG: BackendConfig = Field(
        default_factory=lambda: BackendConfig(
            model_name="gpt-3.5-turbo"
        ),
        description="OpenAI models configuration"
    )

    ANTHROPIC_CONFIG: BackendConfig = Field(
        default_factory=lambda: BackendConfig(
            model_name="claude-3-opus-20240229"
        ),
        description="Anthropic models configuration"
    )

    OLLAMA_CONFIG: BackendConfig = Field(
        default_factory=lambda: BackendConfig(
            model_name="llama2",
            api_base="http://localhost:11434"
        ),
        description="Ollama models configuration"
    )

    # LLM Generation Parameters
    LLM_CONFIG: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM generation parameters"
    )

    # JWT settings
    SECRET_KEY: str = Field(
        default="your-secret-key-please-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate limiting settings
    RATE_LIMIT_DEFAULT_RPM: int = Field(
        default=100,
        description="Default requests per minute"
    )
    RATE_LIMIT_AUTH_RPM: int = Field(
        default=1000,
        description="Authenticated requests per minute"
    )
    RATE_LIMIT_CHAT_RPM: int = Field(
        default=50,
        description="Chat requests per minute"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_prefix="AMEGA_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        validate_default=True
    )

    @model_validator(mode='before')
    @classmethod
    def validate_configs(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and transform configurations from environment variables."""
        # Handle OpenAI config
        if values.get("ACTIVE_LLM_BACKEND") == "openai":
            openai_config = values.get("OPENAI_CONFIG", {})
            if isinstance(openai_config, dict):
                if "MODEL_NAME" in openai_config:
                    openai_config["model_name"] = openai_config.pop("MODEL_NAME")
                if "API_KEY" in openai_config:
                    openai_config["api_key"] = openai_config.pop("API_KEY")
                values["OPENAI_CONFIG"] = openai_config

        # Handle LLM config
        llm_config = values.get("LLM_CONFIG", {})
        if isinstance(llm_config, dict):
            if "TEMPERATURE" in llm_config:
                llm_config["temperature"] = float(llm_config.pop("TEMPERATURE"))
            values["LLM_CONFIG"] = llm_config

        return values

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validates the database URL, returning it if it is a string or None otherwise.

        This method ensures that the database URL is either a valid string or None,
        allowing for optional configuration.
        """
        if isinstance(v, str):
            return v
        return None

    def get_active_backend_config(self) -> BackendConfig:
        """Returns the configuration for the active LLM backend."""
        backend_configs = {
            "huggingface": self.HUGGINGFACE_CONFIG,
            "openai": self.OPENAI_CONFIG,
            "anthropic": self.ANTHROPIC_CONFIG,
            "ollama": self.OLLAMA_CONFIG
        }
        return backend_configs[self.ACTIVE_LLM_BACKEND]

    @classmethod
    def from_yaml(cls, yaml_file: str | Path) -> "Settings":
        """Load settings from a YAML file."""
        yaml_file = Path(yaml_file)
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML configuration file not found: {yaml_file}")

        with yaml_file.open("r") as f:
            yaml_data = yaml.safe_load(f)

        # Transform YAML structure to match our settings format
        config_data = {}

        # Handle app settings
        if "app" in yaml_data:
            config_data.update({
                "APP_NAME": yaml_data["app"].get("name", cls.model_fields["APP_NAME"].default),
                "APP_VERSION": yaml_data["app"].get("version", cls.model_fields["APP_VERSION"].default),
                "DEBUG": yaml_data["app"].get("debug", cls.model_fields["DEBUG"].default)
            })

        # Handle LLM settings
        if "llm" in yaml_data:
            llm_data = yaml_data["llm"]
            if "active_backend" in llm_data:
                config_data["ACTIVE_LLM_BACKEND"] = llm_data["active_backend"]

            if "backends" in llm_data:
                backends = llm_data["backends"]
                if "huggingface" in backends:
                    config_data["HUGGINGFACE_CONFIG"] = backends["huggingface"]
                if "openai" in backends:
                    config_data["OPENAI_CONFIG"] = backends["openai"]
                if "anthropic" in backends:
                    config_data["ANTHROPIC_CONFIG"] = backends["anthropic"]
                if "ollama" in backends:
                    config_data["OLLAMA_CONFIG"] = backends["ollama"]

            if "generation" in llm_data:
                config_data["LLM_CONFIG"] = llm_data["generation"]

        # Create settings instance with YAML data
        return cls(**config_data)

# Global settings instance
settings = Settings()