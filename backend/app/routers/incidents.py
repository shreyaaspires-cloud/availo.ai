import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.incident import IncidentReport, DamageAssessment
from app.schemas.incident import (
    IncidentReportResponse,
    DamageAssessmentResponse,
    DamageAnalysisResult,
    CloseupSubmitRequest,
)
from app.dependencies.auth import get_current_user
from app.services import damage_service

router = APIRouter()


@router.get("/{booking_id}/damage-assessment", response_model=IncidentReportResponse)
async def get_incident_damage_assessment(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncidentReport)
        .options(selectinload(IncidentReport.assessments))
        .where(IncidentReport.booking_id == booking_id)
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="No damage assessment recorded for this booking")
    return incident


@router.post("/{booking_id}/closeup")
async def submit_closeup_photo(
    booking_id: uuid.UUID,
    body: CloseupSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await damage_service.submit_closeup(booking_id, body.angle.value, body.image_url, db)
    return {"message": "Closeup image saved"}
