from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    serial_number = Column(String(12), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="devices")
    heartbeats = relationship("Heartbeat", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, serial_number={self.serial_number})>"

    @property
    def is_online(self) -> bool:
        """Check if device is online based on last seen timestamp"""
        if not self.last_seen:
            return False
        
        from datetime import datetime, timedelta
        return self.last_seen > datetime.utcnow() - timedelta(minutes=5)

    @property
    def current_health_score(self) -> float:
        """Get the most recent health score from heartbeats"""
        if not self.heartbeats:
            return 0.0
        
        latest_heartbeat = max(self.heartbeats, key=lambda h: h.timestamp)
        return latest_heartbeat.health_score

    @property
    def status(self) -> str:
        """Get device status based on connectivity and health"""
        if not self.is_online:
            return "offline"
        
        health_score = self.current_health_score
        if health_score >= 80:
            return "healthy"
        elif health_score >= 60:
            return "warning"
        else:
            return "critical"
