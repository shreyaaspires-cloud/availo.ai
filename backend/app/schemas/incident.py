import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.incident import IncidentStatus, ClaimStatus, ClaimResolutionType, OwnerDecisionType
from app.models.resource import ImageAngle


class DamagePairAssessment(BaseModel):
    angle: ImageAngle
    match: bool
    confidence: float
    anomalies: List[str] = Field(default_factory=list)
    closeup_required: bool = False
    before_image_url: Optional[str] = None
    after_image_url: Optional[str] = None
    comparison_status: str = Field(default="comparable")
    similarity_metric: float = Field(default=1.0)
    similarity_algorithm: str = Field(default="Normalized Grayscale L1 Pixel Difference (PIL/OpenCV)")
    observed_differences: List[str] = Field(default_factory=list)
    damage_category: Optional[str] = None
    location_description: Optional[str] = None
    supporting_evidence: Optional[str] = None
    alternative_explanations: List[str] = Field(default_factory=list)
    human_review_required: bool = False
    difference_image_url: Optional[str] = None
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list)


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
    comparison_status: Optional[str] = "comparable"
    similarity_metric: Optional[float] = 1.0
    similarity_algorithm: Optional[str] = "Normalized Grayscale L1 Pixel Difference"
    observed_differences: Optional[List[str]] = Field(default_factory=list)
    damage_category: Optional[str] = None
    location_description: Optional[str] = None
    supporting_evidence: Optional[str] = None
    alternative_explanations: Optional[List[str]] = Field(default_factory=list)
    human_review_required: Optional[bool] = False
    difference_image_url: Optional[str] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class OwnerDecisionRequest(BaseModel):
    decision: OwnerDecisionType
    notes: Optional[str] = None


class DamageClaimCreate(BaseModel):
    description: str = Field(..., min_length=10)
    photo_angles: List[str] = Field(default_factory=list)
    justification: str = Field(..., min_length=10)
    estimated_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    invoice_url: Optional[str] = None
    requested_resolution: ClaimResolutionType = Field(default=ClaimResolutionType.COMPENSATION)


class DamageClaimResponseRequest(BaseModel):
    action: str = Field(..., pattern="^(ACCEPT|COUNTER|DISPUTE)$")
    note: str = Field(..., min_length=5)
    counter_amount: Optional[Decimal] = Field(default=None, ge=0)
    evidence_url: Optional[str] = None


class RepairSubmitRequest(BaseModel):
    repair_plan: str = Field(..., min_length=10)
    due_date: datetime
    evidence_url: Optional[str] = None


class DamageClaimResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    claimant_id: uuid.UUID
    description: str
    photo_angles: List[str]
    justification: str
    estimated_cost: Decimal
    invoice_url: Optional[str] = None
    requested_resolution: ClaimResolutionType
    status: ClaimStatus
    researcher_response: Optional[str] = None
    researcher_note: Optional[str] = None
    researcher_counter_amount: Optional[Decimal] = None
    researcher_evidence_url: Optional[str] = None
    responded_at: Optional[datetime] = None
    repair_plan: Optional[str] = None
    repair_due_date: Optional[datetime] = None
    repair_evidence_url: Optional[str] = None
    repair_verified_at: Optional[datetime] = None
    agreed_compensation: Optional[Decimal] = None
    payment_reference: Optional[str] = None
    settled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DamageAnalysisResult(BaseModel):
    pairs: List[DamagePairAssessment]
    overall_damage_detected: bool
    overall_confidence: float
    summary: str
    model_version: Optional[str] = "Gemini-2.0-Flash + Perceptual OpenCV XAI Engine"


class IncidentReportResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    raised_by_id: uuid.UUID
    status: IncidentStatus
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    owner_decision: Optional[OwnerDecisionType] = None
    owner_decision_at: Optional[datetime] = None
    owner_decision_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    assessments: List[DamageAssessmentResponse] = Field(default_factory=list)
    claims: List[DamageClaimResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DisputeResolveRequest(BaseModel):
    outcome: str = Field(..., pattern="^(OWNER|USER|SPLIT)$")
    note: str = Field(..., min_length=2)


class CloseupSubmitRequest(BaseModel):
    angle: ImageAngle
    image_url: str
