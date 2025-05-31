"""
Tests for authentication functionality.
"""
import pytest
from backend.auth import fake_users_db

def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"

def test_register_duplicate_user(client):
    """Test registering a duplicate user."""
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate@example.com"
        }
    )
    
    # Attempt duplicate registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate@example.com"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login(client):
    """Test user login."""
    # Register a user first
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "logintest",
            "email": "login@example.com"
        }
    )
    
    # Attempt login
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "logintest",
            "password": "default-password"  # Using the default password from registration
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_protected_endpoint(client):
    """Test accessing a protected endpoint."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "protected",
            "email": "protected@example.com"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "protected",
            "password": "default-password"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Test accessing protected endpoint
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "protected"

def test_protected_endpoint_no_token(client):
    """Test accessing a protected endpoint without a token."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_chat_endpoint_authentication(client):
    """Test chat endpoint with authentication."""
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "chatuser",
            "email": "chat@example.com"
        }
    )
    
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "chatuser",
            "password": "default-password"
        }
    )
    
    token = login_response.json()["access_token"]
    
    # Test chat endpoint with authentication
    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role": "user",
            "content": "Hello, AI!"
        }
    )
    assert response.status_code == 200
    assert "content" in response.json()

def test_chat_endpoint_no_auth(client):
    """Test chat endpoint without authentication."""
    response = client.post(
        "/api/v1/chat",
        json={
            "role": "user",
            "content": "Hello, AI!"
        }
    )
    assert response.status_code == 401

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up the fake database after each test."""
    yield
    fake_users_db.clear() 