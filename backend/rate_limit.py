"""
Rate limiting module for AMEGA-AI

This module implements rate limiting using Redis as a backend for request tracking
and window management.
"""
from datetime import datetime
from typing import Optional, Tuple
import redis
from fastapi import HTTPException, Request, status
from pydantic import BaseModel

class RateLimitConfig(BaseModel):
    """Rate limit configuration."""
    requests: int
    window_seconds: int
    tier: str = "default"

class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_limits: Optional[dict] = None
    ):
        """Initialize rate limiter with Redis connection."""
        self.redis = redis.from_url(redis_url)
        self.default_limits = default_limits or {
            "default": RateLimitConfig(requests=100, window_seconds=60),  # 100 requests per minute
            "authenticated": RateLimitConfig(requests=1000, window_seconds=60),  # 1000 requests per minute
            "chat": RateLimitConfig(requests=50, window_seconds=60),  # 50 chat requests per minute
        }

    def _get_window_key(self, identifier: str, window_start: int) -> str:
        """Generate Redis key for the rate limit window."""
        return f"rate_limit:{identifier}:{window_start}"

    def _get_window_start(self, window_seconds: int) -> int:
        """Get the start timestamp of the current window."""
        now = int(datetime.utcnow().timestamp())
        return now - (now % window_seconds)

    async def is_rate_limited(
        self,
        identifier: str,
        tier: str = "default"
    ) -> Tuple[bool, dict]:
        """
        Check if the request should be rate limited.

        Args:
            identifier: Unique identifier for the client (IP or user ID)
            tier: Rate limit tier to apply

        Returns:
            Tuple of (is_limited, limit_info)
        """
        config = self.default_limits.get(tier)
        if not config:
            config = self.default_limits["default"]

        window_start = self._get_window_start(config.window_seconds)
        key = self._get_window_key(identifier, window_start)

        # Increment request count and set expiry
        current = self.redis.incr(key)
        if current == 1:
            self.redis.expire(key, config.window_seconds)

        is_limited = current > config.requests
        remaining = max(0, config.requests - current)
        reset_time = window_start + config.window_seconds

        limit_info = {
            "limit": config.requests,
            "remaining": remaining,
            "reset": reset_time,
            "tier": tier
        }

        return is_limited, limit_info

def rate_limit_dependency(tier: str = "default"):
    """
    FastAPI dependency for rate limiting.

    Usage:
        @app.get("/endpoint")
        async def endpoint(rate_limit: dict = Depends(rate_limit_dependency())):
            return {"message": "Success"}
    """
    async def check_rate_limit(request: Request) -> dict:
        limiter = request.app.state.rate_limiter

        # Get client identifier (IP address or user ID if authenticated)
        identifier = request.client.host
        if hasattr(request.state, "user"):
            identifier = f"user:{request.state.user.username}"

        is_limited, limit_info = await limiter.is_rate_limited(identifier, tier)

        # Add rate limit headers
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": str(limit_info["reset"])
        }

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=request.state.rate_limit_headers
            )

        return limit_info

    return check_rate_limit
