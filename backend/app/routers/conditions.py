import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.condition_report import ConditionReport, ReportType
from app.models.resource import ImageAngle
from app.schemas.condition import ConditionReportResponse, ConditionImageResponse
from app.dependencies.auth import get_current_user
from app.services import condition_service

router = APIRouter()


@router.post("/{booking_id}/photos", response_model=ConditionImageResponse)
async def upload_condition_photo(
    booking_id: uuid.UUID,
    file: UploadFile = File(...),
    report_type: ReportType = Form(...),
    angle: ImageAngle = Form(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    return await condition_service.submit_condition_photos(
        booking_id=booking_id,
        report_type=report_type,
        angle=angle,
        file_bytes=file_bytes,
        notes=notes,
        db=db,
    )


@router.post("/{booking_id}/checkin-complete", response_model=ConditionReportResponse)
async def checkin_complete(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await condition_service.complete_checkin(booking_id, db)


@router.post("/{booking_id}/checkout-complete")
async def checkout_complete(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await condition_service.complete_checkout(booking_id, db)
    return {"message": "Checkout submitted. AI Damage analysis running."}


@router.get("/{booking_id}", response_model=List[ConditionReportResponse])
async def get_booking_conditions(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConditionReport)
        .options(selectinload(ConditionReport.images))
        .where(ConditionReport.booking_id == booking_id)
    )
    return list(result.scalars().all())
