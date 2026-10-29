import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    roles: List[str]


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roles: List[str]
    trust_score: float
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
