from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from app.models.user import UserRole, UserStatus
from app.schemas.common import QueryParams

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: UserRole = UserRole.OPERATOR
    workshop: Optional[str] = None
    team: Optional[str] = None
    supervisor_id: Optional[int] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    avatar: Optional[str] = None
    timezone: Optional[str] = "Asia/Shanghai"
    language: Optional[str] = "zh-CN"
    theme: Optional[str] = "light"
    remark: Optional[str] = None

class UserCreate(UserBase):
    """创建用户模型"""
    password: str
    status: Optional[UserStatus] = UserStatus.ACTIVE
    is_active: Optional[bool] = True
    permissions: Optional[List[str]] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名长度不能少于3位')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    workshop: Optional[str] = None
    team: Optional[str] = None
    supervisor_id: Optional[int] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    avatar: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None
    permissions: Optional[List[str]] = None
    remark: Optional[str] = None

class UserDetail(UserBase):
    """用户详情模型"""
    id: int
    status: UserStatus
    is_active: bool
    permissions: Optional[List[str]] = None
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    failed_login_count: int = 0
    password_changed_at: Optional[datetime] = None
    password_expires_at: Optional[datetime] = None
    account_locked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserQuery(QueryParams):
    """用户查询参数"""
    keyword: Optional[str] = None  # 关键词搜索（用户名、姓名、邮箱、工号）
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = None
    workshop: Optional[str] = None
    is_active: Optional[bool] = None
    supervisor_id: Optional[int] = None
    
class UserSummary(BaseModel):
    """用户摘要信息"""
    id: int
    username: str
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: UserRole
    status: UserStatus
    is_active: bool
    avatar: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """用户统计信息"""
    total_users: int
    active_users: int
    inactive_users: int
    locked_users: int
    role_distribution: dict
    department_distribution: dict
    workshop_distribution: dict
    recent_logins: int  # 最近7天登录用户数
    new_users: int  # 最近30天新增用户数

class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v

class PasswordResetRequest(BaseModel):
    """重置密码请求"""
    user_id: int
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        return v

class UserStatusUpdate(BaseModel):
    """用户状态更新"""
    status: UserStatus
    is_active: Optional[bool] = None
    remark: Optional[str] = None

class UserRoleUpdate(BaseModel):
    """用户角色更新"""
    role: UserRole
    permissions: Optional[List[str]] = None
    remark: Optional[str] = None

class UserBatchOperation(BaseModel):
    """用户批量操作"""
    user_ids: List[int]
    operation: str  # 'activate', 'deactivate', 'lock', 'unlock', 'delete'
    remark: Optional[str] = None

class UserImport(BaseModel):
    """用户导入"""
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str = "OPERATOR"
    workshop: Optional[str] = None
    team: Optional[str] = None
    password: Optional[str] = None  # 如果为空，使用默认密码
    
    @validator('role')
    def validate_role(cls, v):
        try:
            UserRole(v)
        except ValueError:
            raise ValueError(f'无效的角色: {v}')
        return v

class UserExport(BaseModel):
    """用户导出"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str
    status: str
    is_active: bool
    workshop: Optional[str] = None
    team: Optional[str] = None
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DepartmentInfo(BaseModel):
    """部门信息"""
    name: str
    user_count: int
    active_count: int
    manager: Optional[str] = None

class WorkshopInfo(BaseModel):
    """车间信息"""
    name: str
    user_count: int
    active_count: int
    supervisor: Optional[str] = None
    department: Optional[str] = None

class TeamInfo(BaseModel):
    """班组信息"""
    name: str
    user_count: int
    active_count: int
    leader: Optional[str] = None
    workshop: Optional[str] = None

class UserHierarchy(BaseModel):
    """用户层级关系"""
    user: UserSummary
    subordinates: List['UserHierarchy'] = []
    
    class Config:
        from_attributes = True

# 解决前向引用问题
UserHierarchy.model_rebuild()