from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse
from app.api.deps import get_current_user
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter()

@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    skip: int = Query(0, ge=0, description="Number of devices to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of devices to return"),
    search: Optional[str] = Query(None, description="Search term for device name or location"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of devices for current user
    """
    try:
        query = db.query(Device).filter(Device.user_id == current_user.id)
        
        # Apply search filter
        if search:
            query = query.filter(
                Device.name.ilike(f"%{search}%") |
                Device.location.ilike(f"%{search}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        devices = query.offset(skip).limit(limit).all()
        
        logger.info(
            "Devices retrieved",
            user_id=current_user.id,
            count=len(devices),
            total=total
        )
        
        return DeviceListResponse(
            devices=[DeviceResponse.from_orm(device) for device in devices],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error("Failed to retrieve devices", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve devices"
        )

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific device by ID
    """
    try:
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == current_user.id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        logger.info("Device retrieved", device_id=device_id, user_id=current_user.id)
        
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve device", device_id=device_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new device
    """
    try:
        # Check if device with same serial number already exists
        existing_device = db.query(Device).filter(
            Device.serial_number == device_data.serial_number
        ).first()
        
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device with this serial number already exists"
            )
        
        # Create new device
        device = Device(
            name=device_data.name,
            location=device_data.location,
            serial_number=device_data.serial_number,
            description=device_data.description,
            user_id=current_user.id
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        logger.info(
            "Device created successfully",
            device_id=device.id,
            user_id=current_user.id,
            serial_number=device.serial_number
        )
        
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create device", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create device"
        )

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update device information
    """
    try:
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == current_user.id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Update device fields
        update_data = device_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        db.commit()
        db.refresh(device)
        
        logger.info("Device updated successfully", device_id=device_id, user_id=current_user.id)
        
        return DeviceResponse.from_orm(device)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update device", device_id=device_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a device
    """
    try:
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == current_user.id
        ).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        db.delete(device)
        db.commit()
        
        logger.info("Device deleted successfully", device_id=device_id, user_id=current_user.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete device", device_id=device_id, error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device"
        )

@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_devices(
    device_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete multiple devices
    """
    try:
        if not device_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No device IDs provided"
            )
        
        # Get devices belonging to current user
        devices = db.query(Device).filter(
            Device.id.in_(device_ids),
            Device.user_id == current_user.id
        ).all()
        
        if not devices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No devices found"
            )
        
        # Delete devices
        for device in devices:
            db.delete(device)
        
        db.commit()
        
        logger.info(
            "Bulk delete completed",
            user_id=current_user.id,
            deleted_count=len(devices)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Bulk delete failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk delete failed"
        )

