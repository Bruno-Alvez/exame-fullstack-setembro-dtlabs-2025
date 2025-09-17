from sqlalchemy import Column, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Device metrics
    cpu_usage = Column(Float, nullable=False)
    ram_usage = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    free_disk_space = Column(Float, nullable=False)
    dns_latency = Column(Float, nullable=False)
    connectivity = Column(Boolean, nullable=False)
    boot_timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Calculated metrics
    health_score = Column(Float, nullable=False, index=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    device = relationship("Device", back_populates="heartbeats")

    # Indexes for better query performance
    __table_args__ = (
        Index('ix_heartbeats_device_timestamp', 'device_id', 'timestamp'),
        Index('ix_heartbeats_health_score', 'health_score'),
        Index('ix_heartbeats_timestamp_desc', 'timestamp', postgresql_using='btree'),
    )

    def __repr__(self):
        return f"<Heartbeat(id={self.id}, device_id={self.device_id}, health_score={self.health_score})>"

    @property
    def is_healthy(self) -> bool:
        """Check if heartbeat indicates healthy device"""
        return self.health_score >= 70

    @property
    def is_critical(self) -> bool:
        """Check if heartbeat indicates critical device state"""
        return self.health_score < 40

    @property
    def metrics_summary(self) -> dict:
        """Get a summary of all metrics"""
        return {
            "cpu_usage": self.cpu_usage,
            "ram_usage": self.ram_usage,
            "temperature": self.temperature,
            "free_disk_space": self.free_disk_space,
            "dns_latency": self.dns_latency,
            "connectivity": self.connectivity,
            "health_score": self.health_score
        }

    def calculate_health_score(self) -> float:
        """Calculate health score based on metrics"""
        from app.services.health_scoring import calculate_health_score
        
        return calculate_health_score(
            cpu_usage=self.cpu_usage,
            ram_usage=self.ram_usage,
            temperature=self.temperature,
            free_disk_space=self.free_disk_space,
            connectivity=self.connectivity
        )
