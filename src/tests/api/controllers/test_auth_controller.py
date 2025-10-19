from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pytest
from src.api.schemas.auth_schema import LoginRequest, LoginResponse
from src.api.controllers.auth_controller import AuthController 
from src.api.services.auth_service import AuthService 

class MockAuthService:
    def login(self, db: Session, request: LoginRequest) -> LoginResponse:
        if request.email == "test@example.com" and request.password == "goodpassword":
            return LoginResponse(access_token="fake-jwt-token", token_type="bearer")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

def override_get_db():
    yield None
    import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.api.database import Base, get_db
from src.api.controllers.auth_controller import AuthController
from src.api.services.auth_service import AuthService
from src.api.schemas.auth_schema import LoginRequest, LoginResponse, UserResponse
from src.utils.hashing import get_password_hash
from src.models.user import User
from src.models.role import Role
from src.models.user_role import UserRole
from uuid import uuid4

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
auth_service = AuthService()
auth_controller = AuthController(auth_service)
app.include_router(auth_controller.router)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    user_id = uuid4()
    test_user = User(
        id=user_id,
        email="test@example.com",
        hashed_password=get_password_hash("test_password"),
        full_name="Test User"
    )

    test_role = Role(
        id=uuid4(),
        name="student"
    )

    db.add(test_user)
    db.add(test_role)
    db.commit()

    user_role = UserRole(
        user_id=test_user.id,
        role_id=test_role.id
    )
    db.add(user_role)
    db.commit()
    
    yield db

    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def get_test_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = get_test_db
    return TestClient(app)

def test_login_success(client):
    """Test successful login with correct credentials"""
    login_data = {
        "email": "test@example.com",
        "password": "test_password"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["full_name"] == "Test User"
    assert "student" in data["user"]["roles"]

def test_login_invalid_email(client):
    """Test login with non-existent email"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "test_password"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]

def test_login_invalid_password(client):
    """Test login with incorrect password"""
    login_data = {
        "email": "test@example.com",
        "password": "wrong_password"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Invalid password" in response.json()["detail"]

def test_login_invalid_email_format(client):
    """Test login with invalid email format"""
    login_data = {
        "email": "invalid-email",
        "password": "test_password"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 422


def test_login_missing_fields(client):
    """Test login with missing required fields"""
    response = client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422

    response = client.post("/auth/login", json={"password": "test_password"})
    assert response.status_code == 422

    response = client.post("/auth/login", json={})
    assert response.status_code == 422
