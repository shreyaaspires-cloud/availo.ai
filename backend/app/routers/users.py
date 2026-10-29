import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, VerificationBadge, BadgeStatus, BadgeType
from app.schemas.user import (
    BadgeApplyRequest,
    VerificationBadgeResponse,
    UserProfileResponse,
)
from app.dependencies.auth import get_current_user
from app.services.gemini_service import prescreen_verification_document

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    badges_res = await db.execute(
        select(VerificationBadge).where(VerificationBadge.user_id == current_user.id)
    )
    badges = list(badges_res.scalars().all())
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        roles=current_user.roles,
        trust_score=current_user.trust_score,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        badges=badges,
    )


@router.post("/me/badges/apply")
async def apply_for_badge(
    data: BadgeApplyRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Create VerificationBadge with PENDING status
    badge = VerificationBadge(
        user_id=current_user.id,
        badge_type=data.badge_type,
        document_url=data.document_url,
        status=BadgeStatus.PENDING,
    )
    db.add(badge)
    await db.commit()
    await db.refresh(badge)

    # Trigger prescreening as background task
    async def run_prescreen(badge_id: uuid.UUID, doc_url: str, b_type: str):
        prescreen_res = await prescreen_verification_document(doc_url, b_type)
        # Note can be updated on the badge record if needed

    background_tasks.add_task(
        run_prescreen,
        badge.id,
        data.document_url,
        data.badge_type.value,
    )

    return {"message": "Application submitted. Admin review within 24 hours.", "badge_id": badge.id}
