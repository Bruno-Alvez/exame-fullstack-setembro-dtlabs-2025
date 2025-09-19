import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { websocketService } from '@/services/websocket';
import { LoadingPage } from '@/components/ui/LoadingSpinner';

// Lazy load pages for better performance
const LoginPage = React.lazy(() => import('@/pages/LoginPage'));
const RegisterPage = React.lazy(() => import('@/pages/RegisterPage'));
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'));
const DevicesPage = React.lazy(() => import('@/pages/DevicesPage'));
const NotificationsPage = React.lazy(() => import('@/pages/NotificationsPage'));
const DeviceManagementPage = React.lazy(() => import('@/pages/DeviceManagementPage'));

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingPage message="Authenticating..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Public Route wrapper (redirect to dashboard if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingPage message="Loading..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  const { isAuthenticated, accessToken, user } = useAuthStore();

  // Initialize WebSocket connection when authenticated
  useEffect(() => {
    if (isAuthenticated && accessToken && user) {
      websocketService.connect(accessToken).catch((error) => {
        console.error('Failed to connect to WebSocket:', error);
      });

      // Subscribe to user-specific notifications
      websocketService.subscribeToUser(user.id);
    } else {
      websocketService.disconnect();
    }

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [isAuthenticated, accessToken, user]);

  return (
    <div className="min-h-screen bg-secondary-50">
      <React.Suspense fallback={<LoadingPage />}>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devices"
            element={
              <ProtectedRoute>
                <DevicesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/device-management"
            element={
              <ProtectedRoute>
                <DeviceManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route
            path="/"
            element={<Navigate to="/dashboard" replace />}
          />

          {/* Catch all route */}
          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />
        </Routes>
      </React.Suspense>
    </div>
  );
};

export default App;
