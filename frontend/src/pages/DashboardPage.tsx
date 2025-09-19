import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Server, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Plus
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useDeviceStore } from '@/store/deviceStore';
import { apiService } from '@/services/api';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { HealthScoreBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { DeviceStats } from '@/types';
import { formatRelativeTime } from '@/utils';
import toast from 'react-hot-toast';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { devices, setDevices, setLoading, setError } = useDeviceStore();
  const [stats, setStats] = useState<DeviceStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setIsLoadingStats(true);

      // Load devices and stats in parallel
      const [devicesResponse, statsResponse] = await Promise.all([
        apiService.getDevices({ limit: 10 }),
        apiService.getDeviceStats(),
      ]);

      setDevices(devicesResponse.data.items);
      setStats(statsResponse.data);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load dashboard data';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setIsLoadingStats(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-success-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-warning-500" />;
      case 'critical':
        return <XCircle className="h-5 w-5 text-danger-500" />;
      default:
        return <XCircle className="h-5 w-5 text-secondary-400" />;
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-success-500" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-danger-500" />;
      default:
        return <Minus className="h-4 w-4 text-secondary-400" />;
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            Welcome back, {user?.full_name}
          </h1>
          <p className="text-secondary-600">
            Monitor your IoT devices and their performance in real-time
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-600">Total Devices</p>
                  <p className="text-2xl font-bold text-secondary-900">
                    {isLoadingStats ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      stats?.total_devices || 0
                    )}
                  </p>
                </div>
                <div className="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Server className="h-6 w-6 text-primary-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-600">Online Devices</p>
                  <p className="text-2xl font-bold text-success-600">
                    {isLoadingStats ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      stats?.online_devices || 0
                    )}
                  </p>
                </div>
                <div className="h-12 w-12 bg-success-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="h-6 w-6 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-600">Warning Devices</p>
                  <p className="text-2xl font-bold text-warning-600">
                    {isLoadingStats ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      stats?.warning_devices || 0
                    )}
                  </p>
                </div>
                <div className="h-12 w-12 bg-warning-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-warning-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-600">Critical Devices</p>
                  <p className="text-2xl font-bold text-danger-600">
                    {isLoadingStats ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      stats?.critical_devices || 0
                    )}
                  </p>
                </div>
                <div className="h-12 w-12 bg-danger-100 rounded-lg flex items-center justify-center">
                  <XCircle className="h-6 w-6 text-danger-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Average Health Score */}
        {stats && (
          <Card>
            <CardHeader>
              <CardTitle>System Health Overview</CardTitle>
              <CardDescription>
                Average health score across all devices
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="text-3xl font-bold text-secondary-900">
                    {stats.average_health_score.toFixed(1)}
                  </div>
                  <div className="flex items-center space-x-2">
                    {getTrendIcon('stable')}
                    <span className="text-sm text-secondary-600">Stable</span>
                  </div>
                </div>
                <div className="w-32 h-32 relative">
                  <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-secondary-200"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${(stats.average_health_score / 100) * 251.2} 251.2`}
                      className="text-primary-600 transition-all duration-1000 ease-in-out"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-semibold text-secondary-900">
                      {Math.round(stats.average_health_score)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Devices */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Devices</CardTitle>
              <CardDescription>
                Latest device activity and status updates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {devices.length === 0 ? (
                  <div className="text-center py-8">
                    <Server className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
                    <p className="text-secondary-500">No devices found</p>
                    <Link
                      to="/device-management"
                      className="text-primary-600 hover:text-primary-500 text-sm font-medium"
                    >
                      Add your first device
                    </Link>
                  </div>
                ) : (
                  devices.slice(0, 5).map((device) => (
                    <div
                      key={device.id}
                      className="flex items-center justify-between p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(device.status)}
                        <div>
                          <p className="font-medium text-secondary-900">
                            {device.name}
                          </p>
                          <p className="text-sm text-secondary-500">
                            {device.location}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <HealthScoreBadge score={device.current_health_score} />
                        <div className="text-right">
                          <p className="text-xs text-secondary-500">
                            {device.last_seen
                              ? formatRelativeTime(device.last_seen)
                              : 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>
                Common tasks and navigation shortcuts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <Link
                  to="/devices"
                  className="p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors text-center"
                >
                  <Server className="h-8 w-8 text-primary-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-secondary-900">View Devices</p>
                  <p className="text-xs text-secondary-500">Monitor all devices</p>
                </Link>

                <Link
                  to="/notifications"
                  className="p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors text-center"
                >
                  <AlertTriangle className="h-8 w-8 text-warning-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-secondary-900">Alerts</p>
                  <p className="text-xs text-secondary-500">Manage notifications</p>
                </Link>

                <Link
                  to="/device-management"
                  className="p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors text-center"
                >
                  <Plus className="h-8 w-8 text-success-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-secondary-900">Add Device</p>
                  <p className="text-xs text-secondary-500">Register new device</p>
                </Link>

                <Link
                  to="/devices"
                  className="p-4 border border-secondary-200 rounded-lg hover:bg-secondary-50 transition-colors text-center"
                >
                  <Activity className="h-8 w-8 text-primary-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-secondary-900">Analytics</p>
                  <p className="text-xs text-secondary-500">View metrics</p>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
