"""Tests for security middleware and RBAC functionality."""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from datetime import timedelta
from backend.security import (
    SecurityMiddleware, RBACMiddleware, RequestValidationMiddleware,
    requires_admin, requires_moderator, requires_user
)
from backend.auth import (
    User, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, fake_users_db, get_password_hash
)

# Test app setup
app = FastAPI()
app.add_middleware(SecurityMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(RequestValidationMiddleware)

@pytest.fixture(autouse=True)
def setup_test_users():
    """Setup test users before each test."""
    # Create test users
    test_users = {
        "test_admin": {
            "username": "test_admin",
            "email": "test_admin@example.com",
            "full_name": "Test Admin",
            "disabled": False,
            "role": "admin",
            "hashed_password": get_password_hash("test_admin")
        },
        "test_moderator": {
            "username": "test_moderator",
            "email": "test_moderator@example.com",
            "full_name": "Test Moderator",
            "disabled": False,
            "role": "moderator",
            "hashed_password": get_password_hash("test_moderator")
        },
        "test_user": {
            "username": "test_user",
            "email": "test_user@example.com",
            "full_name": "Test User",
            "disabled": False,
            "role": "user",
            "hashed_password": get_password_hash("test_user")
        }
    }
    
    # Clear existing test users
    for username in ["test_admin", "test_moderator", "test_user"]:
        fake_users_db.pop(username, None)
    
    # Add test users to fake database
    fake_users_db.update(test_users)
    
    yield
    
    # Cleanup after test
    for username in ["test_admin", "test_moderator", "test_user"]:
        fake_users_db.pop(username, None)

# Mock endpoints for testing
@app.get("/test/public")
async def public_endpoint():
    return {"message": "public"}

@app.get("/test/user")
async def user_endpoint(user: User = Depends(requires_user)):
    return {"message": "user", "role": user.role}

@app.get("/test/moderator")
async def moderator_endpoint(user: User = Depends(requires_moderator)):
    return {"message": "moderator", "role": user.role}

@app.get("/test/admin")
async def admin_endpoint(user: User = Depends(requires_admin)):
    return {"message": "admin", "role": user.role}

@app.post("/test/content")
async def content_endpoint():
    return {"message": "content"}

# Test client
client = TestClient(app)

def create_test_token(username: str) -> str:
    """Create a test JWT token."""
    user = fake_users_db[username]
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": username, "role": user["role"]},
        expires_delta=expires
    )
    return token

def test_security_headers():
    """Test security headers are added to responses."""
    response = client.get("/test/public")
    assert response.status_code == 200
    
    # Check security headers
    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert "Content-Security-Policy" in headers
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_rbac_public_endpoint():
    """Test public endpoint access."""
    response = client.get("/test/public")
    assert response.status_code == 200
    assert response.json() == {"message": "public"}

def test_rbac_protected_endpoints_unauthorized():
    """Test protected endpoints without authentication."""
    endpoints = ["/test/user", "/test/moderator", "/test/admin"]
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            assert response.status_code == 401
            assert response.json()["detail"] == "Not authenticated"
        except Exception as e:
            assert "401: Not authenticated" in str(e)

def test_rbac_user_access():
    """Test user role access."""
    # Create user token
    token = create_test_token("test_user")
    headers = {"Authorization": f"Bearer {token}"}
    
    # User can access user endpoint
    response = client.get("/test/user", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "user", "role": "user"}
    
    # User cannot access moderator endpoint
    response = client.get("/test/moderator", headers=headers)
    assert response.status_code == 403
    
    # User cannot access admin endpoint
    response = client.get("/test/admin", headers=headers)
    assert response.status_code == 403

def test_rbac_moderator_access():
    """Test moderator role access."""
    # Create moderator token
    token = create_test_token("test_moderator")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Moderator can access user endpoint
    response = client.get("/test/user", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "user", "role": "moderator"}
    
    # Moderator can access moderator endpoint
    response = client.get("/test/moderator", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "moderator", "role": "moderator"}
    
    # Moderator cannot access admin endpoint
    response = client.get("/test/admin", headers=headers)
    assert response.status_code == 403

def test_rbac_admin_access():
    """Test admin role access."""
    # Create admin token
    token = create_test_token("test_admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Admin can access all endpoints
    endpoints = [
        ("/test/user", "user"),
        ("/test/moderator", "moderator"),
        ("/test/admin", "admin")
    ]
    for endpoint, message in endpoints:
        response = client.get(endpoint, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": message, "role": "admin"}

def test_request_validation():
    """Test request validation middleware."""
    # Get admin token for authentication
    token = create_test_token("test_admin")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test content length limit
    large_content = "x" * (10 * 1024 * 1024 + 1)  # Exceeds 10MB
    try:
        response = client.post(
            "/test/content",
            json={"content": large_content},
            headers=headers
        )
        assert response.status_code == 413
        assert response.json()["detail"] == "Request too large"
    except Exception as e:
        assert "413: Request too large" in str(e)
    
    # Test content type validation
    try:
        response = client.post(
            "/test/content",
            headers={"Content-Type": "text/plain", **headers},
            content="invalid"
        )
        assert response.status_code == 415
        assert response.json()["detail"] == "Unsupported media type"
    except Exception as e:
        assert "415: Unsupported media type" in str(e)
    
    # Test valid request
    response = client.post(
        "/test/content",
        json={"content": "valid"},
        headers=headers
    )
    assert response.status_code == 200 