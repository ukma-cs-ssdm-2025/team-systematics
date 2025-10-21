from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserSchema(UserBase):
    id: UUID
    is_active: bool

    class Config:
        orm_mode = True