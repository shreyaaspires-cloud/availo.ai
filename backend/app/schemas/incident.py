import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.incident import IncidentStatus
from app.models.resource import ImageAngle


class DamagePairAssessment(BaseModel):
    angle: ImageAngle
    match: bool
    confidence: float
    anomalies: List[str] = Field(default_factory=list)
    closeup_required: bool = False
    before_image_url: Optional[str] = None
    after_image_url: Optional[str] = None


class DamageAssessmentResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    angle: ImageAngle
    before_image_url: str
    after_image_url: str
    confidence_score: float
    anomalies: List[Any] = Field(default_factory=list)
    closeup_required: bool
    closeup_image_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DamageAnalysisResult(BaseModel):
    pairs: List[DamagePairAssessment]
    overall_damage_detected: bool
    overall_confidence: float
    summary: str


class IncidentReportResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    raised_by_id: uuid.UUID
    status: IncidentStatus
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    assessments: List[DamageAssessmentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DisputeResolveRequest(BaseModel):
    outcome: str = Field(..., pattern="^(OWNER|USER|SPLIT)$")
    note: str = Field(..., min_length=2)


class CloseupSubmitRequest(BaseModel):
    angle: ImageAngle
    image_url: str
