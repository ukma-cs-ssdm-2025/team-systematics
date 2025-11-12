from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from src.models.users import User
from src.api.database import get_db
from src.utils.auth import get_current_user_id

def get_current_user(db: Session = Depends(get_db), user_id: UUID = Depends(get_current_user_id)) -> User:
    """
    Залежність FastAPI, яка отримує ID користувача з токена,
    завантажує об'єкт користувача та повертає його.
    """
    user = db.query(User).options(
        joinedload(User.major)
    ).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
