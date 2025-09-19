import { create } from 'zustand';
import { Device, FilterOptions } from '@/types';

interface DeviceState {
  devices: Device[];
  selectedDevice: Device | null;
  isLoading: boolean;
  error: string | null;
  filters: FilterOptions;
  totalCount: number;
  currentPage: number;
  pageSize: number;
}

interface DeviceActions {
  setDevices: (devices: Device[]) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: string, updates: Partial<Device>) => void;
  removeDevice: (id: string) => void;
  setSelectedDevice: (device: Device | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<FilterOptions>) => void;
  setTotalCount: (count: number) => void;
  setCurrentPage: (page: number) => void;
  setPageSize: (size: number) => void;
  clearError: () => void;
  reset: () => void;
}

type DeviceStore = DeviceState & DeviceActions;

const initialState: DeviceState = {
  devices: [],
  selectedDevice: null,
  isLoading: false,
  error: null,
  filters: {},
  totalCount: 0,
  currentPage: 1,
  pageSize: 20,
};

export const useDeviceStore = create<DeviceStore>((set) => ({
  ...initialState,

  setDevices: (devices: Device[]) => {
    set({ devices, error: null });
  },

  addDevice: (device: Device) => {
    set((state) => ({
      devices: [device, ...state.devices],
      totalCount: state.totalCount + 1,
    }));
  },

  updateDevice: (id: string, updates: Partial<Device>) => {
    set((state) => ({
      devices: state.devices.map((device) =>
        device.id === id ? { ...device, ...updates } : device
      ),
      selectedDevice: state.selectedDevice?.id === id 
        ? { ...state.selectedDevice, ...updates }
        : state.selectedDevice,
    }));
  },

  removeDevice: (id: string) => {
    set((state) => ({
      devices: state.devices.filter((device) => device.id !== id),
      selectedDevice: state.selectedDevice?.id === id ? null : state.selectedDevice,
      totalCount: Math.max(0, state.totalCount - 1),
    }));
  },

  setSelectedDevice: (device: Device | null) => {
    set({ selectedDevice: device });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setFilters: (filters: Partial<FilterOptions>) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
      currentPage: 1, // Reset to first page when filters change
    }));
  },

  setTotalCount: (count: number) => {
    set({ totalCount: count });
  },

  setCurrentPage: (page: number) => {
    set({ currentPage: page });
  },

  setPageSize: (size: number) => {
    set({ pageSize: size, currentPage: 1 });
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set(initialState);
  },
}));
