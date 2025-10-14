from pydantic import BaseModel
from typing import List

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]

class LoginResponse(BaseModel):
    token: str
    user: UserResponse
