"""
AMEGA-AI FastAPI Application

This module sets up the main FastAPI application instance with configuration
loading from environment variables, CORS middleware, and basic health check endpoint.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn
from typing import List
import logging
from datetime import datetime, timedelta

from .llm_manager import LLMManager, ChatMessage
from .auth import (
    User, Token, authenticate_user, create_access_token,
    get_current_active_user, get_password_hash, fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .rate_limit import RateLimiter, rate_limit_dependency, RateLimitConfig
from .security import (
    SecurityMiddleware, RBACMiddleware, RequestValidationMiddleware,
    requires_admin, requires_user
)
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI application."""
    # Startup
    app.state.llm_manager = LLMManager(model_name=settings.MODEL_NAME)

    # Initialize rate limiter
    app.state.rate_limiter = RateLimiter(
        redis_url=str(settings.REDIS_URL),
        default_limits={
            "default": RateLimitConfig(
                requests=settings.RATE_LIMIT_DEFAULT_RPM,
                window_seconds=60
            ),
            "authenticated": RateLimitConfig(
                requests=settings.RATE_LIMIT_AUTH_RPM,
                window_seconds=60
            ),
            "chat": RateLimitConfig(
                requests=settings.RATE_LIMIT_CHAT_RPM,
                window_seconds=60
            ),
        }
    )
    yield
    # Shutdown
    # Add cleanup code here if needed

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A powerful AI-driven platform for intelligent automation and decision making.",
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(RequestValidationMiddleware)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to all responses."""
    response = await call_next(request)
    if hasattr(request.state, "rate_limit_headers"):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = value
    return response

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=User)
async def register_user(
    user: User,
    rate_limit: dict = Depends(rate_limit_dependency())
):
    """Register a new user."""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create a new user with hashed password
    hashed_password = get_password_hash("default-password")  # In production, get password from request
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    user_dict["role"] = "user"  # Default role for new users
    fake_users_db[user.username] = user_dict

    return user

@app.post("/api/v1/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    rate_limit: dict = Depends(rate_limit_dependency())
):
    """Login endpoint to get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoints
@app.get("/api/v1/users/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    rate_limit: dict = Depends(rate_limit_dependency("authenticated"))
):
    """Get current user information."""
    return current_user

@app.get("/api/v1/users", response_model=List[User])
async def list_users(
    current_user: User = Depends(requires_admin),
    rate_limit: dict = Depends(rate_limit_dependency("authenticated"))
):
    """List all users (admin only)."""
    return list(fake_users_db.values())

@app.post("/api/v1/chat", response_model=ChatMessage)
async def chat(
    message: ChatMessage,
    current_user: User = Depends(requires_user),
    rate_limit: dict = Depends(rate_limit_dependency("chat"))
):
    """Chat with the AI model."""
    response = await app.state.llm_manager.generate_response(message.content)
    return ChatMessage(
        content=response,
        timestamp=datetime.utcnow(),
        user_id=current_user.username
    )

# Health check endpoint (public)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": settings.APP_VERSION
    }

@app.get("/")
async def root(rate_limit: dict = Depends(rate_limit_dependency())):
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Welcome to AMEGA-AI API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
