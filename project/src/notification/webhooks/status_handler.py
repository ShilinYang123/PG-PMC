"""状态回调处理器

处理微信消息的发送状态、用户交互等回调事件。
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from .base import WebhookEvent, WebhookEventType
from ..models import NotificationMessage, MessageStatus
from ..exceptions import NotificationError

logger = logging.getLogger(__name__)


class MessageStatusType(Enum):
    """消息状态类型"""
    PENDING = "pending"          # 待发送
    SENT = "sent"                # 已发送
    DELIVERED = "delivered"      # 已送达
    READ = "read"                # 已读
    FAILED = "failed"            # 发送失败
    EXPIRED = "expired"          # 已过期
    RECALLED = "recalled"        # 已撤回


@dataclass
class MessageStatusUpdate:
    """消息状态更新"""
    message_id: str
    status: MessageStatusType
    timestamp: datetime
    details: Dict[str, Any]
    user_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'user_id': self.user_id,
            'error_message': self.error_message
        }


@dataclass
class UserInteraction:
    """用户交互事件"""
    message_id: str
    user_id: str
    interaction_type: str  # click, reply, forward等
    timestamp: datetime
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'interaction_type': self.interaction_type,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'metadata': self.metadata or {}
        }


class StatusCallbackHandler:
    """状态回调处理器"""
    
    def __init__(self):
        self._status_callbacks: Dict[MessageStatusType, List[Callable]] = {
            status: [] for status in MessageStatusType
        }
        self._interaction_callbacks: List[Callable] = []
        self._message_status_cache: Dict[str, MessageStatusUpdate] = {}
        self._cache_ttl = timedelta(hours=24)  # 缓存24小时
    
    def add_status_callback(self, status: MessageStatusType, callback: Callable[[MessageStatusUpdate], None]):
        """添加状态回调
        
        Args:
            status: 消息状态类型
            callback: 回调函数
        """
        self._status_callbacks[status].append(callback)
    
    def add_interaction_callback(self, callback: Callable[[UserInteraction], None]):
        """添加交互回调
        
        Args:
            callback: 回调函数
        """
        self._interaction_callbacks.append(callback)
    
    async def handle_webhook_event(self, event: WebhookEvent):
        """处理webhook事件
        
        Args:
            event: webhook事件
        """
        try:
            if event.event_type == WebhookEventType.MESSAGE_SENT:
                await self._handle_message_sent(event)
            elif event.event_type == WebhookEventType.MESSAGE_DELIVERED:
                await self._handle_message_delivered(event)
            elif event.event_type == WebhookEventType.MESSAGE_READ:
                await self._handle_message_read(event)
            elif event.event_type == WebhookEventType.MESSAGE_FAILED:
                await self._handle_message_failed(event)
            elif event.event_type == WebhookEventType.USER_INTERACTION:
                await self._handle_user_interaction(event)
            else:
                logger.debug(f"Unhandled event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"Error handling webhook event {event.event_type}: {e}")
    
    async def _handle_message_sent(self, event: WebhookEvent):
        """处理消息发送事件"""
        if not event.message_id:
            logger.warning("Message sent event without message_id")
            return
        
        status_update = MessageStatusUpdate(
            message_id=event.message_id,
            status=MessageStatusType.SENT,
            timestamp=event.timestamp,
            details=event.data,
            user_id=event.user_id
        )
        
        await self._process_status_update(status_update)
    
    async def _handle_message_delivered(self, event: WebhookEvent):
        """处理消息送达事件"""
        if not event.message_id:
            logger.warning("Message delivered event without message_id")
            return
        
        status_update = MessageStatusUpdate(
            message_id=event.message_id,
            status=MessageStatusType.DELIVERED,
            timestamp=event.timestamp,
            details=event.data,
            user_id=event.user_id
        )
        
        await self._process_status_update(status_update)
    
    async def _handle_message_read(self, event: WebhookEvent):
        """处理消息已读事件"""
        if not event.message_id:
            logger.warning("Message read event without message_id")
            return
        
        status_update = MessageStatusUpdate(
            message_id=event.message_id,
            status=MessageStatusType.READ,
            timestamp=event.timestamp,
            details=event.data,
            user_id=event.user_id
        )
        
        await self._process_status_update(status_update)
    
    async def _handle_message_failed(self, event: WebhookEvent):
        """处理消息失败事件"""
        if not event.message_id:
            logger.warning("Message failed event without message_id")
            return
        
        error_message = event.data.get('error_message') or event.data.get('errmsg')
        
        status_update = MessageStatusUpdate(
            message_id=event.message_id,
            status=MessageStatusType.FAILED,
            timestamp=event.timestamp,
            details=event.data,
            user_id=event.user_id,
            error_message=error_message
        )
        
        await self._process_status_update(status_update)
    
    async def _handle_user_interaction(self, event: WebhookEvent):
        """处理用户交互事件"""
        if not event.message_id or not event.user_id:
            logger.warning("User interaction event without message_id or user_id")
            return
        
        # 解析交互类型
        interaction_type = self._parse_interaction_type(event.data)
        content = event.data.get('content') or event.data.get('text')
        
        interaction = UserInteraction(
            message_id=event.message_id,
            user_id=event.user_id,
            interaction_type=interaction_type,
            timestamp=event.timestamp,
            content=content,
            metadata=event.data
        )
        
        await self._process_user_interaction(interaction)
    
    def _parse_interaction_type(self, data: Dict[str, Any]) -> str:
        """解析交互类型"""
        # 根据数据结构判断交互类型
        if 'msgtype' in data:
            msgtype = data['msgtype']
            if msgtype == 'text':
                return 'reply'
            elif msgtype == 'event':
                return data.get('event', 'unknown')
            else:
                return msgtype
        
        # 其他情况
        if 'click' in data:
            return 'click'
        elif 'reply' in data:
            return 'reply'
        else:
            return 'unknown'
    
    async def _process_status_update(self, status_update: MessageStatusUpdate):
        """处理状态更新"""
        # 更新缓存
        self._message_status_cache[status_update.message_id] = status_update
        
        # 触发回调
        callbacks = self._status_callbacks.get(status_update.status, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(status_update)
                else:
                    callback(status_update)
            except Exception as e:
                logger.error(f"Error in status callback for {status_update.status}: {e}")
        
        logger.info(f"Message {status_update.message_id} status updated to {status_update.status.value}")
    
    async def _process_user_interaction(self, interaction: UserInteraction):
        """处理用户交互"""
        # 触发回调
        for callback in self._interaction_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(interaction)
                else:
                    callback(interaction)
            except Exception as e:
                logger.error(f"Error in interaction callback: {e}")
        
        logger.info(f"User {interaction.user_id} interacted with message {interaction.message_id}: {interaction.interaction_type}")
    
    def get_message_status(self, message_id: str) -> Optional[MessageStatusUpdate]:
        """获取消息状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            消息状态更新对象
        """
        return self._message_status_cache.get(message_id)
    
    def get_message_history(self, message_id: str) -> List[MessageStatusUpdate]:
        """获取消息状态历史
        
        Args:
            message_id: 消息ID
            
        Returns:
            状态历史列表
        """
        # 这里可以扩展为从数据库获取完整历史
        current_status = self._message_status_cache.get(message_id)
        return [current_status] if current_status else []
    
    def cleanup_expired_cache(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = []
        
        for message_id, status_update in self._message_status_cache.items():
            if now - status_update.timestamp > self._cache_ttl:
                expired_keys.append(message_id)
        
        for key in expired_keys:
            del self._message_status_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired status cache entries")


class MessageTracker:
    """消息跟踪器"""
    
    def __init__(self):
        self.status_handler = StatusCallbackHandler()
        self._tracking_enabled = True
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def start_tracking(self):
        """开始跟踪"""
        self._tracking_enabled = True
        
        # 启动清理任务
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def stop_tracking(self):
        """停止跟踪"""
        self._tracking_enabled = False
        
        # 取消清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self._tracking_enabled:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                self.status_handler.cleanup_expired_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def add_status_callback(self, status: MessageStatusType, callback: Callable):
        """添加状态回调"""
        self.status_handler.add_status_callback(status, callback)
    
    def add_interaction_callback(self, callback: Callable):
        """添加交互回调"""
        self.status_handler.add_interaction_callback(callback)
    
    async def handle_webhook_event(self, event: WebhookEvent):
        """处理webhook事件"""
        if self._tracking_enabled:
            await self.status_handler.handle_webhook_event(event)


# 全局消息跟踪器
_message_tracker = None

def get_message_tracker() -> MessageTracker:
    """获取全局消息跟踪器"""
    global _message_tracker
    if _message_tracker is None:
        _message_tracker = MessageTracker()
    return _message_tracker