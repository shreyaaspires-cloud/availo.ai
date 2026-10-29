import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.user import BadgeType, BadgeStatus


class VerificationBadgeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    badge_type: BadgeType
    document_url: str
    status: BadgeStatus
    admin_note: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BadgeApplyRequest(BaseModel):
    badge_type: BadgeType
    document_url: str


class BadgeReviewRequest(BaseModel):
    reason: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roles: List[str]
    trust_score: float
    is_active: bool
    created_at: datetime
    badges: List[VerificationBadgeResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
