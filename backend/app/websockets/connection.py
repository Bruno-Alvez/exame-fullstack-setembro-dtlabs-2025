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
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for user-specific real-time updates
    Requires authentication via query parameter
    """
    # Authenticate user from token
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    try:
        from app.core.security import verify_token
        from app.models.user import User
        from app.core.database import SessionLocal
        
        logger.info("WebSocket authentication attempt", token_length=len(token) if token else 0)
        
        # Verify token and get user
        payload = verify_token(token)
        if not payload:
            logger.warning("WebSocket authentication failed: Invalid token")
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("WebSocket authentication failed: No user ID in token")
            await websocket.close(code=1008, reason="Invalid token payload")
            return
        
        logger.info("WebSocket token verified", user_id=user_id)
        
        # Get user from database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                logger.warning("WebSocket authentication failed: User not found or inactive", user_id=user_id)
                await websocket.close(code=1008, reason="User not found or inactive")
                return
        finally:
            db.close()
        
        logger.info("WebSocket authentication successful", user_id=user_id)
        await websocket_manager.connect(websocket, user_id=str(user.id))
        
    except Exception as e:
        logger.error("WebSocket authentication error", error=str(e))
        await websocket.close(code=1011, reason="Authentication failed")
        return
    
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
                            "user_id": str(user.id),
                            "timestamp": message.get("timestamp")
                        }),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received via user WebSocket", user_id=user.id)
            except Exception as e:
                logger.error("Error processing user WebSocket message", user_id=user.id, error=str(e))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id=str(user.id))
        logger.info("User WebSocket disconnected", user_id=user.id)
    except Exception as e:
        logger.error("User WebSocket connection error", user_id=user.id, error=str(e))
        websocket_manager.disconnect(websocket, user_id=str(user.id))


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics
    """
    return websocket_manager.get_connection_stats()
