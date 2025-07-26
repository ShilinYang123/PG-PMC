from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

from app.db.base_class import Base

class MessageType(enum.Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    FILE = "file"
    CARD = "card"

class MessageStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class WeChatMessage(Base):
    """
    微信消息模型
    """
    __tablename__ = "wechat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 消息内容
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # 发送信息
    recipients = Column(Text, nullable=False)  # JSON格式存储接收者列表
    sender = Column(String(100), nullable=True)
    
    # 状态信息
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    priority = Column(Enum(Priority), default=Priority.NORMAL)
    
    # 发送结果
    sent_at = Column(DateTime, nullable=True)
    delivery_status = Column(Text, nullable=True)  # JSON格式存储发送状态
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 业务关联
    business_type = Column(String(50), nullable=True)  # order, production, alert, report
    business_id = Column(String(100), nullable=True)  # 关联的业务ID
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)  # 计划发送时间

class WeChatConfig(Base):
    """
    微信配置模型
    """
    __tablename__ = "wechat_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    is_encrypted = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationRule(Base):
    """
    通知规则模型
    """
    __tablename__ = "notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)  # delivery_alert, progress_update, exception_alert, daily_report
    
    # 规则配置
    conditions = Column(Text, nullable=False)  # JSON格式存储触发条件
    message_template = Column(Text, nullable=False)  # 消息模板
    recipients = Column(Text, nullable=False)  # JSON格式存储接收者
    
    # 调度配置
    schedule = Column(String(200), nullable=True)  # cron表达式或时间间隔
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 状态信息
    enabled = Column(Boolean, default=True)
    priority = Column(Enum(Priority), default=Priority.NORMAL)
    
    # 执行统计
    trigger_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageTemplate(Base):
    """
    消息模板模型
    """
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)  # alert, report, notification
    
    # 模板内容
    title_template = Column(String(500), nullable=True)
    content_template = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    
    # 变量配置
    variables = Column(Text, nullable=True)  # JSON格式存储模板变量
    sample_data = Column(Text, nullable=True)  # JSON格式存储示例数据
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MessageQueue(Base):
    """
    消息队列模型
    """
    __tablename__ = "message_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 队列信息
    message_id = Column(String(50), nullable=False)
    priority = Column(Enum(Priority), default=Priority.NORMAL)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 状态信息
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 时间信息
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeliveryLog(Base):
    """
    消息发送日志模型
    """
    __tablename__ = "delivery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 关联信息
    message_id = Column(String(50), nullable=False)
    recipient = Column(String(200), nullable=False)
    
    # 发送信息
    delivery_method = Column(String(50), nullable=False)  # wechat_work, wechat_webhook
    delivery_status = Column(String(50), nullable=False)  # success, failed, pending
    
    # 响应信息
    response_code = Column(String(20), nullable=True)
    response_message = Column(Text, nullable=True)
    delivery_time = Column(Float, nullable=True)  # 发送耗时（秒）
    
    # 错误信息
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

class MessageStats(Base):
    """
    消息统计模型
    """
    __tablename__ = "message_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    stats_date = Column(DateTime, nullable=False, index=True)
    
    # 发送统计
    total_sent = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    
    # 类型统计
    text_count = Column(Integer, default=0)
    markdown_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    
    # 业务统计
    alert_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    notification_count = Column(Integer, default=0)
    
    # 性能统计
    avg_delivery_time = Column(Float, default=0.0)
    max_delivery_time = Column(Float, default=0.0)
    min_delivery_time = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)