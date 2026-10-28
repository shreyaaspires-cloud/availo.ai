import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UniversalArray


class BadgeType(str, enum.Enum):
    STUDENT = "STUDENT"
    RESEARCHER = "RESEARCHER"
    PROFESSIONAL = "PROFESSIONAL"
    FACULTY = "FACULTY"


class BadgeStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[List[str]] = mapped_column(UniversalArray(String), default=["USER"], nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    badges: Mapped[List["VerificationBadge"]] = relationship(
        "VerificationBadge", back_populates="user", cascade="all, delete-orphan"
    )
    resources: Mapped[List["Resource"]] = relationship(
        "Resource", back_populates="owner", cascade="all, delete-orphan"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="user", foreign_keys="Booking.user_id"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )


class VerificationBadge(Base):
    __tablename__ = "verification_badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_type: Mapped[BadgeType] = mapped_column(
        Enum(BadgeType, name="badge_type_enum"), nullable=False
    )
    document_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[BadgeStatus] = mapped_column(
        Enum(BadgeStatus, name="badge_status_enum"), default=BadgeStatus.PENDING, nullable=False
    )
    admin_note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="badges")
