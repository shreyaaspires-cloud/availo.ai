import uuid
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.resource import Resource, ResourceImage, AvailabilitySlot, ImageAngle
from app.models.booking import Booking, BookingStatus
from app.models.user import User, VerificationBadge, BadgeStatus
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceFilter,
    EligibilityResult,
)
from app.utils.cache import cache_get, cache_set, cache_delete


async def create_resource(owner_id: uuid.UUID, data: ResourceCreate, db: AsyncSession) -> Resource:
    resource = Resource(
        owner_id=owner_id,
        title=data.title,
        description=data.description,
        category=data.category,
        location=data.location,
        daily_rate=data.daily_rate,
        deposit_amount=data.deposit_amount,
        max_booking_days=data.max_booking_days,
        requires_badge=data.requires_badge,
        condition=data.condition,
        fair_use_limit_per_week=data.fair_use_limit_per_week,
        is_active=True,
    )
    db.add(resource)
    await db.commit()
    cache_delete("resources:list:*")
    return await get_resource(resource.id, db)


async def get_resource(resource_id: uuid.UUID, db: AsyncSession) -> Optional[Resource]:
    result = await db.execute(
        select(Resource)
        .options(selectinload(Resource.images), selectinload(Resource.availability_slots))
        .where(Resource.id == resource_id)
    )
    return result.scalars().first()


async def list_resources(filters: ResourceFilter, db: AsyncSession) -> List[Resource]:
    # Query with filters
    stmt = (
        select(Resource)
        .options(selectinload(Resource.images))
        .where(Resource.is_active == True)
    )

    if filters.category:
        stmt = stmt.where(Resource.category.ilike(f"%{filters.category}%"))
    if filters.location:
        stmt = stmt.where(Resource.location.ilike(f"%{filters.location}%"))
    if filters.max_daily_rate is not None:
        stmt = stmt.where(Resource.daily_rate <= filters.max_daily_rate)
    if filters.search:
        # Full text search or ilike fallback
        search_term = f"%{filters.search}%"
        stmt = stmt.where(
            or_(
                Resource.title.ilike(search_term),
                Resource.description.ilike(search_term),
                Resource.location.ilike(search_term),
            )
        )

    result = await db.execute(stmt)
    resources = list(result.scalars().all())

    # Date availability filter if requested
    if filters.date_start and filters.date_end:
        available_resources = []
        for r in resources:
            is_avail = await check_availability(r.id, filters.date_start, filters.date_end, db)
            if is_avail:
                available_resources.append(r)
        return available_resources

    return resources


async def update_resource(
    resource_id: uuid.UUID,
    owner_id: uuid.UUID,
    data: ResourceUpdate,
    db: AsyncSession,
) -> Resource:
    resource = await get_resource(resource_id, db)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this resource")

    update_dict = data.model_dump(exclude_unset=True)
    for field, val in update_dict.items():
        setattr(resource, field, val)

    await db.commit()
    await db.refresh(resource)
    return resource


async def delete_resource(resource_id: uuid.UUID, owner_id: uuid.UUID, db: AsyncSession):
    resource = await get_resource(resource_id, db)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this resource")

    resource.is_active = False
    await db.commit()


async def check_availability(
    resource_id: uuid.UUID,
    start_dt: datetime,
    end_dt: datetime,
    db: AsyncSession,
) -> bool:
    """Returns True if there is NO conflicting booking for that time window."""
    conflicting_statuses = [
        BookingStatus.CONFIRMED,
        BookingStatus.CHECKED_IN,
        BookingStatus.AWAITING_PAYMENT,
    ]
    query = select(Booking.id).where(
        Booking.resource_id == resource_id,
        Booking.status.in_(conflicting_statuses),
        Booking.start_dt < end_dt,
        Booking.end_dt > start_dt,
    )
    result = await db.execute(query)
    conflict = result.scalars().first()
    return conflict is None


async def check_eligibility(
    resource_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> EligibilityResult:
    resource = await get_resource(resource_id, db)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not resource.requires_badge:
        return EligibilityResult(eligible=True, missing_badges=[], reason="No special badge required")

    user_badges_res = await db.execute(
        select(VerificationBadge.badge_type).where(
            VerificationBadge.user_id == user.id,
            VerificationBadge.status == BadgeStatus.APPROVED,
        )
    )
    user_badges = {b.value for b in user_badges_res.scalars().all()}

    missing = [req for req in resource.requires_badge if req not in user_badges]
    if missing:
        return EligibilityResult(
            eligible=False,
            missing_badges=missing,
            reason=f"User is missing required verified badges: {', '.join(missing)}",
        )

    return EligibilityResult(eligible=True, missing_badges=[], reason="All badge requirements satisfied")
