from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert configuration
    conditions = Column(JSON, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Alert state
    last_triggered = Column(DateTime(timezone=True), nullable=True, index=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, name={self.name}, device_id={self.device_id}, is_active={self.is_active})>"

    @property
    def is_triggered(self) -> bool:
        """Check if alert is currently triggered"""
        if not self.last_triggered:
            return False
        
        from datetime import datetime, timedelta
        return self.last_triggered > datetime.utcnow() - timedelta(minutes=self.duration_minutes)

    @property
    def conditions_summary(self) -> str:
        """Get a human-readable summary of alert conditions"""
        if not self.conditions:
            return "No conditions defined"
        
        conditions = []
        for condition in self.conditions:
            metric = condition.get('metric', 'unknown')
            operator = condition.get('operator', 'unknown')
            value = condition.get('value', 'unknown')
            conditions.append(f"{metric} {operator} {value}")
        
        return " AND ".join(conditions)

    def evaluate_conditions(self, heartbeat_data: dict) -> bool:
        """Evaluate if alert conditions are met based on heartbeat data"""
        if not self.conditions or not self.is_active:
            return False
        
        for condition in self.conditions:
            metric = condition.get('metric')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if metric not in heartbeat_data:
                continue
            
            current_value = heartbeat_data[metric]
            
            if operator == '>':
                if not (current_value > value):
                    return False
            elif operator == '>=':
                if not (current_value >= value):
                    return False
            elif operator == '<':
                if not (current_value < value):
                    return False
            elif operator == '<=':
                if not (current_value <= value):
                    return False
            elif operator == '==':
                if not (current_value == value):
                    return False
            elif operator == '!=':
                if not (current_value != value):
                    return False
        
        return True

    def trigger(self):
        """Mark alert as triggered"""
        from datetime import datetime
        self.last_triggered = datetime.utcnow()
        self.trigger_count += 1

    def reset(self):
        """Reset alert trigger state"""
        self.last_triggered = None
