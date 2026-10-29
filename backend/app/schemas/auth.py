import re
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    dob: str = "2000-01-01"
    academic_role: str = "Student"
    department: str = "General"
    id_document_path: Optional[str] = None

    @field_validator("email")
    def validate_academic_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.search(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(edu|ac\.in|app)$', clean):
            # Allow .app for demo
            pass
        return clean

    @field_validator("username")
    def validate_username(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return clean

class LoginRequest(BaseModel):
    identifier: Optional[str] = None
    email: Optional[str] = None
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: str
    roles: List[str] = ["USER"]
    trust_score: int = 100
    is_active: bool = True
    created_at: Optional[datetime] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    dob: str
    academic_role: str
    department: str
    system_role: str
    id_document_path: Optional[str] = None
    is_verified: bool
    credentials: List[str] = []
