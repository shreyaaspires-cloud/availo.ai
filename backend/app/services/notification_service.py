import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.models.booking import Booking
from app.services.connection_manager import connection_manager
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)


async def notify(
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: str,
    booking_id: Optional[uuid.UUID],
    db: AsyncSession,
) -> Notification:
    # 1. Create DB notification
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        is_read=False,
        related_booking_id=booking_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # 2. Push via WebSocket
    payload = {
        "id": str(notif.id),
        "type": type,
        "title": title,
        "body": body,
        "booking_id": str(booking_id) if booking_id else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await connection_manager.send_to_user(str(user_id), payload)

    # 3. Send email via Resend if high-priority event
    email_priority_types = [
        "BOOKING_APPROVED",
        "DAMAGE_DETECTED",
        "OVERDUE_RETURN",
        "CONTRACT_READY",
    ]
    if type in email_priority_types and settings.RESEND_API_KEY and "dummy" not in settings.RESEND_API_KEY:
        # Deduplicate using Redis
        dedup_key = f"notify:{user_id}:{type}:{booking_id}"
        if not cache_get(dedup_key):
            try:
                user_res = await db.execute(select(User).where(User.id == user_id))
                user = user_res.scalars().first()
                if user and user.email:
                    import resend
                    resend.api_key = settings.RESEND_API_KEY
                    resend.Emails.send({
                        "from": settings.RESEND_FROM_EMAIL,
                        "to": user.email,
                        "subject": title,
                        "html": f"<p>{body}</p>",
                    })
                    cache_set(dedup_key, "1", ex=60)
            except Exception as e:
                logger.error("Failed to send Resend email: %s", e)

    return notif


async def notify_booking_request(owner_id: uuid.UUID, booking: Booking, db: AsyncSession):
    await notify(
        user_id=owner_id,
        type="BOOKING_REQUESTED",
        title="New Booking Request",
        body=f"You have a new booking request for your resource.",
        booking_id=booking.id,
        db=db,
    )


async def notify_booking_approved(user_id: uuid.UUID, booking: Booking, db: AsyncSession):
    await notify(
        user_id=user_id,
        type="BOOKING_APPROVED",
        title="Booking Approved",
        body="Your booking request has been approved! Please sign the contract to proceed.",
        booking_id=booking.id,
        db=db,
    )


async def notify_booking_rejected(user_id: uuid.UUID, booking: Booking, reason: str, db: AsyncSession):
    await notify(
        user_id=user_id,
        type="BOOKING_REJECTED",
        title="Booking Rejected",
        body=f"Your booking request was rejected. Reason: {reason}",
        booking_id=booking.id,
        db=db,
    )


async def notify_contract_ready(user_id: uuid.UUID, owner_id: uuid.UUID, contract_id: uuid.UUID, booking_id: uuid.UUID, db: AsyncSession):
    await notify(
        user_id=user_id,
        type="CONTRACT_READY",
        title="Rental Contract Ready for Signature",
        body="Your rental contract has been generated. Please review and sign.",
        booking_id=booking_id,
        db=db,
    )
    await notify(
        user_id=owner_id,
        type="CONTRACT_READY",
        title="Rental Contract Ready for Signature",
        body="A rental contract is ready for your countersignature.",
        booking_id=booking_id,
        db=db,
    )


async def notify_damage_detected(owner_id: uuid.UUID, booking: Booking, confidence: float, db: AsyncSession):
    await notify(
        user_id=owner_id,
        type="DAMAGE_DETECTED",
        title="Damage Detected on Returned Resource",
        body=f"AI detected potential damage with confidence {confidence * 100:.1f}%. Review required.",
        booking_id=booking.id,
        db=db,
    )


async def notify_closeup_required(user_id: uuid.UUID, booking: Booking, angles: List[str], db: AsyncSession):
    await notify(
        user_id=user_id,
        type="CLOSEUP_REQUIRED",
        title="Additional Photos Required",
        body=f"Please upload close-up photos for angles: {', '.join(angles)}.",
        booking_id=booking.id,
        db=db,
    )


async def notify_escrow_released(user_id: uuid.UUID, amount: float, booking_id: uuid.UUID, db: AsyncSession):
    await notify(
        user_id=user_id,
        type="ESCROW_RELEASED",
        title="Deposit Escrow Released",
        body=f"Security deposit of ₹{amount} has been released back to your account.",
        booking_id=booking_id,
        db=db,
    )


async def notify_dispute_opened(admin_id: uuid.UUID, booking: Booking, db: AsyncSession):
    await notify(
        user_id=admin_id,
        type="DISPUTE_OPENED",
        title="New Dispute Escalation",
        body=f"Dispute opened for booking {booking.id}. Admin review required.",
        booking_id=booking.id,
        db=db,
    )
