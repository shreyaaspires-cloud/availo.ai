import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.resource import ImageAngle


class ResourceImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    angle: ImageAngle
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySlotResponse(BaseModel):
    id: uuid.UUID
    start_dt: datetime
    end_dt: datetime
    is_blocked: bool

    model_config = ConfigDict(from_attributes=True)


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str
    category: str
    location: str
    daily_rate: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    deposit_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    max_booking_days: int = Field(default=7, ge=1)
    requires_badge: List[str] = Field(default_factory=list)
    condition: str = "Good condition"
    fair_use_limit_per_week: int = Field(default=2, ge=1)


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    daily_rate: Optional[Decimal] = None
    deposit_amount: Optional[Decimal] = None
    max_booking_days: Optional[int] = None
    requires_badge: Optional[List[str]] = None
    condition: Optional[str] = None
    fair_use_limit_per_week: Optional[int] = None
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str
    category: str
    location: str
    daily_rate: Decimal
    deposit_amount: Decimal
    max_booking_days: int
    requires_badge: List[str]
    condition: str
    is_active: bool
    fair_use_limit_per_week: int
    created_at: datetime
    updated_at: datetime
    images: List[ResourceImageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResourceFilter(BaseModel):
    search: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    badge_required: Optional[str] = None
    max_daily_rate: Optional[Decimal] = None


class EligibilityResult(BaseModel):
    eligible: bool
    missing_badges: List[str] = Field(default_factory=list)
    reason: str = ""
