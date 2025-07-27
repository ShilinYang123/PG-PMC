import React from 'react';
import { Result, Button } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import './index.css';

const Forbidden: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  
  const state = location.state as {
    from?: string;
    requiredPermission?: string;
    requiredRole?: string;
  } | null;

  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  const handleGoHome = () => {
    navigate('/');
  };

  const getSubTitle = () => {
    if (state?.requiredPermission) {
      return `您需要 "${state.requiredPermission}" 权限才能访问此页面。`;
    }
    if (state?.requiredRole) {
      return `您需要 "${state.requiredRole}" 角色才能访问此页面。`;
    }
    return '抱歉，您没有权限访问此页面。请联系管理员获取相应权限。';
  };

  return (
    <div className="forbidden-page">
      <Result
        status="403"
        title="403"
        subTitle={getSubTitle()}
        extra={
          <div className="forbidden-actions">
            <Button type="primary" onClick={handleGoHome}>
              返回首页
            </Button>
            <Button onClick={handleGoBack}>
              返回上页
            </Button>
          </div>
        }
      />
      
      {/* 调试信息（仅开发环境） */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-info">
          <h4>调试信息：</h4>
          <p>当前用户：{user?.username || '未登录'}</p>
          <p>用户角色：{user?.role || '无'}</p>
          <p>用户权限：{user?.permissions?.join(', ') || '无'}</p>
          <p>来源页面：{state?.from || '未知'}</p>
          <p>所需权限：{state?.requiredPermission || '未指定'}</p>
          <p>所需角色：{state?.requiredRole || '未指定'}</p>
        </div>
      )}
    </div>
  );
};

export default Forbidden;