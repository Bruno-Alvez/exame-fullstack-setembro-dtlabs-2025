import React, { useEffect, useState } from 'react';
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Save, 
  X,
  Server,
  MapPin,
  Hash,
  FileText
} from 'lucide-react';
import { useDeviceStore } from '@/store/deviceStore';
import { apiService } from '@/services/api';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Device, DeviceCreate, DeviceUpdate } from '@/types';
import { formatDate, validateSerialNumber, formatSerialNumber } from '@/utils';
import toast from 'react-hot-toast';

export const DeviceManagementPage: React.FC = () => {
  const { 
    devices, 
    setDevices, 
    setTotalCount, 
    setCurrentPage, 
    setLoading, 
    setError,
    addDevice,
    updateDevice,
    removeDevice,
    currentPage,
    pageSize,
    totalCount
  } = useDeviceStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [newDevice, setNewDevice] = useState<DeviceCreate>({
    name: '',
    location: '',
    serial_number: '',
    description: '',
  });

  useEffect(() => {
    loadDevices();
  }, [currentPage, pageSize]);

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

  const handleCreateDevice = async () => {
    if (!newDevice.name || !newDevice.location || !newDevice.serial_number) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (!validateSerialNumber(newDevice.serial_number)) {
      toast.error('Serial number must be exactly 12 digits');
      return;
    }

    try {
      setIsCreating(true);
      const response = await apiService.createDevice(newDevice);
      addDevice(response.data);
      setShowCreateForm(false);
      setNewDevice({
        name: '',
        location: '',
        serial_number: '',
        description: '',
      });
      toast.success('Device created successfully');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create device';
      toast.error(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateDevice = async (device: Device) => {
    if (!device.name || !device.location) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      setIsUpdating(true);
      const updateData: DeviceUpdate = {
        name: device.name,
        location: device.location,
        description: device.description,
      };
      
      const response = await apiService.updateDevice(device.id, updateData);
      updateDevice(device.id, response.data);
      setEditingDevice(null);
      toast.success('Device updated successfully');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update device';
      toast.error(errorMessage);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    if (!confirm('Are you sure you want to delete this device? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteDevice(deviceId);
      removeDevice(deviceId);
      toast.success('Device deleted successfully');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete device';
      toast.error(errorMessage);
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
    // Debounce search
    setTimeout(() => {
      if (value === searchTerm) {
        loadDevices();
      }
    }, 500);
  };

  const filteredDevices = devices.filter(device =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.serial_number.includes(searchTerm)
  );

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-secondary-900">Device Management</h1>
            <p className="text-secondary-600">
              Manage your IoT devices and their configurations
            </p>
          </div>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Device
          </Button>
        </div>

        {/* Create Device Form */}
        {showCreateForm && (
          <Card>
            <CardHeader>
              <CardTitle>Add New Device</CardTitle>
              <CardDescription>
                Register a new IoT device for monitoring
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Device Name"
                  placeholder="Enter device name"
                  leftIcon={<Server className="h-4 w-4" />}
                  value={newDevice.name}
                  onChange={(e) => setNewDevice(prev => ({ ...prev, name: e.target.value }))}
                />
                
                <Input
                  label="Location"
                  placeholder="Enter device location"
                  leftIcon={<MapPin className="h-4 w-4" />}
                  value={newDevice.location}
                  onChange={(e) => setNewDevice(prev => ({ ...prev, location: e.target.value }))}
                />
              </div>

              <Input
                label="Serial Number"
                placeholder="Enter 12-digit serial number"
                leftIcon={<Hash className="h-4 w-4" />}
                value={newDevice.serial_number}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 12);
                  setNewDevice(prev => ({ ...prev, serial_number: value }));
                }}
                helperText="Must be exactly 12 digits"
              />

              <Input
                label="Description (Optional)"
                placeholder="Enter device description"
                leftIcon={<FileText className="h-4 w-4" />}
                value={newDevice.description}
                onChange={(e) => setNewDevice(prev => ({ ...prev, description: e.target.value }))}
              />

              <div className="flex items-center space-x-3">
                <Button onClick={handleCreateDevice} loading={isCreating}>
                  <Save className="h-4 w-4 mr-2" />
                  Create Device
                </Button>
                <Button 
                  variant="secondary" 
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewDevice({
                      name: '',
                      location: '',
                      serial_number: '',
                      description: '',
                    });
                  }}
                >
                  <X className="h-4 w-4 mr-2" />
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
              placeholder="Search devices..."
              leftIcon={<Search className="h-4 w-4" />}
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </CardContent>
        </Card>

        {/* Devices List */}
        <div className="space-y-4">
          {filteredDevices.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Server className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-secondary-900 mb-2">
                  No devices found
                </h3>
                <p className="text-secondary-500 mb-4">
                  Add your first device to start monitoring.
                </p>
                <Button onClick={() => setShowCreateForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Device
                </Button>
              </CardContent>
            </Card>
          ) : (
            filteredDevices.map((device) => (
              <Card key={device.id}>
                <CardContent className="p-6">
                  {editingDevice?.id === device.id ? (
                    // Edit Mode
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input
                          label="Device Name"
                          value={editingDevice.name}
                          onChange={(e) => setEditingDevice(prev => 
                            prev ? { ...prev, name: e.target.value } : null
                          )}
                        />
                        
                        <Input
                          label="Location"
                          value={editingDevice.location}
                          onChange={(e) => setEditingDevice(prev => 
                            prev ? { ...prev, location: e.target.value } : null
                          )}
                        />
                      </div>

                      <Input
                        label="Description"
                        value={editingDevice.description || ''}
                        onChange={(e) => setEditingDevice(prev => 
                          prev ? { ...prev, description: e.target.value } : null
                        )}
                      />

                      <div className="flex items-center space-x-3">
                        <Button 
                          onClick={() => handleUpdateDevice(editingDevice)}
                          loading={isUpdating}
                        >
                          <Save className="h-4 w-4 mr-2" />
                          Save Changes
                        </Button>
                        <Button 
                          variant="secondary" 
                          onClick={() => setEditingDevice(null)}
                        >
                          <X className="h-4 w-4 mr-2" />
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-medium text-secondary-900">
                            {device.name}
                          </h3>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                            {device.is_online ? 'Online' : 'Offline'}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-secondary-600">
                          <div className="flex items-center space-x-2">
                            <MapPin className="h-4 w-4" />
                            <span>{device.location}</span>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <Hash className="h-4 w-4" />
                            <span>{formatSerialNumber(device.serial_number)}</span>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <span>Health: {device.current_health_score.toFixed(1)}%</span>
                          </div>
                        </div>
                        
                        {device.description && (
                          <p className="text-secondary-600 mt-2">
                            {device.description}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-4 text-xs text-secondary-500 mt-3">
                          <span>Created: {formatDate(device.created_at)}</span>
                          {device.last_seen && (
                            <span>Last seen: {formatDate(device.last_seen)}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setEditingDevice(device)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteDevice(device.id)}
                        >
                          <Trash2 className="h-4 w-4 text-danger-500" />
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalCount > pageSize && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-secondary-600">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} devices
                </p>
                
                <div className="flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={currentPage === 1}
                    onClick={() => setCurrentPage(currentPage - 1)}
                  >
                    Previous
                  </Button>
                  
                  <span className="text-sm text-secondary-600">
                    Page {currentPage} of {Math.ceil(totalCount / pageSize)}
                  </span>
                  
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={currentPage >= Math.ceil(totalCount / pageSize)}
                    onClick={() => setCurrentPage(currentPage + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default DeviceManagementPage;
