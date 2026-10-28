import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.models.resource import Resource
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingRejectRequest,
    BookingCancelRequest,
    BookingPaymentConfirmRequest,
)
from app.dependencies.auth import get_current_user, require_owner
from app.services import booking_service

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.create_booking_request(current_user.id, data.resource_id, data, db)


@router.get("", response_model=List[BookingResponse])
async def list_user_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # If user is owner, returns bookings of resources they own OR bookings they made
    result = await db.execute(
        select(Booking)
        .join(Resource, Booking.resource_id == Resource.id)
        .where(
            or_(
                Booking.user_id == current_user.id,
                Resource.owner_id == current_user.id,
            )
        )
        .order_by(Booking.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{id}", response_model=BookingResponse)
async def get_booking_detail(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.get_booking(id, current_user, db)


@router.post("/{id}/approve", response_model=BookingResponse)
async def approve_booking_endpoint(
    id: uuid.UUID,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.approve_booking(id, current_user.id, db)


@router.post("/{id}/reject", response_model=BookingResponse)
async def reject_booking_endpoint(
    id: uuid.UUID,
    body: BookingRejectRequest,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.reject_booking(id, current_user.id, body.reason, db)


@router.post("/{id}/cancel", response_model=BookingResponse)
async def cancel_booking_endpoint(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.cancel_booking(id, current_user.id, db)


@router.post("/{id}/confirm-payment", response_model=BookingResponse)
async def confirm_payment_endpoint(
    id: uuid.UUID,
    body: BookingPaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await db.get(Booking, id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm payment for this booking")
    return await booking_service.confirm_payment(id, body.razorpay_payment_id, db)


@router.post("/waitlist/{waitlist_id}/accept", response_model=BookingResponse)
async def accept_waitlist_endpoint(
    waitlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.accept_waitlist_promotion(waitlist_id, current_user.id, db)


@router.post("/waitlist/{waitlist_id}/decline")
async def decline_waitlist_endpoint(
    waitlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.decline_waitlist_promotion(waitlist_id, current_user.id, db)


