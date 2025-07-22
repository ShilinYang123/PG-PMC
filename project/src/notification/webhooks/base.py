"""Webhook处理基础模块

定义webhook处理的基础接口和事件模型。
"""

import json
import hashlib
import hmac
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Webhook事件类型"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"
    USER_INTERACTION = "user_interaction"
    SYSTEM_EVENT = "system_event"
    UNKNOWN = "unknown"


@dataclass
class WebhookEvent:
    """Webhook事件数据"""
    event_type: WebhookEventType
    timestamp: datetime
    source: str  # 事件来源（如：wechat_api, wechat_bot等）
    data: Dict[str, Any]
    message_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'message_id': self.message_id,
            'user_id': self.user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookEvent':
        """从字典创建事件"""
        return cls(
            event_type=WebhookEventType(data.get('event_type', 'unknown')),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data['data'],
            message_id=data.get('message_id'),
            user_id=data.get('user_id')
        )


class BaseWebhookHandler(ABC):
    """Webhook处理器基类"""
    
    def __init__(self, secret: Optional[str] = None):
        """初始化处理器
        
        Args:
            secret: 用于验证签名的密钥
        """
        self.secret = secret
        self._event_handlers: Dict[WebhookEventType, List[Callable]] = {
            event_type: [] for event_type in WebhookEventType
        }
    
    @abstractmethod
    async def handle_request(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """处理webhook请求
        
        Args:
            headers: HTTP请求头
            body: 请求体
            
        Returns:
            响应数据
        """
        pass
    
    @abstractmethod
    def verify_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        """验证请求签名
        
        Args:
            headers: HTTP请求头
            body: 请求体
            
        Returns:
            签名是否有效
        """
        pass
    
    @abstractmethod
    def parse_event(self, data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """解析事件数据
        
        Args:
            data: 原始事件数据
            
        Returns:
            解析后的事件对象
        """
        pass
    
    def add_event_handler(self, event_type: WebhookEventType, handler: Callable[[WebhookEvent], None]):
        """添加事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: WebhookEventType, handler: Callable[[WebhookEvent], None]):
        """移除事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)
    
    async def _trigger_event_handlers(self, event: WebhookEvent):
        """触发事件处理器
        
        Args:
            event: 事件对象
        """
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
    
    def _generate_hmac_signature(self, data: bytes, algorithm: str = 'sha256') -> str:
        """生成HMAC签名
        
        Args:
            data: 要签名的数据
            algorithm: 哈希算法
            
        Returns:
            签名字符串
        """
        if not self.secret:
            raise ValueError("Secret is required for signature generation")
        
        if algorithm == 'sha256':
            signature = hmac.new(
                self.secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).hexdigest()
        elif algorithm == 'sha1':
            signature = hmac.new(
                self.secret.encode('utf-8'),
                data,
                hashlib.sha1
            ).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return signature
    
    def _verify_hmac_signature(self, signature: str, data: bytes, algorithm: str = 'sha256') -> bool:
        """验证HMAC签名
        
        Args:
            signature: 待验证的签名
            data: 原始数据
            algorithm: 哈希算法
            
        Returns:
            签名是否有效
        """
        try:
            expected_signature = self._generate_hmac_signature(data, algorithm)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False