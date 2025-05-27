"""
Security module for AMEGA-AI

This module provides comprehensive security middleware and utilities for protecting
endpoints, implementing RBAC, and enforcing security best practices.
"""

from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from .auth import User, get_current_user, oauth2_scheme
from .config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing security headers and policies."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": self._build_csp(),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    def _build_csp(self) -> str:
        """Build Content Security Policy header value."""
        policies = [
            "default-src 'self'",
            "img-src 'self' data: https:",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        return "; ".join(policies)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value

        return response


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware for Role-Based Access Control."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Define role hierarchy
        self.role_hierarchy = {
            "admin": ["admin", "moderator", "user"],
            "moderator": ["moderator", "user"],
            "user": ["user"],
        }

        # Define endpoint permissions
        self.endpoint_permissions = {
            "/test/admin": "admin",
            "/test/moderator": "moderator",
            "/test/user": "user",
        }

        # Define public endpoints
        self.public_paths = {
            "/test/public",
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check role-based permissions."""
        # Skip RBAC for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get token
        token = auth_header.split(" ")[1]

        # Get user from token
        try:
            user = await get_current_user(token)
            request.state.user = user

            # Check if user has required role for the endpoint
            required_role = self.endpoint_permissions.get(request.url.path)
            if required_role and not self._has_role_access(user.role, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
                )

            return await call_next(request)
        except HTTPException as e:
            raise e

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        return any(path.startswith(p) for p in self.public_paths)

    def _has_role_access(self, user_role: str, required_role: str) -> bool:
        """Check if user role has access to required role."""
        if user_role not in self.role_hierarchy:
            return False
        return required_role in self.role_hierarchy[user_role]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_content_length = 10 * 1024 * 1024  # 10MB

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Validate and sanitize requests."""
        # Skip validation for GET requests
        if request.method == "GET":
            return await call_next(request)

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request too large"
            )

        # Validate content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Unsupported media type",
                )

        return await call_next(request)


def requires_roles(roles: List[str]) -> Callable:
    """Dependency for role-based access control."""

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            "admin": ["admin", "moderator", "user"],
            "moderator": ["moderator", "user"],
            "user": ["user"],
        }

        # Check if user's role has access to any of the required roles
        if user.role not in role_hierarchy:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )

        allowed_roles = role_hierarchy[user.role]
        if not any(role in allowed_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return role_checker


# Convenience dependencies
requires_admin = requires_roles(["admin"])
requires_moderator = requires_roles(["moderator"])
requires_user = requires_roles(["user"])
