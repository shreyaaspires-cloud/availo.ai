import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.condition_report import ConditionReport, ConditionImage, ReportType
from app.models.resource import ImageAngle
from app.storage.supabase_storage import upload_file
from app.services.audit_service import log_transition
from app.services.damage_service import analyze_damage


async def submit_condition_photos(
    booking_id: uuid.UUID,
    report_type: ReportType,
    angle: ImageAngle,
    file_bytes: bytes,
    notes: Optional[str],
    db: AsyncSession,
) -> ConditionImage:
    # Find or create ConditionReport
    rep_res = await db.execute(
        select(ConditionReport).where(
            ConditionReport.booking_id == booking_id,
            ConditionReport.report_type == report_type,
        )
    )
    report = rep_res.scalars().first()
    if not report:
        report = ConditionReport(
            booking_id=booking_id,
            report_type=report_type,
            notes=notes,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

    # Compute sha256 fingerprint for tamper detection
    fingerprint = hashlib.sha256(file_bytes).hexdigest()
    path = f"condition/{booking_id}/{report_type.value}/{angle.value}_{fingerprint[:8]}.jpg"
    img_url = await upload_file(file_bytes, "condition-photos", path, content_type="image/jpeg")

    # Upsert image for that angle
    img_res = await db.execute(
        select(ConditionImage).where(
            ConditionImage.report_id == report.id,
            ConditionImage.angle == angle,
        )
    )
    cond_img = img_res.scalars().first()
    if not cond_img:
        cond_img = ConditionImage(
            report_id=report.id,
            url=img_url,
            angle=angle,
            fingerprint=fingerprint,
            exif_timestamp=datetime.now(timezone.utc),
        )
        db.add(cond_img)
    else:
        cond_img.url = img_url
        cond_img.fingerprint = fingerprint
        cond_img.exif_timestamp = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(cond_img)
    return cond_img


async def complete_checkin(booking_id: uuid.UUID, db: AsyncSession) -> ConditionReport:
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    rep_res = await db.execute(
        select(ConditionReport)
        .options(selectinload(ConditionReport.images))
        .where(
            ConditionReport.booking_id == booking_id,
            ConditionReport.report_type == ReportType.CHECK_IN,
        )
    )
    report = rep_res.scalars().first()
    if not report or len(report.images) < 6:
        raise HTTPException(status_code=400, detail="All 6 angle photos are required to complete check-in")

    prev_status = booking.status.value
    booking.status = BookingStatus.CHECKED_IN
    await db.commit()

    await log_transition("CHECKIN_COMPLETED", booking.id, booking.user_id, prev_status, BookingStatus.CHECKED_IN.value, db)
    return report


async def complete_checkout(booking_id: uuid.UUID, db: AsyncSession):
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify checkin report
    in_rep_res = await db.execute(
        select(ConditionReport).where(
            ConditionReport.booking_id == booking_id,
            ConditionReport.report_type == ReportType.CHECK_IN,
        )
    )
    checkin_report = in_rep_res.scalars().first()

    # Verify checkout report
    out_rep_res = await db.execute(
        select(ConditionReport)
        .options(selectinload(ConditionReport.images))
        .where(
            ConditionReport.booking_id == booking_id,
            ConditionReport.report_type == ReportType.CHECK_OUT,
        )
    )
    checkout_report = out_rep_res.scalars().first()
    if not checkout_report or len(checkout_report.images) < 6:
        raise HTTPException(status_code=400, detail="All 6 angle photos are required to complete check-out")

    prev_status = booking.status.value
    booking.status = BookingStatus.RETURN_SUBMITTED
    await db.commit()

    await log_transition(
        "RETURN_SUBMITTED",
        booking.id,
        booking.user_id,
        prev_status,
        BookingStatus.RETURN_SUBMITTED.value,
        db,
    )

    # Trigger AI damage analysis
    if checkin_report:
        await analyze_damage(booking.id, checkin_report.id, checkout_report.id, db)
