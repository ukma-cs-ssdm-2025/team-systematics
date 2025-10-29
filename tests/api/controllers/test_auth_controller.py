import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from uuid import uuid4

from src.api.controllers.auth_controller import AuthController
from src.api.database import get_db
from src.api.controllers.versioning import require_api_version
from src.api.schemas.auth import LoginRequest, LoginResponse, UserResponse


@pytest.fixture
def app_with_good_service():
    """
    Build a minimal FastAPI app with AuthController and a mock AuthService
    that succeeds only for the canonical test credentials.
    """
    class GoodAuthService:
        def login(self, db, request: LoginRequest) -> LoginResponse:
            if request.email == "test@example.com" and request.password == "test_password":
                return LoginResponse(
                    access_token="fake-jwt",
                    token_type="bearer",
                    user=UserResponse(
                        id=uuid4(),
                        email="test@example.com",
                        full_name="Test User",
                        roles=["student"],
                    ),
                )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    app = FastAPI()
    controller = AuthController(GoodAuthService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[require_api_version] = lambda: None
    return app


@pytest.fixture
def app_with_failing_service():
    """
    Build a FastAPI app with a mock AuthService that always raises 401.
    Useful to test how the controller forwards service errors.
    """
    class FailingAuthService:
        def login(self, db, request: LoginRequest):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    app = FastAPI()
    controller = AuthController(FailingAuthService())
    app.include_router(controller.router)

    def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[require_api_version] = lambda: None
    return app


@pytest.fixture
def client_good(app_with_good_service) -> TestClient:
    """HTTP client backed by the success-mock service."""
    return TestClient(app_with_good_service)


@pytest.fixture
def client_fail(app_with_failing_service) -> TestClient:
    """HTTP client backed by the failing-mock service."""
    return TestClient(app_with_failing_service)


def test_login_forwards_unauthorized_from_service(client_fail):
    r = client_fail.post("/auth/login", json={"email": "x@y.z", "password": "nope"})
    assert r.status_code == 401
    assert "Invalid" in r.json().get("detail", "")


def test_login_invalid_email_format_returns_422(client_good):
    r = client_good.post("/auth/login", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422


def test_login_missing_fields_returns_422(client_good):
    r1 = client_good.post("/auth/login", json={"email": "test@example.com"})  # missing password
    r2 = client_good.post("/auth/login", json={"password": "test_password"})  # missing email
    r3 = client_good.post("/auth/login", json={})                              # empty body
    assert r1.status_code == 422
    assert r2.status_code == 422
    assert r3.status_code == 422


def test_login_wrong_method_is_405(client_good):
    r = client_good.get("/auth/login")
    assert r.status_code == 405


def test_login_non_json_payload_returns_422(client_good):
    # Sending form data instead of JSON should fail validation
    r = client_good.post("/auth/login", data={"email": "test@example.com", "password": "test_password"})
    assert r.status_code == 422
