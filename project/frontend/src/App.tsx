import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import MainLayout from './components/Layout/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Forbidden from './pages/403';
import Dashboard from '@/pages/Dashboard';
import OrderManagement from '@/pages/OrderManagement';
import ProductionPlan from '@/pages/ProductionPlan';
import MaterialManagement from '@/pages/MaterialManagement';
import ProgressTracking from '@/pages/ProgressTracking';
import Scheduling from '@/pages/Scheduling';
import ChartDemo from './pages/ChartDemo';
import Reports from '@/pages/Reports';
import NotificationCenter from '@/pages/NotificationCenter';
import ReminderCenter from '@/pages/ReminderCenter';
import { initializeAuth } from './stores/authStore';
import './App.css';

const App: React.FC = () => {
  useEffect(() => {
    // 初始化认证状态
    initializeAuth();
  }, []);

  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <div className="App">
          <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<Login />} />
            <Route path="/403" element={<Forbidden />} />
            
            {/* 受保护的路由 */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/*" element={
              <ProtectedRoute>
                <MainLayout>
                  <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/orders" element={
                      <ProtectedRoute requiredPermission="order:read">
                        <OrderManagement />
                      </ProtectedRoute>
                    } />
                    <Route path="/production" element={
                      <ProtectedRoute requiredPermission="production:read">
                        <ProductionPlan />
                      </ProtectedRoute>
                    } />
                    <Route path="/materials" element={
                      <ProtectedRoute requiredPermission="material:read">
                        <MaterialManagement />
                      </ProtectedRoute>
                    } />
                    <Route path="/progress" element={
                      <ProtectedRoute requiredPermission="progress:read">
                        <ProgressTracking />
                      </ProtectedRoute>
                    } />
                    <Route path="/scheduling" element={
                      <ProtectedRoute requiredPermission="schedule:read">
                        <Scheduling />
                      </ProtectedRoute>
                    } />
                    <Route path="/charts" element={<ChartDemo />} />
                    <Route path="/reports" element={
                      <ProtectedRoute requiredPermission="report:read">
                        <Reports />
                      </ProtectedRoute>
                    } />
                    <Route path="/notifications" element={<NotificationCenter />} />
                    <Route path="/reminders" element={<ReminderCenter />} />
                  </Routes>
                </MainLayout>
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
};

export default App;