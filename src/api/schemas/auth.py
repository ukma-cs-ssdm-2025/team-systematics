from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional
from uuid import UUID

class LoginRequest(BaseModel):
    """Схема для запиту на вхід у систему."""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """Схема для запиту на реєстрацію нового користувача."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    major_id: Optional[int] = None  # Опціональна спеціальність (обов'язкова для студентів, опціональна для інших)

class UserResponse(BaseModel):
    """Схема для відображення публічної інформації про користувача."""
    id: UUID
    email: EmailStr
    # Замість first_name та last_name використаємо одне поле,
    # як у вашій моделі user.py
    full_name: str 
    user_major: Optional[str] = None
    roles: List[str] = [] # Ролі, якщо ви їх реалізуєте
    avatar_url: Optional[HttpUrl] = None

class LoginResponse(BaseModel):
    """Повна відповідь, що надсилається клієнту після успішного входу."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class Token(BaseModel):
    """Стандартна схема для представлення JWT токену."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Схема для даних, що зберігаються всередині JWT токену.
    Використовується на бекенді для ідентифікації користувача.
    """
    user_id: Optional[UUID] = None