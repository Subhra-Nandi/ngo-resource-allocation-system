import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReportSubmit(BaseModel):
    """What a field worker or affected user sends."""
    description: str = Field(..., min_length=5)
    need_type: str | None = Field(None, pattern="^(FOOD|MEDICAL|SHELTER|WASH|OTHER)$")
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    location_name: str | None = None
    affected_count: int | None = Field(None, ge=1)
    severity: int | None = Field(None, ge=1, le=5)
    source: str = Field(default="affected_user", pattern="^(field_worker|affected_user)$")


class ReportAccepted(BaseModel):
    """Returned immediately on submit — user polls status with request_id."""
    request_id: uuid.UUID
    status: str
    message: str


class MatchedNgo(BaseModel):
    ngo_name: str
    depot_address: str | None
    contact_phone: str | None
    resource_name: str
    quantity_available: int
    eta_minutes: int
    distance_km: float


class ReportStatusResponse(BaseModel):
    request_id: uuid.UUID
    status: str
    message: str
    matched_ngo: MatchedNgo | None = None
    created_at: datetime

    model_config = {"from_attributes": True}