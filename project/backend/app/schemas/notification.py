from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    """通知类型"""
    SYSTEM = "system"
    EMAIL = "email"
    WECHAT = "wechat"
    SMS = "sms"

class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(str, Enum):
    """通知状态"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

# 通知基础模式
class NotificationBase(BaseModel):
    """通知基础模式"""
    title: str = Field(..., max_length=200, description="通知标题")
    content: str = Field(..., description="通知内容")
    notification_type: NotificationType = Field(..., description="通知类型")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="优先级")
    recipient_id: int = Field(..., description="接收者ID")
    recipient_email: Optional[str] = Field(None, max_length=100, description="接收者邮箱")
    recipient_phone: Optional[str] = Field(None, max_length=20, description="接收者手机号")
    recipient_wechat: Optional[str] = Field(None, max_length=100, description="接收者微信号")
    related_type: Optional[str] = Field(None, max_length=50, description="关联业务类型")
    related_id: Optional[int] = Field(None, description="关联业务ID")
    scheduled_at: Optional[datetime] = Field(None, description="计划发送时间")

class NotificationCreate(NotificationBase):
    """创建通知模式"""
    sender_id: Optional[int] = Field(None, description="发送者ID")

class NotificationUpdate(BaseModel):
    """更新通知模式"""
    title: Optional[str] = Field(None, max_length=200, description="通知标题")
    content: Optional[str] = Field(None, description="通知内容")
    status: Optional[NotificationStatus] = Field(None, description="状态")
    read_at: Optional[datetime] = Field(None, description="阅读时间")

class NotificationResponse(NotificationBase):
    """通知响应模式"""
    id: int
    status: NotificationStatus
    sender_id: Optional[int]
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    retry_count: int
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

# 通知模板模式
class NotificationTemplateBase(BaseModel):
    """通知模板基础模式"""
    name: str = Field(..., max_length=100, description="模板名称")
    title_template: str = Field(..., max_length=200, description="标题模板")
    content_template: str = Field(..., description="内容模板")
    notification_type: NotificationType = Field(..., description="通知类型")
    variables: Optional[str] = Field(None, description="模板变量说明")

class NotificationTemplateCreate(NotificationTemplateBase):
    """创建通知模板模式"""
    pass

class NotificationTemplateUpdate(BaseModel):
    """更新通知模板模式"""
    name: Optional[str] = Field(None, max_length=100, description="模板名称")
    title_template: Optional[str] = Field(None, max_length=200, description="标题模板")
    content_template: Optional[str] = Field(None, description="内容模板")
    variables: Optional[str] = Field(None, description="模板变量说明")
    is_active: Optional[bool] = Field(None, description="是否启用")

class NotificationTemplateResponse(NotificationTemplateBase):
    """通知模板响应模式"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 通知规则模式
class NotificationRuleBase(BaseModel):
    """通知规则基础模式"""
    name: str = Field(..., max_length=100, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    trigger_event: str = Field(..., max_length=100, description="触发事件")
    trigger_conditions: Optional[str] = Field(None, description="触发条件")
    template_id: int = Field(..., description="模板ID")
    notification_types: str = Field(..., max_length=200, description="通知类型列表")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="优先级")
    recipient_rules: str = Field(..., description="接收者规则")

class NotificationRuleCreate(NotificationRuleBase):
    """创建通知规则模式"""
    pass

class NotificationRuleUpdate(BaseModel):
    """更新通知规则模式"""
    name: Optional[str] = Field(None, max_length=100, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    trigger_conditions: Optional[str] = Field(None, description="触发条件")
    notification_types: Optional[str] = Field(None, max_length=200, description="通知类型列表")
    priority: Optional[NotificationPriority] = Field(None, description="优先级")
    recipient_rules: Optional[str] = Field(None, description="接收者规则")
    is_active: Optional[bool] = Field(None, description="是否启用")

class NotificationRuleResponse(NotificationRuleBase):
    """通知规则响应模式"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 批量发送模式
class BatchNotificationCreate(BaseModel):
    """批量创建通知模式"""
    template_id: int = Field(..., description="模板ID")
    notification_types: List[NotificationType] = Field(..., description="通知类型列表")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="优先级")
    recipients: List[int] = Field(..., description="接收者ID列表")
    template_data: Dict[str, Any] = Field({}, description="模板数据")
    related_type: Optional[str] = Field(None, description="关联业务类型")
    related_id: Optional[int] = Field(None, description="关联业务ID")
    scheduled_at: Optional[datetime] = Field(None, description="计划发送时间")

# 通知统计模式
class NotificationStats(BaseModel):
    """通知统计模式"""
    total_count: int = Field(..., description="总数量")
    pending_count: int = Field(..., description="待发送数量")
    sent_count: int = Field(..., description="已发送数量")
    failed_count: int = Field(..., description="发送失败数量")
    read_count: int = Field(..., description="已读数量")
    unread_count: int = Field(..., description="未读数量")

# 通知查询模式
class NotificationQuery(BaseModel):
    """通知查询模式"""
    notification_type: Optional[NotificationType] = Field(None, description="通知类型")
    status: Optional[NotificationStatus] = Field(None, description="状态")
    priority: Optional[NotificationPriority] = Field(None, description="优先级")
    recipient_id: Optional[int] = Field(None, description="接收者ID")
    sender_id: Optional[int] = Field(None, description="发送者ID")
    related_type: Optional[str] = Field(None, description="关联业务类型")
    related_id: Optional[int] = Field(None, description="关联业务ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")