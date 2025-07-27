from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from app.models.user import UserRole

class Token(BaseModel):
    """令牌模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    scopes: List[str] = []

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    remember_me: bool = Field(False, description="记住我")
    captcha: Optional[str] = Field(None, description="验证码")

class UserRegister(BaseModel):
    """用户注册模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认密码")
    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, description="手机号")
    employee_id: Optional[str] = Field(None, description="工号")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    
    def validate_passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v

class PasswordChange(BaseModel):
    """密码修改模型"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认新密码")
    
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v

class PasswordReset(BaseModel):
    """密码重置模型"""
    email: EmailStr = Field(..., description="邮箱")
    reset_code: str = Field(..., description="重置码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认新密码")
    
    def validate_passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码不匹配')
        return v

class UserInfo(BaseModel):
    """用户信息模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: str = Field(..., description="姓名")
    employee_id: Optional[str] = Field(None, description="工号")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    role: UserRole = Field(..., description="角色")
    workshop: Optional[str] = Field(None, description="车间")
    avatar: Optional[str] = Field(None, description="头像")
    permissions: List[str] = Field([], description="权限列表")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

class UserProfile(BaseModel):
    """用户档案模型"""
    full_name: str = Field(..., min_length=2, max_length=100, description="姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    department: Optional[str] = Field(None, description="部门")
    position: Optional[str] = Field(None, description="职位")
    workshop: Optional[str] = Field(None, description="车间")
    address: Optional[str] = Field(None, description="地址")
    emergency_contact: Optional[str] = Field(None, description="紧急联系人")
    emergency_phone: Optional[str] = Field(None, description="紧急联系电话")
    avatar: Optional[str] = Field(None, description="头像")
    timezone: Optional[str] = Field("Asia/Shanghai", description="时区")
    language: Optional[str] = Field("zh-CN", description="语言")
    theme: Optional[str] = Field("light", description="主题")

class LoginHistory(BaseModel):
    """登录历史模型"""
    id: int = Field(..., description="记录ID")
    login_time: datetime = Field(..., description="登录时间")
    logout_time: Optional[datetime] = Field(None, description="登出时间")
    duration: Optional[int] = Field(None, description="在线时长(分钟)")
    login_result: str = Field(..., description="登录结果")
    ip_address: Optional[str] = Field(None, description="IP地址")
    device_type: Optional[str] = Field(None, description="设备类型")
    browser: Optional[str] = Field(None, description="浏览器")
    location: Optional[str] = Field(None, description="登录地点")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    login_time: datetime = Field(..., description="登录时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    ip_address: Optional[str] = Field(None, description="IP地址")
    device_type: Optional[str] = Field(None, description="设备类型")
    browser: Optional[str] = Field(None, description="浏览器")
    is_active: bool = Field(..., description="是否活跃")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }

class PermissionInfo(BaseModel):
    """权限信息模型"""
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    description: Optional[str] = Field(None, description="权限描述")
    category: str = Field(..., description="权限分类")
    is_granted: bool = Field(..., description="是否已授权")

class RoleInfo(BaseModel):
    """角色信息模型"""
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    permissions: List[str] = Field([], description="权限列表")
    user_count: int = Field(0, description="用户数量")

class CaptchaResponse(BaseModel):
    """验证码响应模型"""
    captcha_id: str = Field(..., description="验证码ID")
    captcha_image: str = Field(..., description="验证码图片(base64)")
    expires_in: int = Field(..., description="过期时间(秒)")

class EmailVerification(BaseModel):
    """邮箱验证模型"""
    email: EmailStr = Field(..., description="邮箱")
    verification_code: str = Field(..., description="验证码")

class PhoneVerification(BaseModel):
    """手机验证模型"""
    phone: str = Field(..., description="手机号")
    verification_code: str = Field(..., description="验证码")

class TwoFactorAuth(BaseModel):
    """双因子认证模型"""
    secret_key: str = Field(..., description="密钥")
    qr_code: str = Field(..., description="二维码")
    backup_codes: List[str] = Field(..., description="备用码")

class TwoFactorVerify(BaseModel):
    """双因子验证模型"""
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    backup_code: Optional[str] = Field(None, description="备用码")