from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.alert import Alert
from app.models.device import Device
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse, AlertStats
from app.api.deps import get_current_user
from app.models.user import User
from app.services.alert_service import AlertService

logger = structlog.get_logger()

router = APIRouter()

@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of alerts to return"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of alerts for current user
    """
    try:
        # Get user's devices
        user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
        user_device_ids = [device.id for device in user_devices]
        
        if not user_device_ids:
            return AlertListResponse(
                alerts=[],
                total=0,
                skip=skip,
                limit=limit
            )
        
        # Build query
        query = db.query(Alert).filter(Alert.device_id.in_(user_device_ids))
        
        # Apply filters
        if device_id:
            if device_id not in user_device_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this device"
                )
            query = query.filter(Alert.device_id == device_id)
        
        if is_active is not None:
            query = query.filter(Alert.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        alerts = query.offset(skip).limit(limit).all()
        
        logger.info(
            "Alerts retrieved",
            user_id=current_user.id,
            count=len(alerts),
            total=total
        )
        
        alert_responses = []
        for alert in alerts:
            alert_responses.append(AlertResponse(
                id=str(alert.id),
                name=alert.name,
                description=alert.description,
                device_id=str(alert.device_id),
                conditions=alert.conditions,
                duration_minutes=alert.duration_minutes,
                is_active=alert.is_active,
                last_triggered=alert.last_triggered,
                trigger_count=alert.trigger_count,
                created_at=alert.created_at,
                updated_at=alert.updated_at,
                is_triggered=alert.is_triggered,
                conditions_summary=alert.conditions_summary
            ))
        
        return AlertListResponse(
            alerts=alert_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve alerts", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific alert by ID
    """
    try:
        # Get user's devices
        user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
        user_device_ids = [device.id for device in user_devices]
        
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.device_id.in_(user_device_ids)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        logger.info("Alert retrieved", alert_id=alert_id, user_id=current_user.id)
        
        return AlertResponse(
            id=str(alert.id),
            name=alert.name,
            description=alert.description,
            device_id=str(alert.device_id),
            conditions=alert.conditions,
            duration_minutes=alert.duration_minutes,
            is_active=alert.is_active,
            last_triggered=alert.last_triggered,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            is_triggered=alert.is_triggered,
            conditions_summary=alert.conditions_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve alert", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert"
        )

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new alert
    """
    try:
        # Verify device belongs to user
        device = db.query(Device).filter(
            Device.id == alert_data.device_id,
            Device.user_id == current_user.id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Convert conditions to dict for JSON storage
        conditions_dict = [condition.dict() for condition in alert_data.conditions]
        
        # Create new alert
        alert = Alert(
            name=alert_data.name,
            description=alert_data.description,
            device_id=alert_data.device_id,
            conditions=conditions_dict,
            duration_minutes=alert_data.duration_minutes,
            is_active=alert_data.is_active
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(
            "Alert created successfully",
            alert_id=alert.id,
            user_id=current_user.id,
            device_id=alert_data.device_id
        )
        
        return AlertResponse(
            id=str(alert.id),
            name=alert.name,
            description=alert.description,
            device_id=str(alert.device_id),
            conditions=alert.conditions,
            duration_minutes=alert.duration_minutes,
            is_active=alert.is_active,
            last_triggered=alert.last_triggered,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            is_triggered=alert.is_triggered,
            conditions_summary=alert.conditions_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create alert", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update alert information
    """
    try:
        # Get user's devices
        user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
        user_device_ids = [device.id for device in user_devices]
        
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.device_id.in_(user_device_ids)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update alert fields
        update_data = alert_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        db.commit()
        db.refresh(alert)
        
        logger.info("Alert updated successfully", alert_id=alert_id, user_id=current_user.id)
        
        return AlertResponse(
            id=str(alert.id),
            name=alert.name,
            description=alert.description,
            device_id=str(alert.device_id),
            conditions=alert.conditions,
            duration_minutes=alert.duration_minutes,
            is_active=alert.is_active,
            last_triggered=alert.last_triggered,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            is_triggered=alert.is_triggered,
            conditions_summary=alert.conditions_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update alert", alert_id=alert_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an alert
    """
    try:
        # Get user's devices
        user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
        user_device_ids = [device.id for device in user_devices]
        
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.device_id.in_(user_device_ids)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        db.delete(alert)
        db.commit()
        
        logger.info("Alert deleted successfully", alert_id=alert_id, user_id=current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete alert", alert_id=alert_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )

@router.post("/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle alert active status
    """
    try:
        # Get user's devices
        user_devices = db.query(Device).filter(Device.user_id == current_user.id).all()
        user_device_ids = [device.id for device in user_devices]
        
        alert = db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.device_id.in_(user_device_ids)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Toggle active status
        alert.is_active = not alert.is_active
        db.commit()
        db.refresh(alert)
        
        logger.info(
            "Alert toggled successfully",
            alert_id=alert_id,
            user_id=current_user.id,
            is_active=alert.is_active
        )
        
        return AlertResponse(
            id=str(alert.id),
            name=alert.name,
            description=alert.description,
            device_id=str(alert.device_id),
            conditions=alert.conditions,
            duration_minutes=alert.duration_minutes,
            is_active=alert.is_active,
            last_triggered=alert.last_triggered,
            trigger_count=alert.trigger_count,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            is_triggered=alert.is_triggered,
            conditions_summary=alert.conditions_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to toggle alert", alert_id=alert_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle alert"
        )

@router.get("/stats/summary", response_model=AlertStats)
async def get_alert_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive alert statistics for current user
    """
    try:
        alert_service = AlertService(db)
        stats = alert_service.get_alert_statistics(str(current_user.id))
        
        return AlertStats(**stats)
        
    except Exception as e:
        logger.error("Failed to get alert statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert statistics"
        )

@router.get("/device/{device_id}/summary")
async def get_device_alerts_summary(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get alert summary for a specific device
    """
    try:
        alert_service = AlertService(db)
        summary = alert_service.get_device_alerts_summary(device_id, str(current_user.id))
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found or access denied"
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get device alerts summary", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device alerts summary"
        )

@router.post("/{alert_id}/reset")
async def reset_alert_triggers(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset alert trigger state
    """
    try:
        alert_service = AlertService(db)
        success = alert_service.reset_alert_triggers(alert_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or access denied"
            )
        
        logger.info("Alert triggers reset", alert_id=alert_id, user_id=current_user.id)
        
        return {"message": "Alert triggers reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reset alert triggers", alert_id=alert_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset alert triggers"
        )

