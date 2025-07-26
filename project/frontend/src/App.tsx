import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import MainLayout from '@/components/Layout/MainLayout';
import Dashboard from '@/pages/Dashboard';
import OrderManagement from '@/pages/OrderManagement';
import ProductionPlan from '@/pages/ProductionPlan';
import MaterialManagement from '@/pages/MaterialManagement';
import ProgressTracking from '@/pages/ProgressTracking';
import Scheduling from '@/pages/Scheduling';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/*" element={
            <MainLayout>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/orders" element={<OrderManagement />} />
                <Route path="/production" element={<ProductionPlan />} />
                <Route path="/materials" element={<MaterialManagement />} />
                <Route path="/progress" element={<ProgressTracking />} />
                <Route path="/scheduling" element={<Scheduling />} />
              </Routes>
            </MainLayout>
          } />
        </Routes>
      </div>
    </Router>
  );
};

export default App;