from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "管理员"
    MANAGER = "经理"
    SUPERVISOR = "主管"
    OPERATOR = "操作员"
    VIEWER = "查看者"

class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    ACTIVE = "激活"
    INACTIVE = "未激活"
    SUSPENDED = "暂停"
    LOCKED = "锁定"

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, comment="邮箱")
    phone = Column(String(20), comment="手机号")
    
    # 密码相关
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    password_changed_at = Column(DateTime, comment="密码修改时间")
    password_expires_at = Column(DateTime, comment="密码过期时间")
    
    # 个人信息
    full_name = Column(String(100), nullable=False, comment="姓名")
    employee_id = Column(String(50), unique=True, comment="工号")
    department = Column(String(100), comment="部门")
    position = Column(String(100), comment="职位")
    
    # 权限信息
    role = Column(Enum(UserRole), default=UserRole.VIEWER, comment="角色")
    permissions = Column(Text, comment="权限列表(JSON)")
    
    # 状态信息
    status = Column(Enum(UserStatus), default=UserStatus.INACTIVE, comment="状态")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    
    # 登录信息
    last_login_at = Column(DateTime, comment="最后登录时间")
    last_login_ip = Column(String(50), comment="最后登录IP")
    login_count = Column(Integer, default=0, comment="登录次数")
    failed_login_count = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(DateTime, comment="锁定到期时间")
    
    # 工作信息
    workshop = Column(String(100), comment="所属车间")
    team = Column(String(100), comment="所属班组")
    supervisor_id = Column(Integer, comment="上级主管ID")
    
    # 联系信息
    address = Column(String(255), comment="地址")
    emergency_contact = Column(String(100), comment="紧急联系人")
    emergency_phone = Column(String(20), comment="紧急联系电话")
    
    # 系统信息
    avatar = Column(String(255), comment="头像URL")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    language = Column(String(10), default="zh-CN", comment="语言")
    theme = Column(String(20), default="light", comment="主题")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    def __repr__(self):
        return f"<User(username='{self.username}', full_name='{self.full_name}', role='{self.role}')>"
    
    def check_password(self, password: str) -> bool:
        """检查密码"""
        # 这里应该使用密码哈希库进行验证
        # 例如: return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
        pass
    
    def set_password(self, password: str):
        """设置密码"""
        # 这里应该使用密码哈希库进行加密
        # 例如: self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        pass
    
    def is_password_expired(self) -> bool:
        """检查密码是否过期"""
        if self.password_expires_at:
            from datetime import datetime
            return datetime.now() > self.password_expires_at
        return False
    
    def is_account_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until:
            from datetime import datetime
            return datetime.now() < self.locked_until
        return self.status == UserStatus.LOCKED
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        if self.is_superuser:
            return True
        
        if self.permissions:
            import json
            try:
                perms = json.loads(self.permissions)
                return permission in perms
            except:
                return False
        return False
    
    def get_permissions(self) -> list:
        """获取权限列表"""
        if self.permissions:
            import json
            try:
                return json.loads(self.permissions)
            except:
                return []
        return []
    
    def set_permissions(self, permissions: list):
        """设置权限列表"""
        import json
        self.permissions = json.dumps(permissions)

class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户信息
    user_id = Column(Integer, nullable=False, comment="用户ID")
    username = Column(String(50), nullable=False, comment="用户名")
    
    # 会话信息
    session_id = Column(String(255), unique=True, nullable=False, comment="会话ID")
    token = Column(String(500), comment="访问令牌")
    refresh_token = Column(String(500), comment="刷新令牌")
    
    # 登录信息
    login_time = Column(DateTime, nullable=False, comment="登录时间")
    last_activity = Column(DateTime, comment="最后活动时间")
    expires_at = Column(DateTime, comment="过期时间")
    
    # 设备信息
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    device_type = Column(String(50), comment="设备类型")
    browser = Column(String(100), comment="浏览器")
    os = Column(String(100), comment="操作系统")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    logout_time = Column(DateTime, comment="登出时间")
    logout_reason = Column(String(100), comment="登出原因")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, session_id='{self.session_id}', active={self.is_active})>"
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        if self.expires_at:
            from datetime import datetime
            return datetime.now() > self.expires_at
        return False

class UserLoginLog(Base):
    """用户登录日志模型"""
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户信息
    user_id = Column(Integer, comment="用户ID")
    username = Column(String(50), nullable=False, comment="用户名")
    
    # 登录信息
    login_time = Column(DateTime, nullable=False, comment="登录时间")
    logout_time = Column(DateTime, comment="登出时间")
    duration = Column(Integer, comment="在线时长(分钟)")
    
    # 结果信息
    success = Column(Boolean, default=True, comment="是否成功")
    login_result = Column(String(20), nullable=False, comment="登录结果")
    failure_reason = Column(String(100), comment="失败原因")
    
    # 设备信息
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(String(500), comment="用户代理")
    device_type = Column(String(50), comment="设备类型")
    browser = Column(String(100), comment="浏览器")
    os = Column(String(100), comment="操作系统")
    location = Column(String(100), comment="登录地点")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<UserLoginLog(username='{self.username}', login_time='{self.login_time}', result='{self.login_result}')>"