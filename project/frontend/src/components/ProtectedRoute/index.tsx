import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '../../stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: string;
  fallbackPath?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  requiredRole,
  fallbackPath = '/login'
}) => {
  const location = useLocation();
  const {
    isAuthenticated,
    isLoading,
    user,
    checkPermission,
    checkRole,
    getCurrentUser
  } = useAuthStore();
  
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (token && !user) {
        try {
          await getCurrentUser();
        } catch (error) {
          console.error('获取用户信息失败:', error);
        }
      }
      
      setIsInitializing(false);
    };

    initializeAuth();
  }, [user, getCurrentUser]);

  // 显示加载状态
  if (isLoading || isInitializing) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="正在验证身份..." />
      </div>
    );
  }

  // 未认证，重定向到登录页
  if (!isAuthenticated) {
    return (
      <Navigate 
        to={fallbackPath} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // 检查权限
  if (requiredPermission && !checkPermission(requiredPermission)) {
    return (
      <Navigate 
        to="/403" 
        state={{ 
          from: location.pathname,
          requiredPermission 
        }} 
        replace 
      />
    );
  }

  // 检查角色
  if (requiredRole && !checkRole(requiredRole)) {
    return (
      <Navigate 
        to="/403" 
        state={{ 
          from: location.pathname,
          requiredRole 
        }} 
        replace 
      />
    );
  }

  // 通过所有检查，渲染子组件
  return <>{children}</>;
};

export default ProtectedRoute;