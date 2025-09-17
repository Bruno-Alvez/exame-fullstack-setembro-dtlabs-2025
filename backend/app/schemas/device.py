from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    serial_number: str = Field(..., min_length=12, max_length=12)
    description: Optional[str] = None

    @validator('serial_number')
    def validate_serial_number(cls, v):
        if not re.match(r'^\d{12}$', v):
            raise ValueError('Serial number must be exactly 12 digits')
        return v


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v

    @validator('location')
    def validate_location(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Location cannot be empty')
        return v


class DeviceResponse(DeviceBase):
    id: str
    user_id: str
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_online: bool
    current_health_score: float
    status: str

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int
    skip: int
    limit: int


class DeviceHealthSummary(BaseModel):
    device_id: str
    current_health_score: Optional[float]
    average_health_score: Optional[float]
    min_health_score: Optional[float]
    max_health_score: Optional[float]
    total_heartbeats: int
    hours: int


class DeviceBulkAction(BaseModel):
    action: str = Field(..., regex="^(delete|activate|deactivate)$")
    device_ids: List[str] = Field(..., min_items=1)
