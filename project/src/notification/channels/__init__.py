"""通知渠道模块

提供各种通知渠道的实现：
- NotificationChannel: 抽象基类
- ChannelManager: 渠道管理器
- WeChatAPIChannel: 企业微信API渠道
- WeChatBotChannel: 企业微信群机器人渠道
- EmailChannel: 邮件渠道（预留）
- SMSChannel: 短信渠道（预留）
"""

from .base import NotificationChannel
from .manager import ChannelManager
from .wechat_api import WeChatAPIChannel
from .wechat_bot import WeChatBotChannel

__all__ = [
    "NotificationChannel",
    "ChannelManager",
    "WeChatAPIChannel",
    "WeChatBotChannel",
]