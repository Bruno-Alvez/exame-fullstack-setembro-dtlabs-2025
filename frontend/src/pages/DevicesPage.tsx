import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Download, 
  Server
} from 'lucide-react';
import { useDeviceStore } from '@/store/deviceStore';
import { apiService } from '@/services/api';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { StatusBadge, HealthScoreBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Device, Heartbeat, TimeRange } from '@/types';
import { formatDate, formatRelativeTime, generateTimeRanges, exportToCSV } from '@/utils';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import toast from 'react-hot-toast';

export const DevicesPage: React.FC = () => {
  const { 
    devices, 
    setDevices, 
    setTotalCount, 
    setCurrentPage, 
    setLoading, 
    setError,
    filters,
    setFilters,
    currentPage,
    pageSize,
    totalCount
  } = useDeviceStore();

  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [heartbeats, setHeartbeats] = useState<Heartbeat[]>([]);
  const [isLoadingHeartbeats, setIsLoadingHeartbeats] = useState(false);
  const [timeRange, setTimeRange] = useState<TimeRange>(generateTimeRanges().last24Hours);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadDevices();
  }, [currentPage, pageSize, filters]);

  useEffect(() => {
    if (selectedDevice) {
      loadHeartbeats(selectedDevice.id);
    }
  }, [selectedDevice, timeRange]);

  const loadDevices = async () => {
    try {
      setLoading(true);
      const response = await apiService.getDevices({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
        search: searchTerm || undefined,
      });
      
      setDevices(response.data.items);
      setTotalCount(response.data.total);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load devices';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const loadHeartbeats = async (deviceId: string) => {
    try {
      setIsLoadingHeartbeats(true);
      const response = await apiService.getHeartbeats(deviceId, {
        start_date: timeRange.start.toISOString(),
        end_date: timeRange.end.toISOString(),
        limit: 100,
      });
      
      setHeartbeats(response.data.items);
    } catch (error: any) {
      console.error('Failed to load heartbeats:', error);
    } finally {
      setIsLoadingHeartbeats(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setFilters({ search: value });
    setCurrentPage(1);
  };

  const handleExport = () => {
    if (devices.length === 0) {
      toast.error('No devices to export');
      return;
    }

    const exportData = devices.map(device => ({
      name: device.name,
      location: device.location,
      serial_number: device.serial_number,
      status: device.status,
      health_score: device.current_health_score,
      last_seen: device.last_seen,
      created_at: device.created_at,
    }));

    exportToCSV(exportData, 'devices');
    toast.success('Devices exported successfully');
  };


  const chartData = heartbeats.map(heartbeat => ({
    timestamp: new Date(heartbeat.timestamp).toLocaleTimeString(),
    health_score: heartbeat.health_score,
    cpu_usage: heartbeat.cpu_usage,
    ram_usage: heartbeat.ram_usage,
    temperature: heartbeat.temperature,
  }));

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-secondary-900">Devices</h1>
            <p className="text-secondary-600">
              Monitor and analyze your IoT devices performance
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <Button onClick={handleExport} variant="secondary">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Link to="/device-management">
              <Button>
                <Server className="h-4 w-4 mr-2" />
                Add Device
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Device List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Device List</CardTitle>
                <CardDescription>
                  {totalCount} devices found
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Search */}
                <div className="mb-4">
                  <Input
                    placeholder="Search devices..."
                    leftIcon={<Search className="h-4 w-4" />}
                    value={searchTerm}
                    onChange={(e) => handleSearch(e.target.value)}
                  />
                </div>

                {/* Device List */}
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {devices.map((device) => (
                    <div
                      key={device.id}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedDevice?.id === device.id
                          ? 'border-primary-300 bg-primary-50'
                          : 'border-secondary-200 hover:bg-secondary-50'
                      }`}
                      onClick={() => setSelectedDevice(device)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-secondary-900">
                            {device.name}
                          </p>
                          <p className="text-sm text-secondary-500">
                            {device.location}
                          </p>
                        </div>
                        <div className="text-right">
                          <HealthScoreBadge score={device.current_health_score} />
                          <p className="text-xs text-secondary-500 mt-1">
                            {device.last_seen
                              ? formatRelativeTime(device.last_seen)
                              : 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Device Details & Charts */}
          <div className="lg:col-span-2">
            {selectedDevice ? (
              <div className="space-y-6">
                {/* Device Info */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>{selectedDevice.name}</CardTitle>
                        <CardDescription>
                          {selectedDevice.location} • {selectedDevice.serial_number}
                        </CardDescription>
                      </div>
                      <StatusBadge status={selectedDevice.status} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-secondary-900">
                          {selectedDevice.current_health_score.toFixed(1)}
                        </p>
                        <p className="text-sm text-secondary-500">Health Score</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-secondary-900">
                          {selectedDevice.is_online ? 'Online' : 'Offline'}
                        </p>
                        <p className="text-sm text-secondary-500">Status</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-secondary-900">
                          {selectedDevice.last_seen
                            ? formatRelativeTime(selectedDevice.last_seen)
                            : 'Never'}
                        </p>
                        <p className="text-sm text-secondary-500">Last Seen</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-secondary-900">
                          {formatDate(selectedDevice.created_at)}
                        </p>
                        <p className="text-sm text-secondary-500">Created</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Time Range Selector */}
                <Card>
                  <CardHeader>
                    <CardTitle>Time Range</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(generateTimeRanges()).map(([key, range]) => (
                        <Button
                          key={key}
                          variant={timeRange.label === range.label ? 'primary' : 'secondary'}
                          size="sm"
                          onClick={() => setTimeRange(range)}
                        >
                          {range.label}
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Charts */}
                <Card>
                  <CardHeader>
                    <CardTitle>Performance Metrics</CardTitle>
                    <CardDescription>
                      Historical data for {timeRange.label.toLowerCase()}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {isLoadingHeartbeats ? (
                      <div className="h-64 flex items-center justify-center">
                        <LoadingSpinner />
                      </div>
                    ) : chartData.length > 0 ? (
                      <div className="space-y-6">
                        {/* Health Score Chart */}
                        <div>
                          <h4 className="text-sm font-medium text-secondary-700 mb-2">
                            Health Score Trend
                          </h4>
                          <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="timestamp" />
                              <YAxis domain={[0, 100]} />
                              <Tooltip />
                              <Area
                                type="monotone"
                                dataKey="health_score"
                                stroke="#0ea5e9"
                                fill="#0ea5e9"
                                fillOpacity={0.3}
                              />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>

                        {/* CPU & RAM Chart */}
                        <div>
                          <h4 className="text-sm font-medium text-secondary-700 mb-2">
                            CPU & RAM Usage
                          </h4>
                          <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="timestamp" />
                              <YAxis domain={[0, 100]} />
                              <Tooltip />
                              <Line
                                type="monotone"
                                dataKey="cpu_usage"
                                stroke="#ef4444"
                                strokeWidth={2}
                              />
                              <Line
                                type="monotone"
                                dataKey="ram_usage"
                                stroke="#f59e0b"
                                strokeWidth={2}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>

                        {/* Temperature Chart */}
                        <div>
                          <h4 className="text-sm font-medium text-secondary-700 mb-2">
                            Temperature
                          </h4>
                          <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={chartData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="timestamp" />
                              <YAxis />
                              <Tooltip />
                              <Line
                                type="monotone"
                                dataKey="temperature"
                                stroke="#22c55e"
                                strokeWidth={2}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    ) : (
                      <div className="h-64 flex items-center justify-center text-secondary-500">
                        No data available for the selected time range
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="p-12 text-center">
                  <Server className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-secondary-900 mb-2">
                    Select a Device
                  </h3>
                  <p className="text-secondary-500">
                    Choose a device from the list to view its performance metrics and historical data.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DevicesPage;
