"""
API data models using Pydantic for validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserModel(BaseModel):
    """User data model."""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "user123",
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True
            }
        }


class APIKeyModel(BaseModel):
    """API key data model."""
    key: str = Field(..., pattern=r"^sk-[a-zA-Z0-9]{16,}", description="API key string")
    name: str = Field(..., min_length=1, max_length=100, description="Key name/description")
    created_at: datetime = Field(..., description="Key creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Key expiration timestamp")
    is_active: bool = Field(default=True, description="Whether the key is active")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "key": "sk-1234567890abcdef",
                "name": "Production API Key",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2025-01-01T00:00:00Z",
                "is_active": True
            }
        }


class ModelConfigurationModel(BaseModel):
    """Model configuration data model."""
    model_id: str = Field(..., description="ID of the AI model to use")
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0-1)"
    )
    max_tokens: int = Field(
        default=100,
        gt=0,
        le=4096,
        description="Maximum number of tokens to generate"
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )
    presence_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty parameter"
    )
    frequency_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty parameter"
    )

    @validator("temperature", "top_p")
    def validate_probability(cls, v: float, field: str) -> float:
        """Validate probability values are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"{field} must be between 0 and 1")
        return v

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "model_id": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 100,
                "top_p": 1.0,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0
            }
        } 
