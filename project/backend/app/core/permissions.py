"""权限管理模块

定义系统中的各种权限和权限检查逻辑
"""

from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.user import User


class Permission(Enum):
    """权限枚举"""
    # 用户管理权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 订单管理权限
    ORDER_READ = "order:read"
    ORDER_WRITE = "order:write"
    ORDER_DELETE = "order:delete"
    
    # 生产计划权限
    PLAN_READ = "plan:read"
    PLAN_WRITE = "plan:write"
    PLAN_DELETE = "plan:delete"
    
    # 生产管理权限
    PRODUCTION_READ = "production:read"
    PRODUCTION_WRITE = "production:write"
    PRODUCTION_DELETE = "production:delete"
    
    # 物料管理权限
    MATERIAL_READ = "material:read"
    MATERIAL_WRITE = "material:write"
    MATERIAL_DELETE = "material:delete"
    
    # 进度管理权限
    PROGRESS_READ = "progress:read"
    PROGRESS_WRITE = "progress:write"
    PROGRESS_DELETE = "progress:delete"
    
    # 排产管理权限
    SCHEDULE_READ = "schedule:read"
    SCHEDULE_WRITE = "schedule:write"
    SCHEDULE_DELETE = "schedule:delete"
    
    # 报表权限
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    
    # 系统管理权限
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    
    # 通知权限
    NOTIFICATION_READ = "notification:read"
    NOTIFICATION_WRITE = "notification:write"
    NOTIFICATION_SEND = "notification:send"
    
    # 催办权限
    REMINDER_READ = "reminder:read"
    REMINDER_WRITE = "reminder:write"
    REMINDER_SEND = "reminder:send"


class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"  # 管理员
    MANAGER = "manager"  # 经理
    SUPERVISOR = "supervisor"  # 主管
    OPERATOR = "operator"  # 操作员
    VIEWER = "viewer"  # 查看者


# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        # 管理员拥有所有权限
        Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
        Permission.ORDER_READ, Permission.ORDER_WRITE, Permission.ORDER_DELETE,
        Permission.PLAN_READ, Permission.PLAN_WRITE, Permission.PLAN_DELETE,
        Permission.PRODUCTION_READ, Permission.PRODUCTION_WRITE, Permission.PRODUCTION_DELETE,
        Permission.MATERIAL_READ, Permission.MATERIAL_WRITE, Permission.MATERIAL_DELETE,
        Permission.PROGRESS_READ, Permission.PROGRESS_WRITE, Permission.PROGRESS_DELETE,
        Permission.SCHEDULE_READ, Permission.SCHEDULE_WRITE, Permission.SCHEDULE_DELETE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
        Permission.SYSTEM_ADMIN, Permission.SYSTEM_CONFIG,
        Permission.NOTIFICATION_READ, Permission.NOTIFICATION_WRITE, Permission.NOTIFICATION_SEND,
        Permission.REMINDER_READ, Permission.REMINDER_WRITE, Permission.REMINDER_SEND,
    ],
    Role.MANAGER: [
        # 经理权限
        Permission.USER_READ,
        Permission.ORDER_READ, Permission.ORDER_WRITE,
        Permission.PLAN_READ, Permission.PLAN_WRITE,
        Permission.PRODUCTION_READ, Permission.PRODUCTION_WRITE,
        Permission.MATERIAL_READ, Permission.MATERIAL_WRITE,
        Permission.PROGRESS_READ, Permission.PROGRESS_WRITE,
        Permission.SCHEDULE_READ, Permission.SCHEDULE_WRITE,
        Permission.REPORT_READ, Permission.REPORT_EXPORT,
        Permission.NOTIFICATION_READ, Permission.NOTIFICATION_WRITE, Permission.NOTIFICATION_SEND,
        Permission.REMINDER_READ, Permission.REMINDER_WRITE, Permission.REMINDER_SEND,
    ],
    Role.SUPERVISOR: [
        # 主管权限
        Permission.ORDER_READ, Permission.ORDER_WRITE,
        Permission.PLAN_READ, Permission.PLAN_WRITE,
        Permission.PRODUCTION_READ, Permission.PRODUCTION_WRITE,
        Permission.MATERIAL_READ,
        Permission.PROGRESS_READ, Permission.PROGRESS_WRITE,
        Permission.SCHEDULE_READ, Permission.SCHEDULE_WRITE,
        Permission.REPORT_READ,
        Permission.NOTIFICATION_READ, Permission.NOTIFICATION_WRITE,
        Permission.REMINDER_READ, Permission.REMINDER_WRITE,
    ],
    Role.OPERATOR: [
        # 操作员权限
        Permission.ORDER_READ,
        Permission.PLAN_READ,
        Permission.PRODUCTION_READ,
        Permission.MATERIAL_READ,
        Permission.PROGRESS_READ, Permission.PROGRESS_WRITE,
        Permission.SCHEDULE_READ,
        Permission.REPORT_READ,
        Permission.NOTIFICATION_READ,
        Permission.REMINDER_READ,
    ],
    Role.VIEWER: [
        # 查看者权限
        Permission.ORDER_READ,
        Permission.PLAN_READ,
        Permission.PRODUCTION_READ,
        Permission.MATERIAL_READ,
        Permission.PROGRESS_READ,
        Permission.SCHEDULE_READ,
        Permission.REPORT_READ,
        Permission.NOTIFICATION_READ,
        Permission.REMINDER_READ,
    ],
}


def get_user_permissions(user: User) -> List[Permission]:
    """获取用户权限列表"""
    if not user or not user.role:
        return []
    
    try:
        role = Role(user.role)
        return ROLE_PERMISSIONS.get(role, [])
    except ValueError:
        # 如果角色不在枚举中，返回空权限列表
        return []


def has_permission(user: User, permission: Permission) -> bool:
    """检查用户是否有指定权限"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def require_permission(permission: Permission):
    """权限装饰器，要求用户具有指定权限"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证用户"
                )
            
            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """权限装饰器，要求用户具有任一指定权限"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证用户"
                )
            
            user_permissions = get_user_permissions(current_user)
            if not any(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(permissions: List[Permission]):
    """权限装饰器，要求用户具有所有指定权限"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证用户"
                )
            
            user_permissions = get_user_permissions(current_user)
            if not all(perm in user_permissions for perm in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_resource_permission(user: User, resource_type: str, resource_id: Optional[int] = None, action: str = "read") -> bool:
    """检查用户对特定资源的权限"""
    # 构建权限字符串
    permission_str = f"{resource_type}:{action}"
    
    try:
        permission = Permission(permission_str)
        return has_permission(user, permission)
    except ValueError:
        # 如果权限不存在，默认拒绝
        return False


def is_admin(user: User) -> bool:
    """检查用户是否为管理员"""
    return user and user.role == Role.ADMIN.value


def is_manager_or_above(user: User) -> bool:
    """检查用户是否为经理或更高级别"""
    if not user or not user.role:
        return False
    
    manager_roles = [Role.ADMIN.value, Role.MANAGER.value]
    return user.role in manager_roles


def can_access_user_data(current_user: User, target_user_id: int) -> bool:
    """检查用户是否可以访问其他用户的数据"""
    # 管理员可以访问所有用户数据
    if is_admin(current_user):
        return True
    
    # 用户只能访问自己的数据
    return current_user.id == target_user_id