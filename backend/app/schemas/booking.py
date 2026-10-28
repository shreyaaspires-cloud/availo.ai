import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    resource_id: uuid.UUID
    start_dt: datetime
    end_dt: datetime
    purpose: str = Field(default="", max_length=1000)


class BookingRejectRequest(BaseModel):
    reason: str = Field(..., min_length=2)


class BookingPaymentConfirmRequest(BaseModel):
    razorpay_payment_id: str = Field(..., min_length=2)


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = None


class BookingResponse(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    user_id: uuid.UUID
    status: BookingStatus
    start_dt: datetime
    end_dt: datetime
    purpose: str
    total_amount: Decimal
    deposit_amount: Decimal
    cancellation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    payment_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WaitlistEntryResponse(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    user_id: uuid.UUID
    requested_start: datetime
    requested_end: datetime
    position: int
    notified_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
