#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统认证模块
提供JWT认证、用户验证等功能
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import json

from app.db.database import get_db
from app.models.user import User, UserSession, UserLoginLog, UserStatus
from .security import SecurityManager
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer()
security_manager = SecurityManager()


class AuthenticationError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户凭据
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 密码
        
    Returns:
        User: 验证成功返回用户对象，否则返回None
    """
    try:
        # 查找用户
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            logger.warning(f"用户不存在: {username}")
            return None
        
        # 检查账户状态
        if user.status != UserStatus.ACTIVE:
            logger.warning(f"用户账户未激活: {username}")
            return None
            
        if user.is_account_locked():
            logger.warning(f"用户账户被锁定: {username}")
            return None
        
        # 验证密码
        if not security_manager.verify_password(password, user.hashed_password):
            # 记录失败登录
            user.failed_login_count += 1
            if user.failed_login_count >= 5:  # 5次失败后锁定账户
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"用户账户因多次登录失败被锁定: {username}")
            db.commit()
            return None
        
        # 重置失败计数
        user.failed_login_count = 0
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        db.commit()
        
        logger.info(f"用户登录成功: {username}")
        return user
        
    except Exception as e:
        logger.error(f"用户认证失败: {str(e)}")
        return None


def create_user_session(db: Session, user: User, ip_address: str = None, user_agent: str = None) -> dict:
    """
    创建用户会话
    
    Args:
        db: 数据库会话
        user: 用户对象
        ip_address: IP地址
        user_agent: 用户代理
        
    Returns:
        dict: 包含访问令牌和刷新令牌的字典
    """
    try:
        # 创建JWT载荷
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value if user.role else "viewer",
            "permissions": user.get_permissions(),
            "is_superuser": user.is_superuser
        }
        
        # 生成令牌
        access_token = security_manager.create_access_token(token_data)
        refresh_token = security_manager.create_refresh_token({"sub": str(user.id)})
        
        # 创建会话记录
        session = UserSession(
            user_id=user.id,
            username=user.username,
            session_id=security_manager.generate_api_key(16),
            token=access_token,
            refresh_token=refresh_token,
            login_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        
        # 记录登录日志
        login_log = UserLoginLog(
            user_id=user.id,
            username=user.username,
            login_time=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        db.add(login_log)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        logger.error(f"创建用户会话失败: {str(e)}")
        db.rollback()
        raise AuthenticationError("会话创建失败")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    
    Args:
        credentials: HTTP Bearer认证凭据
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        AuthenticationError: 认证失败时抛出
    """
    try:
        # 验证JWT令牌
        payload = security_manager.verify_token(credentials.credentials)
        
        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("令牌中缺少用户ID")
        
        # 查询用户
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("用户不存在")
        
        # 检查用户状态
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError("用户账户未激活")
            
        if user.is_account_locked():
            raise AuthenticationError("用户账户被锁定")
        
        # 更新会话活动时间
        session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.token == credentials.credentials,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.last_activity = datetime.utcnow()
            db.commit()
        
        return user
        
    except JWTError as e:
        logger.warning(f"JWT验证失败: {str(e)}")
        raise AuthenticationError("无效的令牌")
    except Exception as e:
        logger.error(f"获取当前用户失败: {str(e)}")
        raise AuthenticationError("认证失败")


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 活跃用户对象
        
    Raises:
        AuthenticationError: 用户未激活时抛出
    """
    if not current_user.is_active:
        raise AuthenticationError("用户账户已被禁用")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    要求管理员权限
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        AuthorizationError: 权限不足时抛出
    """
    if not current_user.is_superuser:
        raise AuthorizationError("需要管理员权限")
    return current_user


def require_permissions(permissions: List[str]):
    """
    要求特定权限
    
    Args:
        permissions: 所需权限列表
        
    Returns:
        function: 权限检查装饰器
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # 超级用户拥有所有权限
        if current_user.is_superuser:
            return current_user
        
        # 检查用户权限
        user_permissions = current_user.get_permissions()
        
        for permission in permissions:
            if permission not in user_permissions:
                logger.warning(f"用户 {current_user.username} 缺少权限: {permission}")
                raise AuthorizationError(f"缺少权限: {permission}")
        
        return current_user
    
    return permission_checker


def require_role(roles: List[str]):
    """
    要求特定角色
    
    Args:
        roles: 所需角色列表
        
    Returns:
        function: 角色检查装饰器
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # 超级用户拥有所有角色权限
        if current_user.is_superuser:
            return current_user
        
        # 检查用户角色
        user_role = current_user.role.value if current_user.role else "viewer"
        
        if user_role not in roles:
            logger.warning(f"用户 {current_user.username} 角色不符: {user_role}")
            raise AuthorizationError(f"需要角色: {', '.join(roles)}")
        
        return current_user
    
    return role_checker


def logout_user(db: Session, user: User, token: str) -> bool:
    """
    用户登出
    
    Args:
        db: 数据库会话
        user: 用户对象
        token: 访问令牌
        
    Returns:
        bool: 登出是否成功
    """
    try:
        # 更新会话状态
        session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.token == token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            session.logout_time = datetime.utcnow()
            session.logout_reason = "用户主动登出"
        
        # 更新登录日志
        login_log = db.query(UserLoginLog).filter(
            UserLoginLog.user_id == user.id,
            UserLoginLog.logout_time.is_(None)
        ).order_by(UserLoginLog.login_time.desc()).first()
        
        if login_log:
            login_log.logout_time = datetime.utcnow()
        
        db.commit()
        logger.info(f"用户登出成功: {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"用户登出失败: {str(e)}")
        db.rollback()
        return False


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    刷新访问令牌
    
    Args:
        db: 数据库会话
        refresh_token: 刷新令牌
        
    Returns:
        dict: 新的令牌信息
        
    Raises:
        AuthenticationError: 刷新失败时抛出
    """
    try:
        # 验证刷新令牌
        payload = security_manager.verify_token(refresh_token, "refresh")
        
        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("刷新令牌中缺少用户ID")
        
        # 查询用户
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("用户不存在")
        
        # 检查用户状态
        if user.status != UserStatus.ACTIVE or not user.is_active:
            raise AuthenticationError("用户账户未激活")
        
        # 查找会话
        session = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise AuthenticationError("无效的刷新令牌")
        
        # 生成新的访问令牌
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value if user.role else "viewer",
            "permissions": user.get_permissions(),
            "is_superuser": user.is_superuser
        }
        
        new_access_token = security_manager.create_access_token(token_data)
        
        # 更新会话
        session.token = new_access_token
        session.last_activity = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        db.commit()
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except JWTError as e:
        logger.warning(f"刷新令牌验证失败: {str(e)}")
        raise AuthenticationError("无效的刷新令牌")
    except Exception as e:
        logger.error(f"刷新访问令牌失败: {str(e)}")
        raise AuthenticationError("令牌刷新失败")