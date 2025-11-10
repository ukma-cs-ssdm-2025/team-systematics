from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List
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

class UserProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    major_name: str
    avatar_url: Optional[HttpUrl] = None

class AvatarUpdateResponse(BaseModel):
    avatar_url: HttpUrl

class NotificationSettingsSchema(BaseModel):
    enabled: bool
    remind_before_hours: List[int]