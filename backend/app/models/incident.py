import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Numeric,
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


class OwnerDecisionType(str, enum.Enum):
    NO_DAMAGE_REPORTED = "NO_DAMAGE_REPORTED"
    DAMAGE_REPORTED = "DAMAGE_REPORTED"


class ClaimStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    RESEARCHER_REVIEW = "RESEARCHER_REVIEW"
    ACCEPTED = "ACCEPTED"
    DISPUTED = "DISPUTED"
    WITHDRAWN = "WITHDRAWN"
    RESOLVED = "RESOLVED"


class ClaimResolutionType(str, enum.Enum):
    REPAIR = "REPAIR"
    COMPENSATION = "COMPENSATION"
    WITHDRAWN = "WITHDRAWN"
    DISMISSED = "DISMISSED"
    ARBITRATED = "ARBITRATED"


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

    # Owner Decision Fields
    owner_decision: Mapped[Optional[OwnerDecisionType]] = mapped_column(
        Enum(OwnerDecisionType, name="owner_decision_type_enum"), nullable=True
    )
    owner_decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_decision_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

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
    raised_by: Mapped["User"] = relationship("User", foreign_keys=[raised_by_id])
    assessments: Mapped[List["DamageAssessment"]] = relationship(
        "DamageAssessment", back_populates="incident", cascade="all, delete-orphan"
    )
    claims: Mapped[List["DamageClaim"]] = relationship(
        "DamageClaim", back_populates="incident", cascade="all, delete-orphan"
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

    # Explainable AI (XAI) persisted columns
    comparison_status: Mapped[str] = mapped_column(String(64), default="comparable", nullable=False)
    similarity_metric: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    similarity_algorithm: Mapped[str] = mapped_column(
        String(128), default="Normalized Grayscale L1 Pixel Difference", nullable=False
    )
    observed_differences: Mapped[List[str]] = mapped_column(UniversalJSONB, default=list, nullable=False)
    damage_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alternative_explanations: Mapped[List[str]] = mapped_column(UniversalJSONB, default=list, nullable=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    difference_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    bounding_boxes: Mapped[List[Dict[str, Any]]] = mapped_column(UniversalJSONB, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["IncidentReport"] = relationship("IncidentReport", back_populates="assessments")


class DamageClaim(Base):
    __tablename__ = "damage_claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incident_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claimant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_angles: Mapped[List[str]] = mapped_column(UniversalJSONB, default=list, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    invoice_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    requested_resolution: Mapped[ClaimResolutionType] = mapped_column(
        Enum(ClaimResolutionType, name="claim_resolution_type_enum"),
        default=ClaimResolutionType.COMPENSATION,
        nullable=False,
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, name="claim_status_enum"),
        default=ClaimStatus.SUBMITTED,
        nullable=False,
    )

    # Researcher Response
    researcher_response: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # ACCEPT, COUNTER, DISPUTE
    researcher_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    researcher_counter_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    researcher_evidence_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Repair Tracking
    repair_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repair_due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    repair_evidence_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    repair_verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    repair_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Financial / Settlement Tracking
    agreed_compensation: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    incident: Mapped["IncidentReport"] = relationship("IncidentReport", back_populates="claims")
    claimant: Mapped["User"] = relationship("User", foreign_keys=[claimant_id])
