from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

class IssueImageUpload(BaseModel):
    device_lat: Optional[float] = None
    device_lng: Optional[float] = None
    description: Optional[str] = None

class IssueImageOut(BaseModel):
    id: int
    cluster_id: Optional[int]
    image_url: str
    moondream_output: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IssueClusterOut(BaseModel):
    id: int
    category: str
    severity_hint: str
    confidence: float
    department_id: Optional[int]
    zone: str
    postal_code: str
    affected_count: int
    priority_score: float
    sla_deadline: Optional[datetime]
    escalation_tier: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IssueClusterDetail(IssueClusterOut):
    images: List[IssueImageOut]
    officer_name: Optional[str] = None

class HeatmapPoint(BaseModel):
    lat: float
    lng: float
    priority_score: float
    category: str

class CitizenConfirmationCreate(BaseModel):
    cluster_id: int
    status: str

    @field_validator('status')
    @classmethod
    def check_status(cls, v):
        if v not in ('confirmed', 'disputed'):
            raise ValueError("status must be 'confirmed' or 'disputed'")
        return v

class CompletionEvidenceCreate(BaseModel):
    cluster_id: int
    exif_lat: Optional[float] = None
    exif_lng: Optional[float] = None

class QueueItem(IssueClusterOut):
    days_pending: int
    officer_name: Optional[str] = None
    escalation_info: Optional[str] = None
