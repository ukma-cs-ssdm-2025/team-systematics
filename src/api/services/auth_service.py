from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.api.repositories.user_repository import UserRepository
from src.core.security import create_access_token
from src.api.schemas.auth_schema import LoginRequest, LoginResponse, UserResponse
from src.utils.hashing import verify_password, get_password_hash


class AuthService:
    def __init__(self):
        self.user_repo = None

    def login(self, db: Session, request: LoginRequest) -> LoginResponse:
        self.user_repo = UserRepository(db)

        user = self.user_repo.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        print(f"getPasswordHash: {get_password_hash(request.password)}")

        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")

        roles = self.user_repo.get_user_roles(user.id)
        token = create_access_token({"sub": str(user.id), "roles": roles})

        return LoginResponse(
            access_token=token,  # Changed from token= to access_token=
            token_type="bearer",  # Added explicit token_type
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=f"{user.first_name} {user.last_name}".strip(),
                roles=roles
            )
        )
