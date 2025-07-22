"""通知系统集成模块

提供各种第三方服务的集成功能。"""

from .wechat import (
    WeChatIntegration,
    WeChatAPIClient,
    WeChatBotClient,
    get_wechat_integration
)
from .email import EmailIntegration
from .sms import SMSIntegration

__all__ = [
    'WeChatIntegration',
    'WeChatAPIClient', 
    'WeChatBotClient',
    'get_wechat_integration',
    'EmailIntegration',
    'SMSIntegration',
]