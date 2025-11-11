from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.models.users import User
from src.api.database import get_db

def get_current_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
