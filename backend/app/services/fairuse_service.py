import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.config import settings
from app.models.booking import Booking, BookingStatus


async def check_fair_use(user_id: uuid.UUID, resource_id: uuid.UUID, db: AsyncSession, limit_per_week: int = 2):
    # 1. Check active bookings cap per user
    active_statuses = [
        BookingStatus.PENDING_APPROVAL,
        BookingStatus.APPROVED,
        BookingStatus.AWAITING_SIGNATURES,
        BookingStatus.AWAITING_PAYMENT,
        BookingStatus.CONFIRMED,
        BookingStatus.CHECKED_IN,
    ]
    active_count_res = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.user_id == user_id,
            Booking.status.in_(active_statuses),
        )
    )
    active_count = active_count_res.scalar() or 0
    if active_count >= settings.MAX_ACTIVE_BOOKINGS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fair-use limit reached: Maximum {settings.MAX_ACTIVE_BOOKINGS_PER_USER} active bookings allowed per user.",
        )

    # 2. Check bookings on this specific resource in the current 7-day window
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_res = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.user_id == user_id,
            Booking.resource_id == resource_id,
            Booking.created_at >= one_week_ago,
            Booking.status != BookingStatus.CANCELLED,
            Booking.status != BookingStatus.REJECTED,
        )
    )
    recent_count = recent_res.scalar() or 0
    if recent_count >= limit_per_week:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource fair-use limit reached: Maximum {limit_per_week} bookings allowed per week for this item.",
        )
