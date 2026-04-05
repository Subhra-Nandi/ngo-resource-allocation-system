import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    category: str = Field(..., pattern="^(FOOD|MEDICAL|SHELTER|WASH|OTHER)$")
    name: str = Field(..., min_length=2, max_length=200)
    quantity: int = Field(..., ge=0)
    unit: str | None = None
    depot_lat: float = Field(..., ge=-90, le=90)
    depot_lng: float = Field(..., ge=-180, le=180)
    depot_address: str | None = None
    depot_name: str | None = None
    expiry_date: date | None = None


class ResourceUpdate(BaseModel):
    quantity: int | None = Field(None, ge=0)
    depot_lat: float | None = None
    depot_lng: float | None = None
    depot_address: str | None = None
    expiry_date: date | None = None


class ResourceResponse(BaseModel):
    id: uuid.UUID
    ngo_id: uuid.UUID
    category: str
    name: str
    quantity: int
    unit: str | None
    depot_lat: float | None = None
    depot_lng: float | None = None
    depot_address: str | None
    depot_name: str | None
    expiry_date: date | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class NgoRegister(BaseModel):
    ngo_name: str = Field(..., min_length=3, max_length=200)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)
    contact_phone: str | None = None


class NgoLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"