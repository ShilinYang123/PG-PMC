"""微信用户认证服务

实现企业微信用户认证功能，包括：
- 用户身份验证
- OAuth2.0授权
- 用户信息获取
- 权限管理
- 会话管理
"""

import requests
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import asyncio
import jwt
from urllib.parse import urlencode, quote


class UserRole(Enum):
    """用户角色"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = "admin"  # 管理员
    MANAGER = "manager"  # 经理
    SUPERVISOR = "supervisor"  # 主管
    OPERATOR = "operator"  # 操作员
    VIEWER = "viewer"  # 查看者
    GUEST = "guest"  # 访客


class Permission(Enum):
    """权限枚举"""
    # 系统管理
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    
    # 用户管理
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_VIEW = "user:view"
    
    # 生产管理
    PRODUCTION_CREATE = "production:create"
    PRODUCTION_UPDATE = "production:update"
    PRODUCTION_DELETE = "production:delete"
    PRODUCTION_VIEW = "production:view"
    
    # 订单管理
    ORDER_CREATE = "order:create"
    ORDER_UPDATE = "order:update"
    ORDER_DELETE = "order:delete"
    ORDER_VIEW = "order:view"
    
    # 通知管理
    NOTIFICATION_SEND = "notification:send"
    NOTIFICATION_CONFIG = "notification:config"
    NOTIFICATION_VIEW = "notification:view"


@dataclass
class UserInfo:
    """用户信息"""
    user_id: str
    name: str
    avatar: str
    email: str
    mobile: str
    department: str
    position: str
    role: UserRole
    permissions: List[Permission]
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class AuthSession:
    """认证会话"""
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


@dataclass
class AuthCode:
    """授权码"""
    code: str
    user_id: str
    redirect_uri: str
    scope: str
    expires_at: datetime
    used: bool = False


class WeChatAuthService:
    """微信认证服务"""
    
    def __init__(self, corp_id: str, corp_secret: str, agent_id: str, 
                 app_secret: str = None, redirect_uri: str = None):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.app_secret = app_secret or secrets.token_urlsafe(32)
        self.redirect_uri = redirect_uri or "http://localhost:8000/auth/callback"
        
        self.access_token = None
        self.token_expires_at = None
        
        # 存储
        self.users: Dict[str, UserInfo] = {}
        self.sessions: Dict[str, AuthSession] = {}
        self.auth_codes: Dict[str, AuthCode] = {}
        
        # 角色权限映射
        self.role_permissions = {
            UserRole.SUPER_ADMIN: list(Permission),
            UserRole.ADMIN: [
                Permission.SYSTEM_CONFIG,
                Permission.USER_CREATE, Permission.USER_UPDATE, Permission.USER_VIEW,
                Permission.PRODUCTION_CREATE, Permission.PRODUCTION_UPDATE, Permission.PRODUCTION_VIEW,
                Permission.ORDER_CREATE, Permission.ORDER_UPDATE, Permission.ORDER_VIEW,
                Permission.NOTIFICATION_SEND, Permission.NOTIFICATION_CONFIG, Permission.NOTIFICATION_VIEW
            ],
            UserRole.MANAGER: [
                Permission.USER_VIEW,
                Permission.PRODUCTION_CREATE, Permission.PRODUCTION_UPDATE, Permission.PRODUCTION_VIEW,
                Permission.ORDER_CREATE, Permission.ORDER_UPDATE, Permission.ORDER_VIEW,
                Permission.NOTIFICATION_SEND, Permission.NOTIFICATION_VIEW
            ],
            UserRole.SUPERVISOR: [
                Permission.PRODUCTION_UPDATE, Permission.PRODUCTION_VIEW,
                Permission.ORDER_UPDATE, Permission.ORDER_VIEW,
                Permission.NOTIFICATION_SEND, Permission.NOTIFICATION_VIEW
            ],
            UserRole.OPERATOR: [
                Permission.PRODUCTION_VIEW,
                Permission.ORDER_VIEW,
                Permission.NOTIFICATION_VIEW
            ],
            UserRole.VIEWER: [
                Permission.PRODUCTION_VIEW,
                Permission.ORDER_VIEW,
                Permission.NOTIFICATION_VIEW
            ],
            UserRole.GUEST: [
                Permission.NOTIFICATION_VIEW
            ]
        }
        
        self._init_default_users()
    
    def _init_default_users(self):
        """初始化默认用户"""
        default_users = [
            UserInfo(
                user_id="admin",
                name="系统管理员",
                avatar="",
                email="admin@company.com",
                mobile="13800000000",
                department="信息技术部",
                position="系统管理员",
                role=UserRole.SUPER_ADMIN,
                permissions=self.role_permissions[UserRole.SUPER_ADMIN],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            UserInfo(
                user_id="pmc_manager",
                name="PMC经理",
                avatar="",
                email="pmc@company.com",
                mobile="13800000001",
                department="生产管理部",
                position="PMC经理",
                role=UserRole.MANAGER,
                permissions=self.role_permissions[UserRole.MANAGER],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        for user in default_users:
            self.users[user.user_id] = user
        
        logger.info(f"初始化了 {len(default_users)} 个默认用户")
    
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        if (self.access_token and 
            self.token_expires_at and 
            datetime.now() < self.token_expires_at):
            return self.access_token
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data["access_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 600)
                logger.info("微信访问令牌获取成功")
                return self.access_token
            else:
                logger.error(f"获取微信访问令牌失败: {data}")
                raise Exception(f"获取访问令牌失败: {data.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"获取微信访问令牌异常: {e}")
            raise
    
    def generate_auth_url(self, state: str = None) -> str:
        """生成授权URL"""
        state = state or secrets.token_urlsafe(16)
        
        params = {
            "appid": self.corp_id,
            "redirect_uri": quote(self.redirect_uri),
            "response_type": "code",
            "scope": "snsapi_base",
            "state": state
        }
        
        auth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?{urlencode(params)}#wechat_redirect"
        logger.info(f"生成授权URL: {auth_url}")
        return auth_url
    
    async def handle_auth_callback(self, code: str, state: str) -> Tuple[bool, Optional[str], Optional[UserInfo]]:
        """处理授权回调"""
        try:
            # 通过code获取用户信息
            user_info = await self._get_user_info_by_code(code)
            if not user_info:
                return False, "获取用户信息失败", None
            
            # 检查用户是否存在
            if user_info.user_id not in self.users:
                # 自动注册新用户
                user_info.role = UserRole.VIEWER  # 默认角色
                user_info.permissions = self.role_permissions[UserRole.VIEWER]
                user_info.created_at = datetime.now()
                user_info.updated_at = datetime.now()
                self.users[user_info.user_id] = user_info
                logger.info(f"自动注册新用户: {user_info.user_id} - {user_info.name}")
            else:
                # 更新现有用户信息
                existing_user = self.users[user_info.user_id]
                existing_user.name = user_info.name
                existing_user.avatar = user_info.avatar
                existing_user.email = user_info.email
                existing_user.mobile = user_info.mobile
                existing_user.department = user_info.department
                existing_user.position = user_info.position
                existing_user.last_login = datetime.now()
                existing_user.updated_at = datetime.now()
                user_info = existing_user
            
            # 生成会话
            session = await self._create_session(user_info.user_id)
            
            logger.info(f"用户认证成功: {user_info.user_id} - {user_info.name}")
            return True, session.access_token, user_info
            
        except Exception as e:
            logger.error(f"处理授权回调异常: {e}")
            return False, str(e), None
    
    async def _get_user_info_by_code(self, code: str) -> Optional[UserInfo]:
        """通过授权码获取用户信息"""
        try:
            # 1. 获取access_token
            access_token = await self.get_access_token()
            
            # 2. 通过code获取用户ID
            url = f"https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo"
            params = {
                "access_token": access_token,
                "code": code
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") != 0:
                logger.error(f"获取用户ID失败: {data}")
                return None
            
            user_id = data.get("UserId")
            if not user_id:
                logger.error("未获取到用户ID")
                return None
            
            # 3. 获取用户详细信息
            user_detail = await self._get_user_detail(user_id)
            return user_detail
            
        except Exception as e:
            logger.error(f"通过授权码获取用户信息异常: {e}")
            return None
    
    async def _get_user_detail(self, user_id: str) -> Optional[UserInfo]:
        """获取用户详细信息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get"
            params = {
                "access_token": access_token,
                "userid": user_id
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") != 0:
                logger.error(f"获取用户详细信息失败: {data}")
                return None
            
            # 构建用户信息
            user_info = UserInfo(
                user_id=user_id,
                name=data.get("name", ""),
                avatar=data.get("avatar", ""),
                email=data.get("email", ""),
                mobile=data.get("mobile", ""),
                department=self._get_department_name(data.get("department", [])),
                position=data.get("position", ""),
                role=UserRole.VIEWER,  # 默认角色
                permissions=[]
            )
            
            return user_info
            
        except Exception as e:
            logger.error(f"获取用户详细信息异常: {e}")
            return None
    
    def _get_department_name(self, department_ids: List[int]) -> str:
        """获取部门名称（简化实现）"""
        if not department_ids:
            return "未知部门"
        
        # 实际实现中应该调用企业微信API获取部门信息
        dept_map = {
            1: "总经理办公室",
            2: "生产管理部",
            3: "质量管理部",
            4: "采购部",
            5: "销售部",
            6: "财务部",
            7: "人力资源部",
            8: "信息技术部"
        }
        
        return dept_map.get(department_ids[0], "未知部门")
    
    async def _create_session(self, user_id: str, ip_address: str = "", 
                             user_agent: str = "") -> AuthSession:
        """创建用户会话"""
        session_id = secrets.token_urlsafe(32)
        access_token = self._generate_jwt_token(user_id, "access")
        refresh_token = self._generate_jwt_token(user_id, "refresh")
        
        session = AuthSession(
            session_id=session_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now() + timedelta(hours=24),
            created_at=datetime.now(),
            last_activity=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        logger.info(f"创建用户会话: {user_id} - {session_id}")
        return session
    
    def _generate_jwt_token(self, user_id: str, token_type: str) -> str:
        """生成JWT令牌"""
        now = datetime.now()
        
        if token_type == "access":
            exp = now + timedelta(hours=2)
        else:  # refresh
            exp = now + timedelta(days=7)
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "iss": "pmc-system"
        }
        
        return jwt.encode(payload, self.app_secret, algorithm="HS256")
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.app_secret, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            # 检查用户是否存在且活跃
            if user_id not in self.users or not self.users[user_id].is_active:
                return False, "用户不存在或已禁用", None
            
            return True, None, payload
            
        except jwt.ExpiredSignatureError:
            return False, "令牌已过期", None
        except jwt.InvalidTokenError:
            return False, "无效令牌", None
        except Exception as e:
            logger.error(f"验证令牌异常: {e}")
            return False, "令牌验证失败", None
    
    def refresh_token(self, refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """刷新访问令牌"""
        valid, error, payload = self.verify_token(refresh_token)
        
        if not valid:
            return False, error, None
        
        if payload.get("type") != "refresh":
            return False, "无效的刷新令牌", None
        
        user_id = payload.get("user_id")
        new_access_token = self._generate_jwt_token(user_id, "access")
        
        logger.info(f"刷新访问令牌: {user_id}")
        return True, None, new_access_token
    
    def logout(self, session_id: str) -> bool:
        """用户登出"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            logger.info(f"用户登出: {self.sessions[session_id].user_id}")
            return True
        return False
    
    def get_user_info(self, user_id: str) -> Optional[UserInfo]:
        """获取用户信息"""
        return self.users.get(user_id)
    
    def update_user_role(self, user_id: str, role: UserRole) -> bool:
        """更新用户角色"""
        if user_id in self.users:
            self.users[user_id].role = role
            self.users[user_id].permissions = self.role_permissions[role]
            self.users[user_id].updated_at = datetime.now()
            logger.info(f"更新用户角色: {user_id} -> {role.value}")
            return True
        return False
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """检查用户权限"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        
        return permission in user.permissions
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """获取用户权限列表"""
        user = self.users.get(user_id)
        return user.permissions if user else []
    
    def get_active_sessions(self, user_id: str = None) -> List[AuthSession]:
        """获取活跃会话"""
        sessions = [s for s in self.sessions.values() if s.is_active]
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        return sessions
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.expires_at < now:
                session.is_active = False
                expired_sessions.append(session_id)
        
        logger.info(f"清理过期会话: {len(expired_sessions)} 个")
        return len(expired_sessions)
    
    def get_auth_statistics(self) -> Dict:
        """获取认证统计信息"""
        total_users = len(self.users)
        active_users = len([u for u in self.users.values() if u.is_active])
        active_sessions = len([s for s in self.sessions.values() if s.is_active])
        
        role_stats = {}
        for user in self.users.values():
            if user.is_active:
                role = user.role.value
                role_stats[role] = role_stats.get(role, 0) + 1
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'active_sessions': active_sessions,
            'role_distribution': role_stats,
            'total_sessions': len(self.sessions)
        }