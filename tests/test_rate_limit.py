"""
Tests for rate limiting functionality.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.rate_limit import RateLimiter, RateLimitConfig, rate_limit_dependency

@pytest.fixture
def redis_mock():
    """Mock Redis client."""
    with patch("redis.from_url") as mock:
        yield mock.return_value

@pytest.fixture
def rate_limiter(redis_mock):
    """Create a RateLimiter instance with mocked Redis."""
    return RateLimiter(
        redis_url="redis://fake",
        default_limits={
            "test": RateLimitConfig(requests=2, window_seconds=60)
        }
    )

@pytest.fixture
def test_app(rate_limiter):
    """Create a test FastAPI app with rate limiting."""
    app = FastAPI()
    app.state.rate_limiter = rate_limiter
    
    @app.get("/test")
    async def test_endpoint(rate_limit: dict = Depends(rate_limit_dependency("test"))):
        return {"message": "success"}
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)

def test_rate_limit_config():
    """Test rate limit configuration."""
    config = RateLimitConfig(requests=100, window_seconds=60)
    assert config.requests == 100
    assert config.window_seconds == 60
    assert config.tier == "default"

def test_rate_limiter_init():
    """Test rate limiter initialization."""
    limiter = RateLimiter()
    assert "default" in limiter.default_limits
    assert "authenticated" in limiter.default_limits
    assert "chat" in limiter.default_limits

def test_window_key_generation(rate_limiter):
    """Test window key generation."""
    key = rate_limiter._get_window_key("test_id", 1000)
    assert key == "rate_limit:test_id:1000"

def test_successful_request(test_client, redis_mock):
    """Test successful request within rate limit."""
    redis_mock.incr.return_value = 1
    response = test_client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_exceeded(test_client, redis_mock):
    """Test request when rate limit is exceeded."""
    redis_mock.incr.return_value = 3  # Over the limit of 2
    response = test_client.get("/test")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_headers(test_client, redis_mock):
    """Test rate limit headers are set correctly."""
    redis_mock.incr.return_value = 1
    response = test_client.get("/test")
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"
    assert "X-RateLimit-Reset" in response.headers

@pytest.mark.asyncio
async def test_rate_limit_tiers(rate_limiter, redis_mock):
    """Test different rate limit tiers."""
    redis_mock.incr.return_value = 1
    
    # Test default tier
    is_limited, info = await rate_limiter.is_rate_limited("test_id", "default")
    assert not is_limited
    assert info["tier"] == "default"
    
    # Test authenticated tier
    is_limited, info = await rate_limiter.is_rate_limited("test_id", "authenticated")
    assert not is_limited
    assert info["tier"] == "authenticated"
    
    # Test chat tier
    is_limited, info = await rate_limiter.is_rate_limited("test_id", "chat")
    assert not is_limited
    assert info["tier"] == "chat"

def test_invalid_tier_fallback(rate_limiter, redis_mock):
    """Test fallback to default tier for invalid tier names."""
    redis_mock.incr.return_value = 1
    is_limited, info = await rate_limiter.is_rate_limited("test_id", "invalid_tier")
    assert not is_limited
    assert info["tier"] == "default" 