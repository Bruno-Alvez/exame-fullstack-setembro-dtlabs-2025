import { create } from 'zustand';
import { Alert } from '@/types';

interface AlertState {
  alerts: Alert[];
  selectedAlert: Alert | null;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  activeAlerts: Alert[];
}

interface AlertActions {
  setAlerts: (alerts: Alert[]) => void;
  addAlert: (alert: Alert) => void;
  updateAlert: (id: string, updates: Partial<Alert>) => void;
  removeAlert: (id: string) => void;
  setSelectedAlert: (alert: Alert | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setTotalCount: (count: number) => void;
  setCurrentPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setActiveAlerts: (alerts: Alert[]) => void;
  addActiveAlert: (alert: Alert) => void;
  removeActiveAlert: (id: string) => void;
  clearError: () => void;
  reset: () => void;
}

type AlertStore = AlertState & AlertActions;

const initialState: AlertState = {
  alerts: [],
  selectedAlert: null,
  isLoading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  pageSize: 20,
  activeAlerts: [],
};

export const useAlertStore = create<AlertStore>((set) => ({
  ...initialState,

  setAlerts: (alerts: Alert[]) => {
    set({ alerts, error: null });
  },

  addAlert: (alert: Alert) => {
    set((state) => ({
      alerts: [alert, ...state.alerts],
      totalCount: state.totalCount + 1,
    }));
  },

  updateAlert: (id: string, updates: Partial<Alert>) => {
    set((state) => ({
      alerts: state.alerts.map((alert) =>
        alert.id === id ? { ...alert, ...updates } : alert
      ),
      selectedAlert: state.selectedAlert?.id === id 
        ? { ...state.selectedAlert, ...updates }
        : state.selectedAlert,
    }));
  },

  removeAlert: (id: string) => {
    set((state) => ({
      alerts: state.alerts.filter((alert) => alert.id !== id),
      selectedAlert: state.selectedAlert?.id === id ? null : state.selectedAlert,
      totalCount: Math.max(0, state.totalCount - 1),
      activeAlerts: state.activeAlerts.filter((alert) => alert.id !== id),
    }));
  },

  setSelectedAlert: (alert: Alert | null) => {
    set({ selectedAlert: alert });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: string | null) => {
    set({ error });
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

  setActiveAlerts: (alerts: Alert[]) => {
    set({ activeAlerts: alerts });
  },

  addActiveAlert: (alert: Alert) => {
    set((state) => ({
      activeAlerts: [alert, ...state.activeAlerts.filter(a => a.id !== alert.id)],
    }));
  },

  removeActiveAlert: (id: string) => {
    set((state) => ({
      activeAlerts: state.activeAlerts.filter((alert) => alert.id !== id),
    }));
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set(initialState);
  },
}));
