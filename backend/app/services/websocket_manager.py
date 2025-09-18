from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
import structlog
from datetime import datetime

logger = structlog.get_logger()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, device_id: str = None, user_id: str = None):
        """Accept WebSocket connection and add to appropriate groups"""
        await websocket.accept()
        
        if device_id:
            if device_id not in self.active_connections:
                self.active_connections[device_id] = []
            self.active_connections[device_id].append(websocket)
            logger.info("WebSocket connected for device", device_id=device_id)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
            logger.info("WebSocket connected for user", user_id=user_id)

    def disconnect(self, websocket: WebSocket, device_id: str = None, user_id: str = None):
        """Remove WebSocket connection from groups"""
        if device_id and device_id in self.active_connections:
            if websocket in self.active_connections[device_id]:
                self.active_connections[device_id].remove(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
            logger.info("WebSocket disconnected for device", device_id=device_id)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
            logger.info("WebSocket disconnected for user", user_id=user_id)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))

    async def broadcast_to_device(self, device_id: str, message: dict):
        """Broadcast message to all connections for a specific device"""
        if device_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections[device_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error("Failed to send message to device connection", device_id=device_id, error=str(e))
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections[device_id].remove(connection)

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to all connections for a specific user"""
        if user_id not in self.user_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error("Failed to send message to user connection", user_id=user_id, error=str(e))
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.user_connections[user_id].remove(connection)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all active connections"""
        message_str = json.dumps(message)
        all_connections = set()
        
        # Collect all unique connections
        for connections in self.active_connections.values():
            all_connections.update(connections)
        for connections in self.user_connections.values():
            all_connections.update(connections)
        
        disconnected = []
        
        for connection in all_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error("Failed to broadcast message", error=str(e))
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self._cleanup_connection(connection)

    def _cleanup_connection(self, websocket: WebSocket):
        """Remove connection from all groups"""
        for device_id, connections in list(self.active_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.active_connections[device_id]
        
        for user_id, connections in list(self.user_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.user_connections[user_id]

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        device_connections = sum(len(connections) for connections in self.active_connections.values())
        user_connections = sum(len(connections) for connections in self.user_connections.values())
        
        return {
            "total_device_connections": device_connections,
            "total_user_connections": user_connections,
            "unique_devices": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def broadcast_device_update(self, device_id: str, heartbeat_data: dict):
        """Broadcast device heartbeat update to all connected clients"""
        message = {
            "type": "device_update",
            "device_id": device_id,
            "data": heartbeat_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_device(device_id, message)
        logger.info("Device update broadcasted", device_id=device_id)


# Global WebSocket manager instance
websocket_manager = ConnectionManager()


async def broadcast_device_update(device_id: str, heartbeat_data: dict):
    """Broadcast device heartbeat update to all connected clients"""
    message = {
        "type": "device_update",
        "device_id": device_id,
        "data": heartbeat_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.broadcast_to_device(device_id, message)
    logger.info("Device update broadcasted", device_id=device_id)


async def broadcast_alert_triggered(alert_data: dict):
    """Broadcast alert trigger to relevant users"""
    message = {
        "type": "alert_triggered",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Broadcast to user who owns the device
    user_id = alert_data.get("user_id")
    if user_id:
        await websocket_manager.broadcast_to_user(user_id, message)
        logger.info("Alert trigger broadcasted", user_id=user_id, alert_id=alert_data.get("id"))


async def broadcast_system_status(status_data: dict):
    """Broadcast system status to all connected clients"""
    message = {
        "type": "system_status",
        "data": status_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await websocket_manager.broadcast_to_all(message)
    logger.info("System status broadcasted")
