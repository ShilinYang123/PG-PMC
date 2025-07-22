"""通知调度器

负责统一管理通知消息的发送、调度和状态跟踪。
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
import logging

from .models import NotificationMessage, NotificationStatus, NotificationPriority, ChannelType
from .channels.manager import ChannelManager
from .queue import NotificationQueue
from .exceptions import NotificationError, ChannelUnavailableError

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """通知调度器"""
    
    def __init__(self, 
                 channel_manager: ChannelManager,
                 queue_config: Optional[Dict[str, Any]] = None):
        """初始化通知调度器
        
        Args:
            channel_manager: 渠道管理器
            queue_config: 队列配置
        """
        self.channel_manager = channel_manager
        
        # 初始化队列
        queue_config = queue_config or {}
        self.queue = NotificationQueue(
            max_size=queue_config.get('max_size', 10000),
            batch_size=queue_config.get('batch_size', 10),
            batch_timeout=queue_config.get('batch_timeout', 5.0),
            worker_count=queue_config.get('worker_count', 3)
        )
        
        # 设置队列处理器
        self.queue.set_message_processor(self._process_message)
        self.queue.set_event_callbacks(
            on_sent=self._on_message_sent,
            on_failed=self._on_message_failed,
            on_retry_exhausted=self._on_retry_exhausted
        )
        
        # 消息存储（用于状态跟踪）
        self._messages: Dict[str, NotificationMessage] = {}
        self._message_lock = asyncio.Lock()
        
        # 事件回调
        self._event_callbacks: Dict[str, List[Callable]] = {
            'message_sent': [],
            'message_failed': [],
            'message_retry': [],
            'channel_unavailable': []
        }
        
        # 运行状态
        self._running = False
        
        # 统计信息
        self._stats = {
            'total_messages': 0,
            'successful_messages': 0,
            'failed_messages': 0,
            'retried_messages': 0,
            'channel_failures': 0
        }
    
    async def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动渠道管理器
        await self.channel_manager.start()
        
        # 启动队列
        await self.queue.start()
        
        logger.info("Notification scheduler started")
    
    async def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止队列
        await self.queue.stop()
        
        # 停止渠道管理器
        await self.channel_manager.stop()
        
        logger.info("Notification scheduler stopped")
    
    async def send_message(self, 
                          message: NotificationMessage,
                          channel_name: Optional[str] = None,
                          channel_type: Optional[ChannelType] = None,
                          priority: Optional[NotificationPriority] = None,
                          scheduled_time: Optional[datetime] = None,
                          max_retries: int = 3,
                          retry_delay: float = 1.0,
                          callback: Optional[Callable] = None) -> str:
        """发送通知消息
        
        Args:
            message: 通知消息
            channel_name: 指定渠道名称
            channel_type: 指定渠道类型
            priority: 消息优先级
            scheduled_time: 计划发送时间
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            callback: 完成回调
            
        Returns:
            str: 消息ID
            
        Raises:
            NotificationError: 发送失败
        """
        if not self._running:
            raise NotificationError("Scheduler is not running")
        
        # 存储消息
        async with self._message_lock:
            self._messages[message.message_id] = message
        
        # 更新统计
        self._stats['total_messages'] += 1
        
        # 设置消息状态
        message.status = NotificationStatus.QUEUED
        message.created_at = datetime.now()
        
        try:
            # 加入队列
            await self.queue.enqueue(
                message=message,
                priority=priority,
                scheduled_time=scheduled_time,
                max_retries=max_retries,
                retry_delay=retry_delay,
                channel_name=channel_name,
                callback=callback
            )
            
            logger.info(f"Message queued: {message.message_id}")
            return message.message_id
            
        except Exception as e:
            message.status = NotificationStatus.FAILED
            message.error_message = str(e)
            raise NotificationError(f"Failed to queue message: {str(e)}")
    
    async def send_batch(self, 
                        messages: List[NotificationMessage],
                        channel_name: Optional[str] = None,
                        channel_type: Optional[ChannelType] = None,
                        priority: Optional[NotificationPriority] = None,
                        max_retries: int = 3) -> List[str]:
        """批量发送消息
        
        Args:
            messages: 消息列表
            channel_name: 指定渠道名称
            channel_type: 指定渠道类型
            priority: 消息优先级
            max_retries: 最大重试次数
            
        Returns:
            List[str]: 消息ID列表
        """
        message_ids = []
        
        for message in messages:
            try:
                message_id = await self.send_message(
                    message=message,
                    channel_name=channel_name,
                    channel_type=channel_type,
                    priority=priority,
                    max_retries=max_retries
                )
                message_ids.append(message_id)
            except Exception as e:
                logger.error(f"Failed to send message in batch: {e}")
                message_ids.append(None)
        
        return message_ids
    
    async def broadcast_message(self, 
                              message: NotificationMessage,
                              channel_type: Optional[ChannelType] = None,
                              exclude_channels: Optional[List[str]] = None,
                              priority: Optional[NotificationPriority] = None) -> Dict[str, str]:
        """广播消息到多个渠道
        
        Args:
            message: 通知消息
            channel_type: 渠道类型过滤
            exclude_channels: 排除的渠道列表
            priority: 消息优先级
            
        Returns:
            Dict[str, str]: 各渠道的消息ID
        """
        if not self._running:
            raise NotificationError("Scheduler is not running")
        
        # 获取可用渠道
        available_channels = self.channel_manager.get_available_channels(channel_type)
        exclude_channels = exclude_channels or []
        
        # 过滤排除的渠道
        target_channels = [
            ch for ch in available_channels 
            if ch.name not in exclude_channels
        ]
        
        if not target_channels:
            raise ChannelUnavailableError("No available channels for broadcast")
        
        # 为每个渠道创建消息副本
        channel_message_ids = {}
        
        for channel in target_channels:
            try:
                # 创建消息副本
                msg_copy = NotificationMessage(
                    title=message.title,
                    content=message.content,
                    message_type=message.message_type,
                    recipients=message.recipients,
                    priority=message.priority,
                    metadata=message.metadata.copy()
                )
                
                # 发送消息
                message_id = await self.send_message(
                    message=msg_copy,
                    channel_name=channel.name,
                    priority=priority
                )
                
                channel_message_ids[channel.name] = message_id
                
            except Exception as e:
                logger.error(f"Failed to broadcast to channel {channel.name}: {e}")
                channel_message_ids[channel.name] = None
        
        return channel_message_ids
    
    async def _process_message(self, 
                             message: NotificationMessage, 
                             channel_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """处理消息发送
        
        Args:
            message: 通知消息
            channel_name: 渠道名称
            
        Returns:
            (success, error_message): 发送结果
        """
        try:
            # 发送消息
            success, error_message, used_channel = await self.channel_manager.send_message(
                message=message,
                channel_name=channel_name
            )
            
            if success:
                message.sent_at = datetime.now()
                message.channel_used = used_channel
            
            return success, error_message
            
        except Exception as e:
            return False, str(e)
    
    async def _on_message_sent(self, message: NotificationMessage):
        """消息发送成功回调"""
        self._stats['successful_messages'] += 1
        
        # 触发事件回调
        for callback in self._event_callbacks['message_sent']:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in message_sent callback: {e}")
    
    async def _on_message_failed(self, message: NotificationMessage):
        """消息发送失败回调"""
        self._stats['failed_messages'] += 1
        
        # 触发事件回调
        for callback in self._event_callbacks['message_failed']:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in message_failed callback: {e}")
    
    async def _on_retry_exhausted(self, message: NotificationMessage):
        """重试耗尽回调"""
        self._stats['retried_messages'] += 1
        
        # 触发事件回调
        for callback in self._event_callbacks['message_retry']:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in message_retry callback: {e}")
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调
        
        Args:
            event_type: 事件类型 (message_sent, message_failed, message_retry, channel_unavailable)
            callback: 回调函数
        """
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """移除事件回调"""
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    async def get_message_status(self, message_id: str) -> Optional[NotificationMessage]:
        """获取消息状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[NotificationMessage]: 消息对象
        """
        async with self._message_lock:
            return self._messages.get(message_id)
    
    async def get_messages_by_status(self, status: NotificationStatus) -> List[NotificationMessage]:
        """根据状态获取消息列表
        
        Args:
            status: 消息状态
            
        Returns:
            List[NotificationMessage]: 消息列表
        """
        async with self._message_lock:
            return [msg for msg in self._messages.values() if msg.status == status]
    
    async def cancel_message(self, message_id: str) -> bool:
        """取消消息发送
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功取消
        """
        async with self._message_lock:
            message = self._messages.get(message_id)
            if message and message.status in [NotificationStatus.QUEUED, NotificationStatus.RETRYING]:
                message.status = NotificationStatus.CANCELLED
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        queue_stats = self.queue.get_stats()
        channel_stats = self.channel_manager.get_all_status()
        
        return {
            'scheduler': self._stats,
            'queue': queue_stats,
            'channels': {
                'total_channels': len(self.channel_manager),
                'available_channels': len(self.channel_manager.get_available_channels()),
                'channel_details': channel_stats
            },
            'running': self._running
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        # 检查渠道健康状态
        channel_health = await self.channel_manager.health_check_all()
        
        # 检查队列状态
        queue_stats = self.queue.get_stats()
        
        # 计算整体健康状态
        healthy_channels = sum(1 for status in channel_health.values() if status)
        total_channels = len(channel_health)
        
        overall_healthy = (
            self._running and
            queue_stats['status'] == 'running' and
            (total_channels == 0 or healthy_channels > 0)  # 至少有一个健康的渠道
        )
        
        return {
            'overall_healthy': overall_healthy,
            'scheduler_running': self._running,
            'queue_status': queue_stats['status'],
            'total_channels': total_channels,
            'healthy_channels': healthy_channels,
            'channel_health': channel_health,
            'queue_size': queue_stats['current_queue_size'],
            'delayed_queue_size': queue_stats['current_delayed_size']
        }
    
    async def cleanup_old_messages(self, days: int = 7):
        """清理旧消息
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        async with self._message_lock:
            old_message_ids = [
                msg_id for msg_id, msg in self._messages.items()
                if msg.created_at and msg.created_at < cutoff_time
            ]
            
            for msg_id in old_message_ids:
                del self._messages[msg_id]
        
        logger.info(f"Cleaned up {len(old_message_ids)} old messages")
    
    async def pause_queue(self):
        """暂停队列处理"""
        await self.queue.pause()
    
    async def resume_queue(self):
        """恢复队列处理"""
        await self.queue.resume()
    
    async def clear_queue(self):
        """清空队列"""
        self.queue.clear()
    
    async def get_pending_messages(self) -> List[Dict[str, Any]]:
        """获取待处理消息"""
        return await self.queue.get_pending_messages()