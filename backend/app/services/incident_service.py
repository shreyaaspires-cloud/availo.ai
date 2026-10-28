import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.incident import IncidentReport, IncidentStatus
from app.services.audit_service import log_transition
from app.services.notification_service import notify, notify_escrow_released


async def resolve_dispute(
    booking_id: uuid.UUID,
    admin_id: uuid.UUID,
    outcome: str,
    note: str,
    db: AsyncSession,
) -> IncidentReport:
    inc_res = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.booking))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = inc_res.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    booking = incident.booking
    prev_status = booking.status.value

    # Outcome handling: OWNER, USER, SPLIT
    if outcome == "OWNER":
        incident.status = IncidentStatus.RESOLVED_OWNER
        booking.status = BookingStatus.RESOLVED_OWNER
    elif outcome == "USER":
        incident.status = IncidentStatus.RESOLVED_USER
        booking.status = BookingStatus.RESOLVED_USER
        await notify_escrow_released(booking.user_id, float(booking.deposit_amount), booking.id, db)
    elif outcome == "SPLIT":
        incident.status = IncidentStatus.RESOLVED_SPLIT
        booking.status = BookingStatus.RESOLVED_SPLIT
        split_amount = float(booking.deposit_amount) / 2.0
        await notify_escrow_released(booking.user_id, split_amount, booking.id, db)

    incident.resolution_note = note
    incident.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    await log_transition(
        "DISPUTE_RESOLVED",
        booking.id,
        admin_id,
        prev_status,
        booking.status.value,
        db,
        metadata={"outcome": outcome, "note": note},
    )

    await notify(
        user_id=booking.user_id,
        type="DISPUTE_RESOLVED",
        title="Dispute Resolution Completed",
        body=f"Your dispute has been resolved with outcome: {outcome}. Note: {note}",
        booking_id=booking.id,
        db=db,
    )

    return incident
