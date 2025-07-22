"""PMC通知系统模块

该模块提供完整的通知功能，支持多种通知渠道：
- 企业微信API
- 企业微信群机器人
- 邮件通知（预留）
- 短信通知（预留）

主要组件：
- NotificationService: 核心通知服务
- ChannelManager: 通知渠道管理
- MessageQueue: 消息队列
- RetryManager: 重试机制
- StatusTracker: 状态跟踪
"""

from .models import (
    NotificationMessage, NotificationTemplate, ChannelConfig,
    NotificationStatus, NotificationPriority, ChannelType
)
from .exceptions import (
    NotificationError, ChannelError, MessageError, RetryError, QueueError
)
from .channels import ChannelManager, NotificationChannel
from .queue import NotificationQueue
from .scheduler import NotificationScheduler
from .service import NotificationService, get_notification_service
from .config import NotificationConfig, ConfigManager, get_config_manager
from .utils import MessageFormatter, generate_message_id, format_message_content
from .api import (
    NotificationAPIClient,
    APIEndpoints,
    APIAuth,
    TokenAuth,
    KeyAuth
)

__version__ = "1.0.0"
__author__ = "雨俊"

__all__ = [
    # 核心服务
    'NotificationService',
    'get_notification_service',
    
    # 配置管理
    'NotificationConfig',
    'ConfigManager', 
    'get_config_manager',
    
    # 渠道管理
    'ChannelManager',
    'NotificationChannel',
    
    # 消息队列和调度
    'NotificationQueue',
    'NotificationScheduler',
    
    # 数据模型
    'NotificationMessage',
    'NotificationTemplate',
    'ChannelConfig',
    'NotificationStatus',
    'NotificationPriority',
    'ChannelType',
    
    # 异常类
    'NotificationError',
    'ChannelError',
    'MessageError',
    'RetryError',
    'QueueError',
    
    # 工具函数
    'MessageFormatter',
    'generate_message_id',
    'format_message_content',
    
    # API客户端
    'NotificationAPIClient',
    'APIEndpoints',
    'APIAuth',
    'TokenAuth',
    'KeyAuth',
]

# 默认配置
DEFAULT_CONFIG = {
    "queue_size": 1000,
    "max_retries": 3,
    "retry_delay": 60,
    "batch_size": 10,
    "timeout": 30,
    "enable_persistence": True,
    "db_path": "data/notifications.db"
}