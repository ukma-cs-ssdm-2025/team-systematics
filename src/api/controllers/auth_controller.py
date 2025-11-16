from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from src.api.services.auth_service import AuthService
from src.api.database import get_db
from src.api.controllers.versioning import require_api_version

class AuthController:
    def __init__(self, service: AuthService) -> None:
        self.service = service
        self.router = APIRouter(
            prefix="/auth",
            tags=["Auth"],
            dependencies=[Depends(require_api_version)]
        )

        @self.router.post(
            "/login",
            response_model=LoginResponse,
            status_code=status.HTTP_200_OK,
            summary="User login"
        )
        async def login(request: LoginRequest, db: Session = Depends(get_db)):
            return self.service.login(db, request)

        @self.router.post(
            "/register",
            response_model=LoginResponse,
            status_code=status.HTTP_201_CREATED,
            summary="User registration"
        )
        async def register(request: RegisterRequest, db: Session = Depends(get_db)):
            """Реєстрація нового користувача. За замовчуванням призначається роль 'student'."""
            return self.service.register(db, request)
