from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pytest
from src.api.schemas import LoginRequest, LoginResponse
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

mock_auth_service = MockAuthService()

auth_controller = AuthController(service=mock_auth_service)

app = FastAPI()
app.include_router(auth_controller.router)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
