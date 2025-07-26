#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统安全模块
提供JWT认证、密码加密、权限验证等安全功能
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from ..db.database import get_db
from ..models.user import User
from .logging import get_logger

logger = get_logger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer()


class SecurityManager:
    """
    安全管理器
    提供密码加密、JWT令牌管理等功能
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """
        生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希密码
        """
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT访问令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新令牌
        
        Args:
            data: 令牌载荷数据
            
        Returns:
            str: JWT刷新令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            token_type: 令牌类型（access/refresh）
            
        Returns:
            Dict[str, Any]: 令牌载荷
            
        Raises:
            HTTPException: 令牌无效时抛出异常
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"无效的令牌类型，期望: {token_type}"
                )
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌缺少过期时间"
                )
            
            if datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已过期"
                )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT验证失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )
    
    def generate_api_key(self, length: int = 32) -> str:
        """
        生成API密钥
        
        Args:
            length: 密钥长度
            
        Returns:
            str: API密钥
        """
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """
        哈希API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            str: 哈希后的API密钥
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """
        验证API密钥
        
        Args:
            api_key: 原始API密钥
            hashed_key: 哈希后的API密钥
            
        Returns:
            bool: 密钥是否正确
        """
        return self.hash_api_key(api_key) == hashed_key


# 全局安全管理器实例
security_manager = SecurityManager()


# 便捷函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return security_manager.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return security_manager.get_password_hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌"""
    return security_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """验证JWT令牌"""
    return security_manager.verify_token(token, token_type)


def generate_api_key(length: int = 32) -> str:
    """生成API密钥"""
    return security_manager.generate_api_key(length)


def hash_api_key(api_key: str) -> str:
    """哈希API密钥"""
    return security_manager.hash_api_key(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """验证API密钥"""
    return security_manager.verify_api_key(api_key, hashed_key)


# 依赖注入函数
def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    获取当前用户令牌载荷
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        Dict[str, Any]: 令牌载荷
    """
    return verify_token(credentials.credentials)


def get_current_user(db: Session = Depends(get_db), token_data: Dict[str, Any] = Depends(get_current_user_token)) -> User:
    """
    获取当前用户
    
    Args:
        db: 数据库会话
        token_data: 令牌数据
        
    Returns:
        User: 用户对象
        
    Raises:
        HTTPException: 用户不存在时抛出异常
    """
    user_id = token_data.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 活跃用户对象
        
    Raises:
        HTTPException: 用户未激活时抛出异常
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前超级用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 超级用户对象
        
    Raises:
        HTTPException: 用户不是超级用户时抛出异常
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


class PermissionChecker:
    """
    权限检查器
    用于检查用户权限
    """
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查用户权限
        
        Args:
            current_user: 当前用户
            
        Returns:
            User: 有权限的用户对象
            
        Raises:
            HTTPException: 权限不足时抛出异常
        """
        # 超级用户拥有所有权限
        if current_user.is_superuser:
            return current_user
        
        # 检查用户角色权限
        user_permissions = set()
        if current_user.role:
            user_permissions.update(current_user.role.permissions or [])
        
        # 检查是否拥有所需权限
        required_set = set(self.required_permissions)
        if not required_set.issubset(user_permissions):
            missing_permissions = required_set - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，缺少权限: {', '.join(missing_permissions)}"
            )
        
        return current_user


def require_permissions(*permissions: str):
    """
    权限要求装饰器
    
    Args:
        *permissions: 所需权限列表
        
    Returns:
        PermissionChecker: 权限检查器
    """
    return PermissionChecker(list(permissions))


class RoleChecker:
    """
    角色检查器
    用于检查用户角色
    """
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        检查用户角色
        
        Args:
            current_user: 当前用户
            
        Returns:
            User: 有角色的用户对象
            
        Raises:
            HTTPException: 角色不匹配时抛出异常
        """
        # 超级用户拥有所有角色
        if current_user.is_superuser:
            return current_user
        
        # 检查用户角色
        user_role = current_user.role.name if current_user.role else None
        if user_role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色不匹配，需要角色: {', '.join(self.required_roles)}"
            )
        
        return current_user


def require_roles(*roles: str):
    """
    角色要求装饰器
    
    Args:
        *roles: 所需角色列表
        
    Returns:
        RoleChecker: 角色检查器
    """
    return RoleChecker(list(roles))


# 常用权限常量
class Permissions:
    """权限常量"""
    
    # 用户管理
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 订单管理
    ORDER_READ = "order:read"
    ORDER_WRITE = "order:write"
    ORDER_DELETE = "order:delete"
    ORDER_APPROVE = "order:approve"
    
    # 生产计划
    PRODUCTION_READ = "production:read"
    PRODUCTION_WRITE = "production:write"
    PRODUCTION_DELETE = "production:delete"
    PRODUCTION_SCHEDULE = "production:schedule"
    
    # 物料管理
    MATERIAL_READ = "material:read"
    MATERIAL_WRITE = "material:write"
    MATERIAL_DELETE = "material:delete"
    MATERIAL_INVENTORY = "material:inventory"
    
    # 进度跟踪
    PROGRESS_READ = "progress:read"
    PROGRESS_WRITE = "progress:write"
    
    # 报表查看
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"
    
    # 系统管理
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOG = "system:log"
    SYSTEM_BACKUP = "system:backup"


# 常用角色常量
class Roles:
    """角色常量"""
    
    ADMIN = "admin"  # 管理员
    MANAGER = "manager"  # 经理
    OPERATOR = "operator"  # 操作员
    VIEWER = "viewer"  # 查看者
    GUEST = "guest"  # 访客


# 导出主要接口
__all__ = [
    'SecurityManager',
    'security_manager',
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'generate_api_key',
    'hash_api_key',
    'verify_api_key',
    'get_current_user_token',
    'get_current_user',
    'get_current_active_user',
    'get_current_superuser',
    'PermissionChecker',
    'require_permissions',
    'RoleChecker',
    'require_roles',
    'Permissions',
    'Roles'
]