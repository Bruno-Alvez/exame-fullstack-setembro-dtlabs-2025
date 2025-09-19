import { WebSocketMessage } from '@/types';
import { useAlertStore } from '@/store/alertStore';
import { useDeviceStore } from '@/store/deviceStore';
import toast from 'react-hot-toast';

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private isConnecting = false;
  private messageHandlers: Map<string, (data: any) => void> = new Map();

  constructor() {
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.sendMessage = this.sendMessage.bind(this);
  }

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;

      try {
        const wsUrl = `${(import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000'}/ws/user`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.setupMessageHandlers();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.ws = null;

          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(token);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  private scheduleReconnect(token: string) {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(token).catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private setupMessageHandlers() {
    this.messageHandlers.set('alert_triggered', (data) => {
      const alertStore = useAlertStore.getState();
      alertStore.addActiveAlert(data);
      
      toast.error(`Alert: ${data.name} - Device: ${data.device_name}`, {
        duration: 6000,
      });
    });

    this.messageHandlers.set('device_status', (data) => {
      const deviceStore = useDeviceStore.getState();
      deviceStore.updateDevice(data.device_id, {
        is_online: data.is_online,
        status: data.status,
        current_health_score: data.health_score,
        last_seen: data.last_seen,
      });
    });

    this.messageHandlers.set('heartbeat', (data) => {
      const deviceStore = useDeviceStore.getState();
      deviceStore.updateDevice(data.device_id, {
        current_health_score: data.health_score,
        last_seen: data.timestamp,
        status: data.health_score >= 80 ? 'healthy' : 
                data.health_score >= 60 ? 'warning' : 'critical',
      });
    });

    this.messageHandlers.set('pong', (data) => {
      console.log('Pong received:', data.timestamp);
    });
  }

  private handleMessage(message: WebSocketMessage) {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message.data);
    } else {
      console.log('Unhandled message type:', message.type, message.data);
    }
  }

  sendMessage(type: string, data?: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = {
        type,
        timestamp: new Date().toISOString(),
        data,
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  ping() {
    this.sendMessage('ping', { timestamp: new Date().toISOString() });
  }

  subscribeToDevice(deviceId: string) {
    this.sendMessage('subscribe', { device_id: deviceId });
  }

  subscribeToUser(userId: string) {
    this.sendMessage('subscribe', { user_id: userId });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.reconnectAttempts = 0;
  }

  getConnectionState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  addMessageHandler(type: string, handler: (data: any) => void) {
    this.messageHandlers.set(type, handler);
  }

  removeMessageHandler(type: string) {
    this.messageHandlers.delete(type);
  }
}

export const websocketService = new WebSocketService();
