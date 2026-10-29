import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
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
    # Explainable AI (XAI) additions
    comparison_status: str = Field(default="comparable")  # comparable | partially_comparable | not_comparable
    similarity_metric: float = Field(default=1.0)
    similarity_algorithm: str = Field(default="Normalized Grayscale L1 Pixel Difference (PIL/OpenCV)")
    observed_differences: List[str] = Field(default_factory=list)
    damage_category: Optional[str] = None  # scratch, crack, dent, deformation, missing_part, stain, wear, none
    location_description: Optional[str] = None
    supporting_evidence: Optional[str] = None
    alternative_explanations: List[str] = Field(default_factory=list)  # lighting, shadows, camera_angle, blur, dust
    human_review_required: bool = False
    difference_image_url: Optional[str] = None
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list)  # [{'box_2d': [ymin, xmin, ymax, xmax], 'label': str}]


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
    # XAI fields exposed to API
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
    created_at: datetime
    assessments: List[DamageAssessmentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DisputeResolveRequest(BaseModel):
    outcome: str = Field(..., pattern="^(OWNER|USER|SPLIT)$")
    note: str = Field(..., min_length=2)


class CloseupSubmitRequest(BaseModel):
    angle: ImageAngle
    image_url: str
