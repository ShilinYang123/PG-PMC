import React from 'react';
import { Result, Button } from 'antd';
import { useAuthStore } from '../../stores/authStore';

interface PermissionGuardProps {
  children: React.ReactNode;
  permission?: string;
  role?: string;
  permissions?: string[];
  roles?: string[];
  fallback?: React.ReactNode;
  showFallback?: boolean;
  requireAll?: boolean; // 是否需要满足所有权限/角色
}

const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  permission,
  role,
  permissions = [],
  roles = [],
  fallback,
  showFallback = true,
  requireAll = false
}) => {
  const { checkPermission, checkRole, user } = useAuthStore();

  // 检查单个权限
  const hasPermission = permission ? checkPermission(permission) : true;
  
  // 检查单个角色
  const hasRole = role ? checkRole(role) : true;
  
  // 检查多个权限
  const hasPermissions = permissions.length > 0 
    ? requireAll 
      ? permissions.every(p => checkPermission(p))
      : permissions.some(p => checkPermission(p))
    : true;
  
  // 检查多个角色
  const hasRoles = roles.length > 0
    ? requireAll
      ? roles.every(r => checkRole(r))
      : roles.some(r => checkRole(r))
    : true;

  // 综合权限检查
  const hasAccess = hasPermission && hasRole && hasPermissions && hasRoles;

  if (!hasAccess) {
    if (!showFallback) {
      return null;
    }

    if (fallback) {
      return <>{fallback}</>;
    }

    // 默认无权限提示
    return (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您没有权限访问此内容。"
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回
          </Button>
        }
      />
    );
  }

  return <>{children}</>;
};

// 权限检查Hook
export const usePermissionCheck = () => {
  const { checkPermission, checkRole } = useAuthStore();

  const hasPermission = (permission: string) => checkPermission(permission);
  
  const hasRole = (role: string) => checkRole(role);
  
  const hasAnyPermission = (permissions: string[]) => 
    permissions.some(p => checkPermission(p));
  
  const hasAllPermissions = (permissions: string[]) => 
    permissions.every(p => checkPermission(p));
  
  const hasAnyRole = (roles: string[]) => 
    roles.some(r => checkRole(r));
  
  const hasAllRoles = (roles: string[]) => 
    roles.every(r => checkRole(r));

  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    hasAllRoles
  };
};

// 权限按钮组件
interface PermissionButtonProps {
  permission?: string;
  role?: string;
  permissions?: string[];
  roles?: string[];
  requireAll?: boolean;
  children: React.ReactNode;
  [key: string]: any;
}

export const PermissionButton: React.FC<PermissionButtonProps> = ({
  permission,
  role,
  permissions = [],
  roles = [],
  requireAll = false,
  children,
  ...props
}) => {
  return (
    <PermissionGuard
      permission={permission}
      role={role}
      permissions={permissions}
      roles={roles}
      requireAll={requireAll}
      showFallback={false}
    >
      {React.cloneElement(children as React.ReactElement, props)}
    </PermissionGuard>
  );
};

// 权限文本组件
interface PermissionTextProps {
  permission?: string;
  role?: string;
  permissions?: string[];
  roles?: string[];
  requireAll?: boolean;
  children: React.ReactNode;
  placeholder?: string;
}

export const PermissionText: React.FC<PermissionTextProps> = ({
  permission,
  role,
  permissions = [],
  roles = [],
  requireAll = false,
  children,
  placeholder = '***'
}) => {
  return (
    <PermissionGuard
      permission={permission}
      role={role}
      permissions={permissions}
      roles={roles}
      requireAll={requireAll}
      showFallback={true}
      fallback={<span>{placeholder}</span>}
    >
      {children}
    </PermissionGuard>
  );
};

export default PermissionGuard;