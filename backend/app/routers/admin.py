import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, VerificationBadge, BadgeStatus
from app.models.booking import Booking, BookingStatus
from app.models.resource import AvailabilitySlot
from app.models.incident import IncidentReport, IncidentStatus
from app.schemas.user import VerificationBadgeResponse, BadgeReviewRequest
from app.schemas.incident import DisputeResolveRequest, IncidentReportResponse
from app.schemas.booking import BookingResponse
from app.schemas.notification import AdminDashboardResponse
from app.dependencies.auth import require_admin
from app.services.incident_service import resolve_dispute
from app.services.notification_service import notify
from app.services.audit_service import log_transition

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    # 1. Pending verifications
    v_res = await db.execute(
        select(func.count(VerificationBadge.id)).where(VerificationBadge.status == BadgeStatus.PENDING)
    )
    pending_verifications = v_res.scalar() or 0

    # 2. Open disputes
    d_res = await db.execute(
        select(func.count(IncidentReport.id)).where(IncidentReport.status == IncidentStatus.OPEN)
    )
    open_disputes = d_res.scalar() or 0

    # 3. Overdue returns
    o_res = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.status == BookingStatus.CHECKED_IN,
            Booking.end_dt < now,
        )
    )
    overdue_returns = o_res.scalar() or 0

    # 4. Active bookings
    a_res = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
        )
    )
    active_bookings = a_res.scalar() or 0

    # 5. Utilisation pct
    total_slots_res = await db.execute(select(func.count(AvailabilitySlot.id)))
    total_slots = total_slots_res.scalar() or 1
    utilisation_pct = round((active_bookings / max(1, total_slots)) * 100.0, 2)

    return AdminDashboardResponse(
        pending_verifications=pending_verifications,
        open_disputes=open_disputes,
        overdue_returns=overdue_returns,
        active_bookings=active_bookings,
        platform_utilisation_pct=utilisation_pct,
    )


@router.get("/verifications", response_model=List[VerificationBadgeResponse])
async def list_pending_verifications(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VerificationBadge)
        .where(VerificationBadge.status == BadgeStatus.PENDING)
        .order_by(VerificationBadge.created_at.asc())
    )
    return list(result.scalars().all())


@router.post("/verifications/{id}/approve", response_model=VerificationBadgeResponse)
async def approve_badge(
    id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    badge = await db.get(VerificationBadge, id)
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    badge.status = BadgeStatus.APPROVED
    badge.verified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(badge)

    await notify(
        user_id=badge.user_id,
        type="BADGE_APPROVED",
        title="Verification Badge Approved",
        body=f"Your credential for badge {badge.badge_type.value} has been verified and approved!",
        booking_id=None,
        db=db,
    )
    return badge


@router.post("/verifications/{id}/reject", response_model=VerificationBadgeResponse)
async def reject_badge(
    id: uuid.UUID,
    body: BadgeReviewRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    badge = await db.get(VerificationBadge, id)
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    badge.status = BadgeStatus.REJECTED
    badge.admin_note = body.reason or "Does not meet verification criteria"
    await db.commit()
    await db.refresh(badge)

    await notify(
        user_id=badge.user_id,
        type="BADGE_REJECTED",
        title="Verification Badge Not Approved",
        body=f"Your credential submission was not approved. Note: {badge.admin_note}",
        booking_id=None,
        db=db,
    )
    return badge


@router.get("/disputes", response_model=List[IncidentReportResponse])
async def list_open_disputes(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.assessments))
        .where(IncidentReport.status.in_([IncidentStatus.OPEN, IncidentStatus.UNDER_REVIEW]))
    )
    return list(result.scalars().all())


@router.post("/disputes/{booking_id}/resolve", response_model=IncidentReportResponse)
async def resolve_booking_dispute(
    booking_id: uuid.UUID,
    body: DisputeResolveRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await resolve_dispute(
        booking_id=booking_id,
        admin_id=current_admin.id,
        outcome=body.outcome,
        note=body.note,
        db=db,
    )


@router.get("/overdue", response_model=List[BookingResponse])
async def list_overdue_bookings(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Booking).where(
            Booking.status == BookingStatus.CHECKED_IN,
            Booking.end_dt < now,
        )
    )
    return list(result.scalars().all())


@router.post("/overdue/{booking_id}/escalate", response_model=BookingResponse)
async def escalate_overdue_booking(
    booking_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    prev_status = booking.status.value
    booking.status = BookingStatus.DISPUTE_OPEN
    await db.commit()

    await log_transition("OVERDUE_ESCALATED", booking.id, current_admin.id, prev_status, BookingStatus.DISPUTE_OPEN.value, db)
    await notify(
        user_id=booking.user_id,
        type="OVERDUE_RETURN",
        title="Urgent: Return Overdue Escalated to Dispute",
        body="Your booking return has been escalated to platform administration due to overdue return.",
        booking_id=booking.id,
        db=db,
    )
    return booking
