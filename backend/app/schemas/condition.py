import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.condition_report import ReportType
from app.models.resource import ImageAngle


class ConditionImageResponse(BaseModel):
    id: uuid.UUID
    report_id: uuid.UUID
    url: str
    angle: ImageAngle
    exif_timestamp: Optional[datetime] = None
    exif_gps_lat: Optional[float] = None
    exif_gps_lon: Optional[float] = None
    fingerprint: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConditionReportResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    report_type: ReportType
    submitted_at: datetime
    notes: Optional[str] = None
    created_at: datetime
    images: List[ConditionImageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConditionReportSubmit(BaseModel):
    notes: Optional[str] = None
