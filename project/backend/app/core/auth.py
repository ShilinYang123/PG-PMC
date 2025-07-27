from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# 简单的认证模块，用于测试
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    获取当前用户（简化版本，用于测试）
    在实际项目中，这里应该验证JWT token并返回用户信息
    """
    # 简化的认证逻辑，仅用于测试
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 在实际项目中，这里应该解析和验证JWT token
    # 现在只是返回一个模拟的用户信息
    return {
        "id": "test_user_001",
        "username": "test_user",
        "email": "test@example.com",
        "role": "admin"
    }

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """
    获取当前活跃用户
    """
    # 在实际项目中，这里可以检查用户是否被禁用等
    return current_user

def require_admin(current_user: dict = Depends(get_current_active_user)):
    """
    要求管理员权限
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

def require_permissions(*permissions):
    """
    要求特定权限的装饰器
    """
    def permission_checker(current_user: dict = Depends(get_current_active_user)):
        # 简化的权限检查，实际项目中应该从数据库查询用户权限
        user_permissions = current_user.get("permissions", [])
        
        # 管理员拥有所有权限
        if current_user.get("role") == "admin":
            return current_user
            
        # 检查是否拥有所需权限
        for permission in permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}"
                )
        
        return current_user
    
    return permission_checker