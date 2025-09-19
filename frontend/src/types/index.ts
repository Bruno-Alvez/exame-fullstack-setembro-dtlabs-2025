export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  name: string;
  location: string;
  serial_number: string;
  description?: string;
  user_id: string;
  last_seen?: string;
  created_at: string;
  updated_at: string;
  is_online: boolean;
  current_health_score: number;
  status: 'healthy' | 'warning' | 'critical' | 'offline';
}

export interface Heartbeat {
  id: string;
  device_id: string;
  cpu_usage: number;
  ram_usage: number;
  temperature: number;
  free_disk_space: number;
  dns_latency: number;
  connectivity: boolean;
  boot_timestamp: string;
  health_score: number;
  timestamp: string;
  is_healthy: boolean;
  is_critical: boolean;
  metrics_summary: {
    cpu_usage: number;
    ram_usage: number;
    temperature: number;
    free_disk_space: number;
    dns_latency: number;
    connectivity: boolean;
    health_score: number;
  };
}

export interface Alert {
  id: string;
  name: string;
  description?: string;
  device_id: string;
  conditions: AlertCondition[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  device?: Device;
  conditions_summary: string;
  last_triggered?: string;
  trigger_count: number;
}

export interface AlertCondition {
  metric: 'cpu_usage' | 'ram_usage' | 'temperature' | 'free_disk_space' | 'dns_latency' | 'connectivity' | 'health_score';
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  value: number | boolean;
  duration?: number;
}

export interface DeviceCreate {
  name: string;
  location: string;
  serial_number: string;
  description?: string;
}

export interface DeviceUpdate {
  name?: string;
  location?: string;
  description?: string;
}

export interface AlertCreate {
  name: string;
  description?: string;
  device_id: string;
  conditions: AlertCondition[];
}

export interface AlertUpdate {
  name?: string;
  description?: string;
  conditions?: AlertCondition[];
  is_active?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface DeviceListResponse extends PaginatedResponse<Device> {}
export interface HeartbeatListResponse extends PaginatedResponse<Heartbeat> {}
export interface AlertListResponse extends PaginatedResponse<Alert> {}

export interface WebSocketMessage {
  type: 'alert_triggered' | 'device_status' | 'heartbeat' | 'ping' | 'pong';
  timestamp: string;
  data?: any;
}

export interface HealthScoreStats {
  average: number;
  min: number;
  max: number;
  trend: 'up' | 'down' | 'stable';
  count: number;
}

export interface DeviceStats {
  total_devices: number;
  online_devices: number;
  offline_devices: number;
  healthy_devices: number;
  warning_devices: number;
  critical_devices: number;
  average_health_score: number;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface TimeRange {
  start: Date;
  end: Date;
  label: string;
}

export interface FilterOptions {
  search?: string;
  status?: string;
  location?: string;
  timeRange?: TimeRange;
}
