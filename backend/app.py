"""
AMEGA-AI FastAPI Application

This module sets up the main FastAPI application instance with configuration
loading from environment variables, CORS middleware, and basic health check endpoint.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_active_user,
    get_password_hash,
)
from .config import settings
from .llm_manager import ChatMessage, LLMManager
from .rate_limit import RateLimitConfig, RateLimiter, rate_limit_dependency

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            "default": RateLimitConfig(requests=settings.RATE_LIMIT_DEFAULT_RPM, window_seconds=60),
            "authenticated": RateLimitConfig(
                requests=settings.RATE_LIMIT_AUTH_RPM, window_seconds=60
            ),
            "chat": RateLimitConfig(requests=settings.RATE_LIMIT_CHAT_RPM, window_seconds=60),
        },
    )
    yield
    # Shutdown
    # Add cleanup code here if needed


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A powerful AI-driven platform for intelligent automation and decision making.",
    lifespan=lifespan,
)

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
async def register_user(user: User, rate_limit: dict = Depends(rate_limit_dependency())):
    """Register a new user."""
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
        )

    # Create a new user with hashed password
    hashed_password = get_password_hash(
        "default-password"
    )  # In production, get password from request
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hashed_password
    fake_users_db[user.username] = user_dict

    return user


@app.post("/api/v1/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    rate_limit: dict = Depends(rate_limit_dependency()),
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


@app.get("/api/v1/users/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    rate_limit: dict = Depends(rate_limit_dependency("authenticated")),
):
    """Get current user information."""
    return current_user


# Protected chat endpoints
@app.post("/api/v1/chat", response_model=ChatMessage)
async def chat_completion(
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    rate_limit: dict = Depends(rate_limit_dependency("chat")),
):
    """
    Chat completion endpoint.

    This endpoint processes a chat message and returns an AI-generated response.
    The conversation history is maintained for context-aware responses.
    """
    try:
        logger.info(f"Received chat message from user {current_user.username}: {message.content}")
        response = await app.state.llm_manager.chat(message)
        logger.info(f"Generated response: {response.content}")
        return response
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request.",
        )


@app.get("/api/v1/chat/history", response_model=List[ChatMessage])
async def get_chat_history(
    current_user: User = Depends(get_current_active_user),
    rate_limit: dict = Depends(rate_limit_dependency("authenticated")),
):
    """Retrieve the conversation history."""
    try:
        return app.state.llm_manager.get_conversation_history()
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the chat history.",
        )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(rate_limit: dict = Depends(rate_limit_dependency())):
    """Health check endpoint to verify API status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


@app.get("/")
async def root(rate_limit: dict = Depends(rate_limit_dependency())):
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Welcome to AMEGA-AI API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
