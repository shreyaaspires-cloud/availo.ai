import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UniversalJSONB
from app.models.resource import ImageAngle


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED_OWNER = "RESOLVED_OWNER"
    RESOLVED_USER = "RESOLVED_USER"
    RESOLVED_SPLIT = "RESOLVED_SPLIT"


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    raised_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status_enum"),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
    booking: Mapped["Booking"] = relationship("Booking", back_populates="incident_report")
    raised_by: Mapped["User"] = relationship("User")
    assessments: Mapped[List["DamageAssessment"]] = relationship(
        "DamageAssessment", back_populates="incident", cascade="all, delete-orphan"
    )


class DamageAssessment(Base):
    __tablename__ = "damage_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incident_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    angle: Mapped[ImageAngle] = mapped_column(
        Enum(ImageAngle, name="damage_angle_enum"), nullable=False
    )
    before_image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    after_image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    anomalies: Mapped[List[Any]] = mapped_column(UniversalJSONB, default=list, nullable=False)
    closeup_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    closeup_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["IncidentReport"] = relationship("IncidentReport", back_populates="assessments")
