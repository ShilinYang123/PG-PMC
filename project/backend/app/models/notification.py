from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class NotificationType(enum.Enum):
    """通知类型枚举"""
    SYSTEM = "system"  # 系统通知
    EMAIL = "email"    # 邮件通知
    WECHAT = "wechat"  # 微信通知
    SMS = "sms"        # 短信通知

class NotificationPriority(enum.Enum):
    """通知优先级枚举"""
    LOW = "low"        # 低优先级
    NORMAL = "normal"  # 普通优先级
    HIGH = "high"      # 高优先级
    URGENT = "urgent"  # 紧急

class NotificationStatus(enum.Enum):
    """通知状态枚举"""
    PENDING = "pending"    # 待发送
    SENDING = "sending"    # 发送中
    SENT = "sent"          # 已发送
    FAILED = "failed"      # 发送失败
    READ = "read"          # 已读

class Notification(Base):
    """通知模型"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    notification_type = Column(Enum(NotificationType), nullable=False, comment="通知类型")
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, comment="优先级")
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, comment="状态")
    
    # 发送相关信息
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="发送者ID")
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="接收者ID")
    recipient_email = Column(String(100), nullable=True, comment="接收者邮箱")
    recipient_phone = Column(String(20), nullable=True, comment="接收者手机号")
    recipient_wechat = Column(String(100), nullable=True, comment="接收者微信号")
    
    # 业务关联
    related_type = Column(String(50), nullable=True, comment="关联业务类型")
    related_id = Column(Integer, nullable=True, comment="关联业务ID")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    scheduled_at = Column(DateTime, nullable=True, comment="计划发送时间")
    sent_at = Column(DateTime, nullable=True, comment="实际发送时间")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retry = Column(Integer, default=3, comment="最大重试次数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关联关系
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_notifications")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_notifications")

class NotificationTemplate(Base):
    """通知模板模型"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="模板名称")
    title_template = Column(String(200), nullable=False, comment="标题模板")
    content_template = Column(Text, nullable=False, comment="内容模板")
    notification_type = Column(Enum(NotificationType), nullable=False, comment="通知类型")
    
    # 模板变量说明
    variables = Column(Text, nullable=True, comment="模板变量说明(JSON格式)")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

class NotificationRule(Base):
    """通知规则模型"""
    __tablename__ = "notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    
    # 触发条件
    trigger_event = Column(String(100), nullable=False, comment="触发事件")
    trigger_conditions = Column(Text, nullable=True, comment="触发条件(JSON格式)")
    
    # 通知配置
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=False, comment="模板ID")
    notification_types = Column(String(200), nullable=False, comment="通知类型列表")
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL, comment="优先级")
    
    # 接收者配置
    recipient_rules = Column(Text, nullable=False, comment="接收者规则(JSON格式)")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联关系
    template = relationship("NotificationTemplate", back_populates="rules")

# 更新关联关系
NotificationTemplate.rules = relationship("NotificationRule", back_populates="template")