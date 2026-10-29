import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.resource import Resource, ResourceImage, ImageAngle
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceFilter,
    EligibilityResult,
    ResourceImageResponse,
    AvailabilitySlotResponse,
)
from app.dependencies.auth import get_current_user, require_owner
from app.services import resource_service
from app.storage.supabase_storage import upload_file

router = APIRouter()


@router.get("", response_model=List[ResourceResponse])
async def list_resources(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_start: Optional[datetime] = Query(None),
    date_end: Optional[datetime] = Query(None),
    badge_required: Optional[str] = Query(None),
    max_daily_rate: Optional[Decimal] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    filters = ResourceFilter(
        search=search,
        category=category,
        location=location,
        date_start=date_start,
        date_end=date_end,
        badge_required=badge_required,
        max_daily_rate=max_daily_rate,
    )
    return await resource_service.list_resources(filters, db)


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    return await resource_service.create_resource(current_user.id, data, db)


@router.get("/{id}", response_model=ResourceResponse)
async def get_resource_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    resource = await resource_service.get_resource(id, db)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.get("/{id}/eligibility", response_model=EligibilityResult)
async def check_resource_eligibility(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await resource_service.check_eligibility(id, current_user, db)


@router.patch("/{id}", response_model=ResourceResponse)
async def update_resource(
    id: uuid.UUID,
    data: ResourceUpdate,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    return await resource_service.update_resource(id, current_user.id, data, db)


@router.delete("/{id}")
async def delete_resource(
    id: uuid.UUID,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    await resource_service.delete_resource(id, current_user.id, db)
    return {"message": "Resource deactivated successfully"}


@router.get("/{id}/availability", response_model=List[AvailabilitySlotResponse])
async def get_availability(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    resource = await resource_service.get_resource(id, db)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    # Return slots or simulated availability for the next 30 days
    now = datetime.now(timezone.utc)
    slots = []
    for day in range(30):
        start = now + timedelta(days=day)
        end = start + timedelta(days=1)
        avail = await resource_service.check_availability(id, start, end, db)
        slots.append(
            AvailabilitySlotResponse(
                id=uuid.uuid4(),
                start_dt=start,
                end_dt=end,
                is_blocked=not avail,
            )
        )
    return slots


@router.post("/{id}/images", response_model=ResourceImageResponse)
async def upload_resource_image(
    id: uuid.UUID,
    file: UploadFile = File(...),
    angle: ImageAngle = Form(ImageAngle.FRONT),
    is_primary: bool = Form(False),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    resource = await resource_service.get_resource(id, db)
    if not resource or resource.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add images for this resource")

    contents = await file.read()
    path = f"resources/{id}/{angle.value}_{file.filename}"
    url = await upload_file(contents, "condition-photos", path, content_type=file.content_type or "image/jpeg")

    img = ResourceImage(
        resource_id=id,
        url=url,
        angle=angle,
        is_primary=is_primary,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return img
