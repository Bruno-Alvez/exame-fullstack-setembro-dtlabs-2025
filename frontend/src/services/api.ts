import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  User,
  Device,
  DeviceCreate,
  DeviceUpdate,
  DeviceListResponse,
  Heartbeat,
  HeartbeatListResponse,
  Alert,
  AlertCreate,
  AlertUpdate,
  AlertListResponse,
  DeviceStats,
  HealthScoreStats,
} from '@/types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors and token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              useAuthStore.getState().setAuth(response.data);
              
              // Retry original request with new token
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            useAuthStore.getState().logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        // Handle other errors
        if (error.response?.data?.detail) {
          toast.error(error.response.data.detail);
        } else if (error.message) {
          toast.error(error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AxiosResponse<AuthResponse>> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    return this.api.post('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  }

  async register(userData: RegisterRequest): Promise<AxiosResponse<AuthResponse>> {
    return this.api.post('/api/v1/auth/register', userData);
  }

  async getCurrentUser(): Promise<AxiosResponse<User>> {
    return this.api.get('/api/v1/auth/me');
  }

  async refreshToken(refreshToken: string): Promise<AxiosResponse<AuthResponse>> {
    return this.api.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  // Device endpoints
  async getDevices(params?: {
    skip?: number;
    limit?: number;
    search?: string;
  }): Promise<AxiosResponse<DeviceListResponse>> {
    return this.api.get('/api/v1/devices/', { params });
  }

  async getDevice(id: string): Promise<AxiosResponse<Device>> {
    return this.api.get(`/api/v1/devices/${id}`);
  }

  async createDevice(deviceData: DeviceCreate): Promise<AxiosResponse<Device>> {
    return this.api.post('/api/v1/devices/', deviceData);
  }

  async updateDevice(id: string, deviceData: DeviceUpdate): Promise<AxiosResponse<Device>> {
    return this.api.put(`/api/v1/devices/${id}`, deviceData);
  }

  async deleteDevice(id: string): Promise<AxiosResponse<void>> {
    return this.api.delete(`/api/v1/devices/${id}`);
  }

  async getDeviceStats(): Promise<AxiosResponse<DeviceStats>> {
    return this.api.get('/api/v1/devices/stats');
  }

  // Heartbeat endpoints
  async getHeartbeats(
    deviceId: string,
    params?: {
      skip?: number;
      limit?: number;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<AxiosResponse<HeartbeatListResponse>> {
    return this.api.get(`/api/v1/heartbeats/${deviceId}`, { params });
  }

  async getLatestHeartbeat(deviceId: string): Promise<AxiosResponse<Heartbeat>> {
    return this.api.get(`/api/v1/heartbeats/${deviceId}/latest`);
  }

  async getHealthScoreStats(deviceId: string): Promise<AxiosResponse<HealthScoreStats>> {
    return this.api.get(`/api/v1/heartbeats/${deviceId}/health-score`);
  }

  // Alert endpoints
  async getAlerts(params?: {
    skip?: number;
    limit?: number;
    device_id?: string;
    is_active?: boolean;
  }): Promise<AxiosResponse<AlertListResponse>> {
    return this.api.get('/api/v1/alerts/', { params });
  }

  async getAlert(id: string): Promise<AxiosResponse<Alert>> {
    return this.api.get(`/api/v1/alerts/${id}`);
  }

  async createAlert(alertData: AlertCreate): Promise<AxiosResponse<Alert>> {
    return this.api.post('/api/v1/alerts/', alertData);
  }

  async updateAlert(id: string, alertData: AlertUpdate): Promise<AxiosResponse<Alert>> {
    return this.api.put(`/api/v1/alerts/${id}`, alertData);
  }

  async deleteAlert(id: string): Promise<AxiosResponse<void>> {
    return this.api.delete(`/api/v1/alerts/${id}`);
  }

  async toggleAlert(id: string): Promise<AxiosResponse<Alert>> {
    return this.api.patch(`/api/v1/alerts/${id}/toggle`);
  }

  async getAlertStats(): Promise<AxiosResponse<any>> {
    return this.api.get('/api/v1/alerts/stats');
  }
}

export const apiService = new ApiService();
