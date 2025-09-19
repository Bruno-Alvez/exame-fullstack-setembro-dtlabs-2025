import React, { useEffect, useState } from 'react';
import { 
  Bell, 
  Plus, 
  Search, 
  ToggleLeft, 
  ToggleRight,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useAlertStore } from '@/store/alertStore';
import { useDeviceStore } from '@/store/deviceStore';
import { apiService } from '@/services/api';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Alert, AlertCreate } from '@/types';
import { formatDate, formatRelativeTime } from '@/utils';
import toast from 'react-hot-toast';

export const NotificationsPage: React.FC = () => {
  const { 
    alerts, 
    setAlerts, 
    setTotalCount, 
    setLoading, 
    setError,
    updateAlert,
    removeAlert,
    currentPage,
    pageSize,
  } = useAlertStore();

  const { devices } = useDeviceStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newAlert, setNewAlert] = useState<Partial<AlertCreate>>({
    name: '',
    description: '',
    device_id: '',
    conditions: [],
  });

  useEffect(() => {
    loadAlerts();
  }, [currentPage, pageSize]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAlerts({
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      });
      
      setAlerts(response.data.items);
      setTotalCount(response.data.total);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load alerts';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      await apiService.toggleAlert(alertId);
      updateAlert(alertId, { is_active: !isActive });
      toast.success(`Alert ${!isActive ? 'activated' : 'deactivated'}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to toggle alert';
      toast.error(errorMessage);
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    if (!confirm('Are you sure you want to delete this alert?')) {
      return;
    }

    try {
      await apiService.deleteAlert(alertId);
      removeAlert(alertId);
      toast.success('Alert deleted successfully');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete alert';
      toast.error(errorMessage);
    }
  };

  const handleCreateAlert = async () => {
    if (!newAlert.name || !newAlert.device_id || !newAlert.conditions?.length) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      setIsCreating(true);
      const response = await apiService.createAlert(newAlert as AlertCreate);
      setAlerts([response.data, ...alerts]);
      setShowCreateForm(false);
      setNewAlert({
        name: '',
        description: '',
        device_id: '',
        conditions: [],
      });
      toast.success('Alert created successfully');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create alert';
      toast.error(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const addCondition = () => {
    setNewAlert(prev => ({
      ...prev,
      conditions: [
        ...(prev.conditions || []),
        {
          metric: 'cpu_usage',
          operator: 'gt',
          value: 70,
          duration: 5,
        }
      ]
    }));
  };

  const removeCondition = (index: number) => {
    setNewAlert(prev => ({
      ...prev,
      conditions: prev.conditions?.filter((_, i) => i !== index) || []
    }));
  };

  const updateCondition = (index: number, field: string, value: any) => {
    setNewAlert(prev => ({
      ...prev,
      conditions: prev.conditions?.map((condition, i) => 
        i === index ? { ...condition, [field]: value } : condition
      ) || []
    }));
  };

  const getAlertIcon = (alert: Alert) => {
    if (!alert.is_active) {
      return <XCircle className="h-5 w-5 text-secondary-400" />;
    }
    
    if (alert.last_triggered) {
      return <AlertTriangle className="h-5 w-5 text-danger-500" />;
    }
    
    return <CheckCircle className="h-5 w-5 text-success-500" />;
  };

  const filteredAlerts = alerts.filter(alert =>
    alert.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    alert.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-secondary-900">Notifications</h1>
            <p className="text-secondary-600">
              Manage alerts and notifications for your devices
            </p>
          </div>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Alert
          </Button>
        </div>

        {/* Create Alert Form */}
        {showCreateForm && (
          <Card>
            <CardHeader>
              <CardTitle>Create New Alert</CardTitle>
              <CardDescription>
                Set up monitoring conditions for your devices
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Alert Name"
                  placeholder="Enter alert name"
                  value={newAlert.name}
                  onChange={(e) => setNewAlert(prev => ({ ...prev, name: e.target.value }))}
                />
                
                <div>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Device
                  </label>
                  <select
                    className="input-field"
                    value={newAlert.device_id}
                    onChange={(e) => setNewAlert(prev => ({ ...prev, device_id: e.target.value }))}
                  >
                    <option value="">Select a device</option>
                    {devices.map(device => (
                      <option key={device.id} value={device.id}>
                        {device.name} - {device.location}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <Input
                label="Description (Optional)"
                placeholder="Enter alert description"
                value={newAlert.description}
                onChange={(e) => setNewAlert(prev => ({ ...prev, description: e.target.value }))}
              />

              {/* Conditions */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-secondary-700">
                    Conditions
                  </label>
                  <Button size="sm" variant="secondary" onClick={addCondition}>
                    <Plus className="h-4 w-4 mr-1" />
                    Add Condition
                  </Button>
                </div>
                
                <div className="space-y-3">
                  {newAlert.conditions?.map((condition, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 border border-secondary-200 rounded-lg">
                      <select
                        className="input-field flex-1"
                        value={condition.metric}
                        onChange={(e) => updateCondition(index, 'metric', e.target.value)}
                      >
                        <option value="cpu_usage">CPU Usage</option>
                        <option value="ram_usage">RAM Usage</option>
                        <option value="temperature">Temperature</option>
                        <option value="free_disk_space">Free Disk Space</option>
                        <option value="dns_latency">DNS Latency</option>
                        <option value="connectivity">Connectivity</option>
                        <option value="health_score">Health Score</option>
                      </select>
                      
                      <select
                        className="input-field"
                        value={condition.operator}
                        onChange={(e) => updateCondition(index, 'operator', e.target.value)}
                      >
                        <option value="gt">Greater than</option>
                        <option value="lt">Less than</option>
                        <option value="eq">Equals</option>
                        <option value="gte">Greater than or equal</option>
                        <option value="lte">Less than or equal</option>
                      </select>
                      
                      <Input
                        type="number"
                        className="w-24"
                        value={typeof condition.value === 'number' ? condition.value : ''}
                        onChange={(e) => updateCondition(index, 'value', parseFloat(e.target.value))}
                      />
                      
                      <Input
                        type="number"
                        className="w-20"
                        placeholder="Min"
                        value={typeof condition.duration === 'number' ? condition.duration : ''}
                        onChange={(e) => updateCondition(index, 'duration', parseInt(e.target.value))}
                      />
                      
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => removeCondition(index)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Button onClick={handleCreateAlert} loading={isCreating}>
                  Create Alert
                </Button>
                <Button variant="secondary" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Search */}
        <Card>
          <CardContent className="p-4">
            <Input
              placeholder="Search alerts..."
              leftIcon={<Search className="h-4 w-4" />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </CardContent>
        </Card>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Bell className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-secondary-900 mb-2">
                  No alerts found
                </h3>
                <p className="text-secondary-500 mb-4">
                  Create your first alert to start monitoring your devices.
                </p>
                <Button onClick={() => setShowCreateForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Alert
                </Button>
              </CardContent>
            </Card>
          ) : (
            filteredAlerts.map((alert) => (
              <Card key={alert.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      {getAlertIcon(alert)}
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-medium text-secondary-900">
                            {alert.name}
                          </h3>
                          <StatusBadge 
                            status={alert.is_active ? 'healthy' : 'offline'}
                          >
                            {alert.is_active ? 'Active' : 'Inactive'}
                          </StatusBadge>
                        </div>
                        
                        {alert.description && (
                          <p className="text-secondary-600 mb-3">
                            {alert.description}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-4 text-sm text-secondary-500">
                          <span>Device: {alert.device?.name || 'Unknown'}</span>
                          <span>•</span>
                          <span>Created: {formatDate(alert.created_at)}</span>
                          {alert.last_triggered && (
                            <>
                              <span>•</span>
                              <span>Last triggered: {formatRelativeTime(alert.last_triggered)}</span>
                            </>
                          )}
                        </div>
                        
                        <div className="mt-3">
                          <p className="text-sm font-medium text-secondary-700 mb-1">
                            Conditions:
                          </p>
                          <p className="text-sm text-secondary-600">
                            {alert.conditions_summary}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleToggleAlert(alert.id, alert.is_active)}
                      >
                        {alert.is_active ? (
                          <ToggleRight className="h-4 w-4 text-success-500" />
                        ) : (
                          <ToggleLeft className="h-4 w-4 text-secondary-400" />
                        )}
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteAlert(alert.id)}
                      >
                        <XCircle className="h-4 w-4 text-danger-500" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </Layout>
  );
};

export default NotificationsPage;
