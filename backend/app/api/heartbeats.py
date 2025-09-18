from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.heartbeat import Heartbeat
from app.models.device import Device
from app.schemas.heartbeat import HeartbeatCreate, HeartbeatResponse, HeartbeatListResponse
from app.services.health_scoring import calculate_health_score
from app.services.websocket_manager import websocket_manager

logger = structlog.get_logger()

router = APIRouter()

@router.post("/{device_id}", response_model=HeartbeatResponse, status_code=status.HTTP_201_CREATED)
async def create_heartbeat(
    device_id: str,
    heartbeat_data: HeartbeatCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new heartbeat for a device
    """
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Calculate health score
        health_score = calculate_health_score(
            cpu_usage=heartbeat_data.cpu_usage,
            ram_usage=heartbeat_data.ram_usage,
            temperature=heartbeat_data.temperature,
            free_disk_space=heartbeat_data.free_disk_space,
            connectivity=heartbeat_data.connectivity
        )
        
        # Create heartbeat
        heartbeat = Heartbeat(
            device_id=device_id,
            cpu_usage=heartbeat_data.cpu_usage,
            ram_usage=heartbeat_data.ram_usage,
            temperature=heartbeat_data.temperature,
            free_disk_space=heartbeat_data.free_disk_space,
            dns_latency=heartbeat_data.dns_latency,
            connectivity=heartbeat_data.connectivity,
            boot_timestamp=heartbeat_data.boot_timestamp,
            health_score=health_score
        )
        
        db.add(heartbeat)
        db.commit()
        db.refresh(heartbeat)
        
        # Update device last seen
        device.last_seen = datetime.utcnow()
        db.commit()
        
        # Create response data
        heartbeat_response = HeartbeatResponse(
            id=str(heartbeat.id),
            device_id=str(heartbeat.device_id),
            cpu_usage=heartbeat.cpu_usage,
            ram_usage=heartbeat.ram_usage,
            temperature=heartbeat.temperature,
            free_disk_space=heartbeat.free_disk_space,
            dns_latency=heartbeat.dns_latency,
            connectivity=heartbeat.connectivity,
            boot_timestamp=heartbeat.boot_timestamp,
            health_score=heartbeat.health_score,
            timestamp=heartbeat.timestamp,
            is_healthy=health_score >= 80,
            is_critical=health_score < 60,
            metrics_summary={
                "cpu_status": "high" if heartbeat.cpu_usage > 80 else "normal",
                "ram_status": "high" if heartbeat.ram_usage > 80 else "normal",
                "temp_status": "high" if heartbeat.temperature > 60 else "normal",
                "disk_status": "low" if heartbeat.free_disk_space < 20 else "normal"
            }
        )
        
        # Send real-time update via WebSocket
        await websocket_manager.broadcast_device_update(
            device_id=device_id,
            heartbeat_data=heartbeat_response.model_dump()
        )
        
        logger.info(
            "Heartbeat created successfully",
            device_id=device_id,
            health_score=health_score
        )
        
        return heartbeat_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create heartbeat", device_id=device_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create heartbeat"
        )

@router.get("/{device_id}", response_model=HeartbeatListResponse)
async def get_device_heartbeats(
    device_id: str,
    limit: int = 100,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get heartbeats for a specific device
    """
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get heartbeats
        heartbeats = db.query(Heartbeat).filter(
            Heartbeat.device_id == device_id,
            Heartbeat.timestamp >= start_time,
            Heartbeat.timestamp <= end_time
        ).order_by(Heartbeat.timestamp.desc()).limit(limit).all()
        
        logger.info(
            "Heartbeats retrieved",
            device_id=device_id,
            count=len(heartbeats),
            hours=hours
        )
        
        heartbeat_responses = []
        for hb in heartbeats:
            heartbeat_responses.append(HeartbeatResponse(
                id=str(hb.id),
                device_id=str(hb.device_id),
                cpu_usage=hb.cpu_usage,
                ram_usage=hb.ram_usage,
                temperature=hb.temperature,
                free_disk_space=hb.free_disk_space,
                dns_latency=hb.dns_latency,
                connectivity=hb.connectivity,
                boot_timestamp=hb.boot_timestamp,
                health_score=hb.health_score,
                timestamp=hb.timestamp,
                is_healthy=hb.health_score >= 80,
                is_critical=hb.health_score < 60,
                metrics_summary={
                    "cpu_status": "high" if hb.cpu_usage > 80 else "normal",
                    "ram_status": "high" if hb.ram_usage > 80 else "normal",
                    "temp_status": "high" if hb.temperature > 60 else "normal",
                    "disk_status": "low" if hb.free_disk_space < 20 else "normal"
                }
            ))
        
        return HeartbeatListResponse(
            heartbeats=heartbeat_responses,
            device_id=device_id,
            total=len(heartbeats),
            hours=hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve heartbeats", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve heartbeats"
        )

@router.get("/{device_id}/latest", response_model=HeartbeatResponse)
async def get_latest_heartbeat(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the latest heartbeat for a device
    """
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Get latest heartbeat
        heartbeat = db.query(Heartbeat).filter(
            Heartbeat.device_id == device_id
        ).order_by(Heartbeat.timestamp.desc()).first()
        
        if not heartbeat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No heartbeats found for this device"
            )
        
        logger.info("Latest heartbeat retrieved", device_id=device_id)
        
        return HeartbeatResponse(
            id=str(heartbeat.id),
            device_id=str(heartbeat.device_id),
            cpu_usage=heartbeat.cpu_usage,
            ram_usage=heartbeat.ram_usage,
            temperature=heartbeat.temperature,
            free_disk_space=heartbeat.free_disk_space,
            dns_latency=heartbeat.dns_latency,
            connectivity=heartbeat.connectivity,
            boot_timestamp=heartbeat.boot_timestamp,
            health_score=heartbeat.health_score,
            timestamp=heartbeat.timestamp,
            is_healthy=heartbeat.health_score >= 80,
            is_critical=heartbeat.health_score < 60,
            metrics_summary={
                "cpu_status": "high" if heartbeat.cpu_usage > 80 else "normal",
                "ram_status": "high" if heartbeat.ram_usage > 80 else "normal",
                "temp_status": "high" if heartbeat.temperature > 60 else "normal",
                "disk_status": "low" if heartbeat.free_disk_space < 20 else "normal"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve latest heartbeat", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve latest heartbeat"
        )

@router.get("/{device_id}/health-score", response_model=dict)
async def get_device_health_score(
    device_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get health score statistics for a device
    """
    try:
        # Verify device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get heartbeats in time range
        heartbeats = db.query(Heartbeat).filter(
            Heartbeat.device_id == device_id,
            Heartbeat.timestamp >= start_time,
            Heartbeat.timestamp <= end_time
        ).all()
        
        if not heartbeats:
            return {
                "device_id": device_id,
                "current_health_score": None,
                "average_health_score": None,
                "min_health_score": None,
                "max_health_score": None,
                "total_heartbeats": 0,
                "hours": hours
            }
        
        # Calculate statistics
        health_scores = [hb.health_score for hb in heartbeats]
        current_health_score = health_scores[0] if health_scores else None
        average_health_score = sum(health_scores) / len(health_scores)
        min_health_score = min(health_scores)
        max_health_score = max(health_scores)
        
        logger.info(
            "Health score statistics retrieved",
            device_id=device_id,
            current_score=current_health_score,
            average_score=average_health_score
        )
        
        return {
            "device_id": device_id,
            "current_health_score": current_health_score,
            "average_health_score": round(average_health_score, 2),
            "min_health_score": min_health_score,
            "max_health_score": max_health_score,
            "total_heartbeats": len(heartbeats),
            "hours": hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve health score", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health score"
        )

