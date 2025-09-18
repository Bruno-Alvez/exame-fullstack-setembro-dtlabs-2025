from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.models.alert import Alert
from app.models.device import Device
from app.models.heartbeat import Heartbeat
from app.services.websocket_manager import websocket_manager

logger = structlog.get_logger()


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    async def evaluate_device_alerts(self, device_id: str, heartbeat_data: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all active alerts for a device based on heartbeat data
        """
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if not device:
                logger.warning("Device not found for alert evaluation", device_id=device_id)
                return []

            active_alerts = self.db.query(Alert).filter(
                Alert.device_id == device_id,
                Alert.is_active == True
            ).all()

            triggered_alerts = []
            
            for alert in active_alerts:
                if alert.evaluate_conditions(heartbeat_data):
                    if not alert.is_triggered:
                        alert.trigger()
                        self.db.commit()
                        triggered_alerts.append(alert)
                        
                        logger.info(
                            "Alert triggered",
                            alert_id=alert.id,
                            device_id=device_id,
                            alert_name=alert.name,
                            conditions=alert.conditions_summary
                        )
                        
                        await self._send_alert_notification(alert, heartbeat_data, device)

            return triggered_alerts

        except Exception as e:
            logger.error("Failed to evaluate device alerts", device_id=device_id, error=str(e))
            return []

    async def _send_alert_notification(self, alert: Alert, heartbeat_data: Dict[str, Any], device: Device):
        """
        Send real-time alert notification via WebSocket
        """
        try:
            from datetime import timezone
            alert_data = {
                "id": str(alert.id),
                "name": alert.name,
                "description": alert.description,
                "device_id": str(alert.device_id),
                "device_name": device.name,
                "conditions": alert.conditions,
                "conditions_summary": alert.conditions_summary,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "heartbeat_data": heartbeat_data,
                "user_id": str(device.user_id)
            }

            await websocket_manager.broadcast_to_user(
                user_id=str(device.user_id),
                message={
                    "type": "alert_triggered",
                    "data": alert_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            logger.info(
                "Alert notification sent",
                alert_id=alert.id,
                user_id=device.user_id,
                device_id=alert.device_id
            )

        except Exception as e:
            logger.error("Failed to send alert notification", alert_id=alert.id, error=str(e))

    def get_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive alert statistics for a user
        """
        try:
            user_devices = self.db.query(Device).filter(Device.user_id == user_id).all()
            user_device_ids = [device.id for device in user_devices]

            if not user_device_ids:
                return {
                    "total_alerts": 0,
                    "active_alerts": 0,
                    "triggered_alerts": 0,
                    "alerts_by_device": {},
                    "most_triggered_alerts": []
                }

            total_alerts = self.db.query(Alert).filter(Alert.device_id.in_(user_device_ids)).count()
            active_alerts = self.db.query(Alert).filter(
                Alert.device_id.in_(user_device_ids),
                Alert.is_active == True
            ).count()

            triggered_alerts = self.db.query(Alert).filter(
                Alert.device_id.in_(user_device_ids),
                Alert.last_triggered.isnot(None)
            ).count()

            alerts_by_device = {}
            for device in user_devices:
                count = self.db.query(Alert).filter(Alert.device_id == device.id).count()
                if count > 0:
                    alerts_by_device[device.name] = count

            most_triggered = self.db.query(Alert).filter(
                Alert.device_id.in_(user_device_ids),
                Alert.trigger_count > 0
            ).order_by(Alert.trigger_count.desc()).limit(5).all()

            most_triggered_alerts = []
            for alert in most_triggered:
                device = next((d for d in user_devices if d.id == alert.device_id), None)
                most_triggered_alerts.append({
                    "id": str(alert.id),
                    "name": alert.name,
                    "device_name": device.name if device else "Unknown",
                    "trigger_count": alert.trigger_count,
                    "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
                })

            return {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "triggered_alerts": triggered_alerts,
                "alerts_by_device": alerts_by_device,
                "most_triggered_alerts": most_triggered_alerts
            }

        except Exception as e:
            logger.error("Failed to get alert statistics", user_id=user_id, error=str(e))
            return {
                "total_alerts": 0,
                "active_alerts": 0,
                "triggered_alerts": 0,
                "alerts_by_device": {},
                "most_triggered_alerts": []
            }

    def reset_alert_triggers(self, alert_id: str, user_id: str) -> bool:
        """
        Reset alert trigger state for a specific alert
        """
        try:
            user_devices = self.db.query(Device).filter(Device.user_id == user_id).all()
            user_device_ids = [device.id for device in user_devices]

            alert = self.db.query(Alert).filter(
                Alert.id == alert_id,
                Alert.device_id.in_(user_device_ids)
            ).first()

            if not alert:
                return False

            alert.reset()
            self.db.commit()

            logger.info("Alert triggers reset", alert_id=alert_id, user_id=user_id)
            return True

        except Exception as e:
            logger.error("Failed to reset alert triggers", alert_id=alert_id, error=str(e))
            self.db.rollback()
            return False

    def get_device_alerts_summary(self, device_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get alert summary for a specific device
        """
        try:
            device = self.db.query(Device).filter(
                Device.id == device_id,
                Device.user_id == user_id
            ).first()

            if not device:
                return {}

            alerts = self.db.query(Alert).filter(Alert.device_id == device_id).all()

            active_count = sum(1 for alert in alerts if alert.is_active)
            triggered_count = sum(1 for alert in alerts if alert.is_triggered)
            total_triggers = sum(alert.trigger_count for alert in alerts)

            from datetime import timezone
            recent_triggers = []
            now = datetime.now(timezone.utc)
            for alert in alerts:
                if alert.last_triggered:
                    # Handle timezone-aware comparison
                    last_triggered = alert.last_triggered
                    if last_triggered.tzinfo is None:
                        last_triggered = last_triggered.replace(tzinfo=timezone.utc)
                    
                    if last_triggered > now - timedelta(hours=24):
                        recent_triggers.append({
                            "alert_name": alert.name,
                            "triggered_at": alert.last_triggered.isoformat(),
                            "conditions": alert.conditions_summary
                        })

            return {
                "device_id": device_id,
                "device_name": device.name,
                "total_alerts": len(alerts),
                "active_alerts": active_count,
                "triggered_alerts": triggered_count,
                "total_triggers": total_triggers,
                "recent_triggers": recent_triggers
            }

        except Exception as e:
            logger.error("Failed to get device alerts summary", device_id=device_id, error=str(e))
            return {}
