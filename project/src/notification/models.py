"""通知系统数据模型

定义了通知系统中使用的数据模型和枚举类型。
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class NotificationStatus(Enum):
    """通知状态枚举"""
    PENDING = "pending"          # 待发送
    QUEUED = "queued"            # 已入队
    SENDING = "sending"          # 发送中
    SENT = "sent"                # 已发送
    DELIVERED = "delivered"      # 已送达
    FAILED = "failed"            # 发送失败
    RETRYING = "retrying"        # 重试中
    CANCELLED = "cancelled"      # 已取消
    EXPIRED = "expired"          # 已过期


class NotificationPriority(Enum):
    """通知优先级枚举"""
    CRITICAL = 1    # 紧急
    HIGH = 2        # 高
    NORMAL = 3      # 普通
    LOW = 4         # 低
    BULK = 5        # 批量


class ChannelType(Enum):
    """通知渠道类型枚举"""
    WECHAT_API = "wechat_api"        # 企业微信API
    WECHAT_BOT = "wechat_bot"        # 企业微信群机器人
    EMAIL = "email"                  # 邮件
    SMS = "sms"                      # 短信
    WEBHOOK = "webhook"              # Webhook
    PUSH = "push"                    # 推送通知


@dataclass
class NotificationMessage:
    """通知消息数据模型"""
    
    # 基本信息
    title: str
    content: str
    channel: str
    target: str
    
    # 可选信息
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    template_name: Optional[str] = None
    template_vars: Dict[str, Any] = field(default_factory=dict)
    
    # 重试信息
    retry_count: int = 0
    max_retries: int = 3
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # 错误信息
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # 扩展信息
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.priority, int):
            self.priority = NotificationPriority(self.priority)
        if isinstance(self.status, str):
            self.status = NotificationStatus(self.status)
    
    def update_status(self, status: NotificationStatus, error_message: str = None, error_code: str = None):
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()
        
        if status == NotificationStatus.SENT:
            self.sent_at = datetime.now()
        elif status == NotificationStatus.DELIVERED:
            self.delivered_at = datetime.now()
        elif status == NotificationStatus.FAILED:
            self.error_message = error_message
            self.error_code = error_code
    
    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1
        self.status = NotificationStatus.RETRYING
        self.updated_at = datetime.now()
    
    def is_retryable(self) -> bool:
        """判断是否可以重试"""
        return (
            self.retry_count < self.max_retries and
            self.status in [NotificationStatus.FAILED, NotificationStatus.RETRYING]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "title": self.title,
            "content": self.content,
            "channel": self.channel,
            "target": self.target,
            "priority": self.priority.value,
            "status": self.status.value,
            "template_name": self.template_name,
            "template_vars": self.template_vars,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "error_details": self.error_details,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationMessage':
        """从字典创建实例"""
        # 处理时间字段
        for time_field in ['created_at', 'updated_at', 'sent_at', 'delivered_at']:
            if data.get(time_field):
                data[time_field] = datetime.fromisoformat(data[time_field])
        
        # 处理枚举字段
        if 'priority' in data:
            data['priority'] = NotificationPriority(data['priority'])
        if 'status' in data:
            data['status'] = NotificationStatus(data['status'])
        
        return cls(**data)


@dataclass
class NotificationTemplate:
    """通知模板数据模型"""
    
    name: str
    title_template: str
    content_template: str
    channel: str
    variables: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def render(self, variables: Dict[str, Any]) -> tuple[str, str]:
        """渲染模板
        
        Args:
            variables: 模板变量
            
        Returns:
            (title, content): 渲染后的标题和内容
        """
        try:
            title = self.title_template.format(**variables)
            content = self.content_template.format(**variables)
            return title, content
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
        except Exception as e:
            raise ValueError(f"Template render error: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "title_template": self.title_template,
            "content_template": self.content_template,
            "channel": self.channel,
            "variables": self.variables,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ChannelConfig:
    """通知渠道配置数据模型"""
    
    name: str
    channel_type: ChannelType
    enabled: bool = True
    priority: int = 1
    rate_limit: int = 100  # 每分钟最大发送数
    timeout: int = 30      # 超时时间（秒）
    retry_delay: int = 60  # 重试延迟（秒）
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.channel_type, str):
            self.channel_type = ChannelType(self.channel_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "channel_type": self.channel_type.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "retry_delay": self.retry_delay,
            "config": self.config
        }


@dataclass
class NotificationStats:
    """通知统计数据模型"""
    
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_retries: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    
    def calculate_success_rate(self):
        """计算成功率"""
        total = self.total_sent + self.total_failed
        if total > 0:
            self.success_rate = self.total_delivered / total * 100
        else:
            self.success_rate = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_sent": self.total_sent,
            "total_delivered": self.total_delivered,
            "total_failed": self.total_failed,
            "total_retries": self.total_retries,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time
        }