from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.utils.hashing import verify_password
from app.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # password check (plain vs hashed — adjust later if needed)
    if user.hashed_password != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    roles = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    roles = [r[0] for r in roles]

    token = create_access_token({"sub": str(user.id), "roles": roles})

    return LoginResponse(
        token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles
        )
    )
