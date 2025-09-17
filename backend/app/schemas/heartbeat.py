from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class HeartbeatBase(BaseModel):
    cpu_usage: float = Field(..., ge=0, le=100)
    ram_usage: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=-50, le=150)
    free_disk_space: float = Field(..., ge=0, le=100)
    dns_latency: float = Field(..., ge=0, le=10000)
    connectivity: bool
    boot_timestamp: datetime

    @validator('cpu_usage', 'ram_usage', 'free_disk_space')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Percentage values must be between 0 and 100')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if not -50 <= v <= 150:
            raise ValueError('Temperature must be between -50 and 150 degrees Celsius')
        return v

    @validator('dns_latency')
    def validate_dns_latency(cls, v):
        if not 0 <= v <= 10000:
            raise ValueError('DNS latency must be between 0 and 10000 milliseconds')
        return v


class HeartbeatCreate(HeartbeatBase):
    pass


class HeartbeatResponse(HeartbeatBase):
    id: str
    device_id: str
    health_score: float
    timestamp: datetime
    is_healthy: bool
    is_critical: bool
    metrics_summary: dict

    class Config:
        from_attributes = True


class HeartbeatListResponse(BaseModel):
    heartbeats: List[HeartbeatResponse]
    device_id: str
    total: int
    hours: int


class HeartbeatMetrics(BaseModel):
    cpu_usage: float
    ram_usage: float
    temperature: float
    free_disk_space: float
    dns_latency: float
    connectivity: bool
    health_score: float


class HeartbeatStats(BaseModel):
    device_id: str
    period_hours: int
    total_heartbeats: int
    average_health_score: float
    min_health_score: float
    max_health_score: float
    uptime_percentage: float
    last_heartbeat: Optional[datetime]
