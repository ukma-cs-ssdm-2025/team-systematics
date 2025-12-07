"""
Tests for authentication functionality with mocks.
"""
import pytest
from uuid import uuid4


class MockAuthService:
    """Mock authentication service for testing."""
    
    def login(self, email, password):
        """Mock login."""
        if email == "valid@test.com" and password == "correct_password":
            return {"access_token": "fake-jwt-token", "user_id": uuid4()}
        raise ValueError("Invalid credentials")
    
    def verify_token(self, token):
        """Mock token verification."""
        if token == "fake-jwt-token":
            return uuid4()
        raise ValueError("Invalid token")
    
    def register(self, email, password, full_name):
        """Mock user registration."""
        return {
            "id": uuid4(),
            "email": email,
            "full_name": full_name
        }


@pytest.fixture
def auth_service():
    """Create mock auth service."""
    return MockAuthService()


def test_login_success(auth_service):
    """Test successful login."""
    result = auth_service.login("valid@test.com", "correct_password")
    
    assert result["access_token"] == "fake-jwt-token"
    assert result["user_id"] is not None


def test_login_invalid_credentials(auth_service):
    """Test login with invalid credentials."""
    with pytest.raises(ValueError) as exc_info:
        auth_service.login("valid@test.com", "wrong_password")
    
    assert "Invalid credentials" in str(exc_info.value)


def test_login_invalid_email(auth_service):
    """Test login with invalid email."""
    with pytest.raises(ValueError):
        auth_service.login("invalid@test.com", "correct_password")


def test_login_missing_email(auth_service):
    """Test login with missing email."""
    with pytest.raises((TypeError, ValueError)):
        auth_service.login(None, "correct_password")


def test_login_missing_password(auth_service):
    """Test login with missing password."""
    with pytest.raises((TypeError, ValueError)):
        auth_service.login("valid@test.com", None)


def test_verify_valid_token(auth_service):
    """Test token verification with valid token."""
    user_id = auth_service.verify_token("fake-jwt-token")
    
    assert user_id is not None


def test_verify_invalid_token(auth_service):
    """Test token verification with invalid token."""
    with pytest.raises(ValueError):
        auth_service.verify_token("invalid-token")


def test_register_new_user(auth_service):
    """Test user registration."""
    result = auth_service.register("new@test.com", "password123", "New User")
    
    assert result["email"] == "new@test.com"
    assert result["full_name"] == "New User"
    assert result["id"] is not None
