import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, VerificationBadge, BadgeStatus
from app.schemas.auth import RegisterRequest
from app.services.auth_service import hash_password


async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(data: RegisterRequest, db: AsyncSession, roles: Optional[list[str]] = None) -> User:
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        roles=roles or ["USER"],
        trust_score=100.0,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_badges(user_id: uuid.UUID, db: AsyncSession) -> list[VerificationBadge]:
    result = await db.execute(
        select(VerificationBadge).where(
            VerificationBadge.user_id == user_id,
            VerificationBadge.status == BadgeStatus.APPROVED,
        )
    )
    return list(result.scalars().all())
