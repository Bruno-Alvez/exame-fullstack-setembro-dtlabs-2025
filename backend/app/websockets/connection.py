from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import structlog
import asyncio

from app.services.websocket_manager import websocket_manager
from app.api.deps import get_current_user
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    device_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time communication
    """
    await websocket_manager.connect(websocket, device_id=device_id, user_id=user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Handle different message types
            try:
                import json
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Handle subscription to specific devices or users
                    target_device = message.get("device_id")
                    target_user = message.get("user_id")
                    
                    if target_device:
                        await websocket_manager.connect(websocket, device_id=target_device)
                    if target_user:
                        await websocket_manager.connect(websocket, user_id=target_user)
                        
                elif message_type == "unsubscribe":
                    # Handle unsubscription
                    target_device = message.get("device_id")
                    target_user = message.get("user_id")
                    
                    if target_device:
                        websocket_manager.disconnect(websocket, device_id=target_device)
                    if target_user:
                        websocket_manager.disconnect(websocket, user_id=target_user)
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received via WebSocket")
            except Exception as e:
                logger.error("Error processing WebSocket message", error=str(e))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, device_id=device_id, user_id=user_id)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket connection error", error=str(e))
        websocket_manager.disconnect(websocket, device_id=device_id, user_id=user_id)


@router.websocket("/ws/device/{device_id}")
async def device_websocket_endpoint(
    websocket: WebSocket,
    device_id: str
):
    """
    WebSocket endpoint for device-specific real-time updates
    """
    await websocket_manager.connect(websocket, device_id=device_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            try:
                import json
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "device_id": device_id,
                            "timestamp": message.get("timestamp")
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received via device WebSocket", device_id=device_id)
            except Exception as e:
                logger.error("Error processing device WebSocket message", device_id=device_id, error=str(e))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, device_id=device_id)
        logger.info("Device WebSocket disconnected", device_id=device_id)
    except Exception as e:
        logger.error("Device WebSocket connection error", device_id=device_id, error=str(e))
        websocket_manager.disconnect(websocket, device_id=device_id)


@router.websocket("/ws/user")
async def user_websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for user-specific real-time updates
    Requires authentication
    """
    await websocket_manager.connect(websocket, user_id=str(current_user.id))
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            try:
                import json
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "user_id": str(current_user.id),
                            "timestamp": message.get("timestamp")
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received via user WebSocket", user_id=current_user.id)
            except Exception as e:
                logger.error("Error processing user WebSocket message", user_id=current_user.id, error=str(e))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id=str(current_user.id))
        logger.info("User WebSocket disconnected", user_id=current_user.id)
    except Exception as e:
        logger.error("User WebSocket connection error", user_id=current_user.id, error=str(e))
        websocket_manager.disconnect(websocket, user_id=str(current_user.id))


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    """
    return websocket_manager.get_connection_stats()
