"""通知队列模块

提供消息队列、重试机制和批处理功能。
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import heapq

from .models import NotificationMessage, NotificationStatus, NotificationPriority
from .exceptions import QueueError, QueueFullError, RetryError, RetryExhaustedError

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    """队列状态"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class QueuedMessage:
    """队列中的消息"""
    message: NotificationMessage
    priority: int = field(default=0)  # 优先级，数字越小优先级越高
    scheduled_time: datetime = field(default_factory=datetime.now)
    retry_count: int = field(default=0)
    max_retries: int = field(default=3)
    retry_delay: float = field(default=1.0)  # 重试延迟（秒）
    retry_backoff: float = field(default=2.0)  # 退避倍数
    channel_name: Optional[str] = field(default=None)
    callback: Optional[Callable] = field(default=None)
    
    def __lt__(self, other):
        """用于优先队列排序"""
        if self.scheduled_time != other.scheduled_time:
            return self.scheduled_time < other.scheduled_time
        return self.priority < other.priority
    
    def calculate_next_retry_time(self) -> datetime:
        """计算下次重试时间"""
        delay = self.retry_delay * (self.retry_backoff ** self.retry_count)
        return datetime.now() + timedelta(seconds=delay)
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return self.retry_count < self.max_retries
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message.message_id,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff": self.retry_backoff,
            "channel_name": self.channel_name
        }


class NotificationQueue:
    """通知队列"""
    
    def __init__(self, 
                 max_size: int = 10000,
                 batch_size: int = 10,
                 batch_timeout: float = 5.0,
                 worker_count: int = 3):
        """初始化通知队列
        
        Args:
            max_size: 队列最大大小
            batch_size: 批处理大小
            batch_timeout: 批处理超时时间（秒）
            worker_count: 工作线程数量
        """
        self.max_size = max_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.worker_count = worker_count
        
        # 队列状态
        self.status = QueueStatus.STOPPED
        
        # 消息队列（优先队列）
        self._queue: List[QueuedMessage] = []
        self._queue_lock = asyncio.Lock()
        
        # 延迟队列（用于重试）
        self._delayed_queue: List[QueuedMessage] = []
        self._delayed_lock = asyncio.Lock()
        
        # 工作任务
        self._workers: List[asyncio.Task] = []
        self._delayed_processor: Optional[asyncio.Task] = None
        
        # 统计信息
        self._stats = {
            "total_enqueued": 0,
            "total_processed": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_retries": 0,
            "current_queue_size": 0,
            "current_delayed_size": 0
        }
        
        # 消息处理器
        self._message_processor: Optional[Callable] = None
        
        # 事件回调
        self._on_message_sent: Optional[Callable] = None
        self._on_message_failed: Optional[Callable] = None
        self._on_retry_exhausted: Optional[Callable] = None
    
    def set_message_processor(self, processor: Callable):
        """设置消息处理器
        
        Args:
            processor: 消息处理函数，签名为 async def(message: NotificationMessage, channel_name: str) -> Tuple[bool, str]
        """
        self._message_processor = processor
    
    def set_event_callbacks(self, 
                          on_sent: Optional[Callable] = None,
                          on_failed: Optional[Callable] = None,
                          on_retry_exhausted: Optional[Callable] = None):
        """设置事件回调
        
        Args:
            on_sent: 消息发送成功回调
            on_failed: 消息发送失败回调
            on_retry_exhausted: 重试耗尽回调
        """
        self._on_message_sent = on_sent
        self._on_message_failed = on_failed
        self._on_retry_exhausted = on_retry_exhausted
    
    async def enqueue(self, 
                     message: NotificationMessage,
                     priority: Optional[NotificationPriority] = None,
                     scheduled_time: Optional[datetime] = None,
                     max_retries: int = 3,
                     retry_delay: float = 1.0,
                     retry_backoff: float = 2.0,
                     channel_name: Optional[str] = None,
                     callback: Optional[Callable] = None) -> bool:
        """将消息加入队列
        
        Args:
            message: 通知消息
            priority: 消息优先级
            scheduled_time: 计划发送时间
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            retry_backoff: 退避倍数
            channel_name: 指定渠道名称
            callback: 完成回调
            
        Returns:
            bool: 是否成功加入队列
            
        Raises:
            QueueFullError: 队列已满
        """
        async with self._queue_lock:
            if len(self._queue) >= self.max_size:
                raise QueueFullError(f"Queue is full (max_size: {self.max_size})")
            
            # 设置默认优先级
            if priority is None:
                priority = message.priority
            
            priority_value = {
                NotificationPriority.LOW: 3,
                NotificationPriority.NORMAL: 2,
                NotificationPriority.HIGH: 1,
                NotificationPriority.URGENT: 0
            }.get(priority, 2)
            
            # 创建队列消息
            queued_msg = QueuedMessage(
                message=message,
                priority=priority_value,
                scheduled_time=scheduled_time or datetime.now(),
                max_retries=max_retries,
                retry_delay=retry_delay,
                retry_backoff=retry_backoff,
                channel_name=channel_name,
                callback=callback
            )
            
            # 加入队列
            heapq.heappush(self._queue, queued_msg)
            self._stats["total_enqueued"] += 1
            self._stats["current_queue_size"] = len(self._queue)
            
            logger.debug(f"Message enqueued: {message.message_id} (priority: {priority_value})")
            return True
    
    async def enqueue_batch(self, messages: List[Tuple[NotificationMessage, Dict[str, Any]]]) -> int:
        """批量加入消息
        
        Args:
            messages: 消息列表，每个元素为 (message, options)
            
        Returns:
            int: 成功加入的消息数量
        """
        success_count = 0
        
        for message, options in messages:
            try:
                await self.enqueue(message, **options)
                success_count += 1
            except QueueFullError:
                logger.warning(f"Queue full, skipping message: {message.message_id}")
                break
            except Exception as e:
                logger.error(f"Failed to enqueue message {message.message_id}: {e}")
        
        return success_count
    
    async def start(self):
        """启动队列处理"""
        if self.status == QueueStatus.RUNNING:
            return
        
        if not self._message_processor:
            raise QueueError("Message processor not set")
        
        self.status = QueueStatus.RUNNING
        
        # 启动工作线程
        self._workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.worker_count)
        ]
        
        # 启动延迟处理器
        self._delayed_processor = asyncio.create_task(self._delayed_processor_loop())
        
        logger.info(f"Notification queue started with {self.worker_count} workers")
    
    async def stop(self):
        """停止队列处理"""
        if self.status == QueueStatus.STOPPED:
            return
        
        self.status = QueueStatus.STOPPED
        
        # 停止工作线程
        for worker in self._workers:
            worker.cancel()
        
        if self._delayed_processor:
            self._delayed_processor.cancel()
        
        # 等待所有任务完成
        await asyncio.gather(*self._workers, self._delayed_processor, return_exceptions=True)
        
        self._workers.clear()
        self._delayed_processor = None
        
        logger.info("Notification queue stopped")
    
    async def pause(self):
        """暂停队列处理"""
        self.status = QueueStatus.PAUSED
        logger.info("Notification queue paused")
    
    async def resume(self):
        """恢复队列处理"""
        self.status = QueueStatus.RUNNING
        logger.info("Notification queue resumed")
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        logger.info(f"Worker {worker_name} started")
        
        while self.status != QueueStatus.STOPPED:
            try:
                if self.status == QueueStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue
                
                # 获取消息
                queued_msg = await self._dequeue()
                if not queued_msg:
                    await asyncio.sleep(0.1)
                    continue
                
                # 检查是否到了发送时间
                if queued_msg.scheduled_time > datetime.now():
                    # 重新放入延迟队列
                    await self._enqueue_delayed(queued_msg)
                    continue
                
                # 处理消息
                await self._process_message(queued_msg)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _dequeue(self) -> Optional[QueuedMessage]:
        """从队列中取出消息"""
        async with self._queue_lock:
            if self._queue:
                msg = heapq.heappop(self._queue)
                self._stats["current_queue_size"] = len(self._queue)
                return msg
            return None
    
    async def _process_message(self, queued_msg: QueuedMessage):
        """处理单个消息"""
        try:
            # 更新消息状态
            queued_msg.message.status = NotificationStatus.SENDING
            queued_msg.message.sent_at = datetime.now()
            
            # 调用消息处理器
            success, error_message = await self._message_processor(
                queued_msg.message, 
                queued_msg.channel_name
            )
            
            self._stats["total_processed"] += 1
            
            if success:
                # 发送成功
                queued_msg.message.status = NotificationStatus.SENT
                self._stats["total_success"] += 1
                
                # 调用成功回调
                if self._on_message_sent:
                    try:
                        await self._on_message_sent(queued_msg.message)
                    except Exception as e:
                        logger.error(f"Error in success callback: {e}")
                
                # 调用消息回调
                if queued_msg.callback:
                    try:
                        await queued_msg.callback(queued_msg.message, True, None)
                    except Exception as e:
                        logger.error(f"Error in message callback: {e}")
                
                logger.debug(f"Message sent successfully: {queued_msg.message.message_id}")
            
            else:
                # 发送失败，尝试重试
                await self._handle_send_failure(queued_msg, error_message)
        
        except Exception as e:
            # 处理异常
            await self._handle_send_failure(queued_msg, str(e))
    
    async def _handle_send_failure(self, queued_msg: QueuedMessage, error_message: str):
        """处理发送失败"""
        queued_msg.message.status = NotificationStatus.FAILED
        queued_msg.message.error_message = error_message
        
        if queued_msg.can_retry():
            # 可以重试
            queued_msg.retry_count += 1
            queued_msg.scheduled_time = queued_msg.calculate_next_retry_time()
            queued_msg.message.status = NotificationStatus.RETRYING
            
            # 加入延迟队列
            await self._enqueue_delayed(queued_msg)
            
            self._stats["total_retries"] += 1
            logger.warning(f"Message retry scheduled: {queued_msg.message.message_id} (attempt {queued_msg.retry_count}/{queued_msg.max_retries})")
        
        else:
            # 重试耗尽
            self._stats["total_failed"] += 1
            
            # 调用重试耗尽回调
            if self._on_retry_exhausted:
                try:
                    await self._on_retry_exhausted(queued_msg.message)
                except Exception as e:
                    logger.error(f"Error in retry exhausted callback: {e}")
            
            # 调用失败回调
            if self._on_message_failed:
                try:
                    await self._on_message_failed(queued_msg.message)
                except Exception as e:
                    logger.error(f"Error in failure callback: {e}")
            
            # 调用消息回调
            if queued_msg.callback:
                try:
                    await queued_msg.callback(queued_msg.message, False, error_message)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")
            
            logger.error(f"Message failed permanently: {queued_msg.message.message_id} - {error_message}")
    
    async def _enqueue_delayed(self, queued_msg: QueuedMessage):
        """加入延迟队列"""
        async with self._delayed_lock:
            heapq.heappush(self._delayed_queue, queued_msg)
            self._stats["current_delayed_size"] = len(self._delayed_queue)
    
    async def _delayed_processor_loop(self):
        """延迟队列处理循环"""
        while self.status != QueueStatus.STOPPED:
            try:
                await self._process_delayed_messages()
                await asyncio.sleep(1)  # 每秒检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Delayed processor error: {e}")
                await asyncio.sleep(5)
    
    async def _process_delayed_messages(self):
        """处理延迟消息"""
        now = datetime.now()
        ready_messages = []
        
        async with self._delayed_lock:
            # 找出所有到期的消息
            while self._delayed_queue and self._delayed_queue[0].scheduled_time <= now:
                ready_messages.append(heapq.heappop(self._delayed_queue))
            
            self._stats["current_delayed_size"] = len(self._delayed_queue)
        
        # 将到期消息重新加入主队列
        if ready_messages:
            async with self._queue_lock:
                for msg in ready_messages:
                    heapq.heappush(self._queue, msg)
                
                self._stats["current_queue_size"] = len(self._queue)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        return {
            **self._stats,
            "status": self.status.value,
            "worker_count": len(self._workers),
            "max_size": self.max_size,
            "batch_size": self.batch_size,
            "batch_timeout": self.batch_timeout
        }
    
    def clear(self):
        """清空队列"""
        self._queue.clear()
        self._delayed_queue.clear()
        self._stats["current_queue_size"] = 0
        self._stats["current_delayed_size"] = 0
        logger.info("Queue cleared")
    
    async def get_pending_messages(self) -> List[Dict[str, Any]]:
        """获取待处理消息列表"""
        pending = []
        
        async with self._queue_lock:
            for msg in self._queue:
                pending.append(msg.to_dict())
        
        async with self._delayed_lock:
            for msg in self._delayed_queue:
                msg_dict = msg.to_dict()
                msg_dict["is_delayed"] = True
                pending.append(msg_dict)
        
        return pending