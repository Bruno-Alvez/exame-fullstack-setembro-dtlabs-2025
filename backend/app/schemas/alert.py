from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class AlertCondition(BaseModel):
    metric: str = Field(..., pattern="^(cpu_usage|ram_usage|temperature|free_disk_space|dns_latency|connectivity|health_score)$")
    operator: str = Field(..., pattern="^(>|>=|<|<=|==|!=)$")
    value: float

    @validator('value')
    def validate_value(cls, v, values):
        metric = values.get('metric')
        if metric in ['cpu_usage', 'ram_usage', 'free_disk_space'] and not (0 <= v <= 100):
            raise ValueError('Percentage values must be between 0 and 100')
        elif metric == 'temperature' and not (-50 <= v <= 150):
            raise ValueError('Temperature must be between -50 and 150 degrees Celsius')
        elif metric == 'dns_latency' and not (0 <= v <= 10000):
            raise ValueError('DNS latency must be between 0 and 10000 milliseconds')
        elif metric == 'health_score' and not (0 <= v <= 100):
            raise ValueError('Health score must be between 0 and 100')
        return v


class AlertBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: List[AlertCondition] = Field(..., min_items=1, max_items=5)
    duration_minutes: int = Field(5, ge=1, le=1440)  # 1 minute to 24 hours
    is_active: bool = True

    @validator('conditions')
    def validate_conditions(cls, v):
        if not v:
            raise ValueError('At least one condition is required')
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Alert name cannot be empty')
        return v.strip()


class AlertCreate(AlertBase):
    device_id: str


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[List[AlertCondition]] = Field(None, min_items=1, max_items=5)
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_active: Optional[bool] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Alert name cannot be empty')
        return v.strip() if v else v


class AlertResponse(AlertBase):
    id: str
    device_id: str
    last_triggered: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime
    is_triggered: bool
    conditions_summary: str

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    skip: int
    limit: int


class AlertTrigger(BaseModel):
    alert_id: str
    device_id: str
    triggered_at: datetime
    conditions_met: List[AlertCondition]
    heartbeat_data: Dict[str, Any]


class AlertStats(BaseModel):
    total_alerts: int
    active_alerts: int
    triggered_alerts: int
    alerts_by_device: Dict[str, int]
    most_triggered_alerts: List[Dict[str, Any]]
