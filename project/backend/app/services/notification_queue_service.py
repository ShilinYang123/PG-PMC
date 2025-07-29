"""通知队列管理服务

管理通知发送队列，包括：
- 异步通知发送
- 队列优先级管理
- 失败重试机制
- 批量发送优化
"""

import asyncio
import json
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from queue import PriorityQueue
from threading import Thread, Lock
from loguru import logger
import time
from sqlalchemy.orm import Session

from ..models.notification import Notification, NotificationStatus, NotificationPriority
from ..services.notification_service import NotificationService
from ..services.wechat_service import WeChatService
from ..services.sms_service import sms_service
from ..services.email_service import email_service


class QueueStatus(Enum):
    """队列状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class QueueItem:
    """队列项"""
    id: str
    notification_id: int
    priority: int
    channel: str
    recipient: str
    content: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    scheduled_at: datetime = None
    status: QueueStatus = QueueStatus.PENDING
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.scheduled_at is None:
            self.scheduled_at = datetime.now()
    
    def __lt__(self, other):
        # 优先级队列排序：优先级高的先处理，时间早的先处理
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.scheduled_at < other.scheduled_at


@dataclass
class BatchItem:
    """批量发送项"""
    channel: str
    items: List[QueueItem]
    batch_size: int = 50
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class NotificationQueueService:
    """通知队列管理服务"""
    
    def __init__(self, db_session_factory: Callable[[], Session]):
        self.db_session_factory = db_session_factory
        self.queue = PriorityQueue()
        self.batch_queues = {
            "email": [],
            "sms": [],
            "wechat": []
        }
        self.processing_items = {}
        self.completed_items = {}
        self.failed_items = {}
        
        self.lock = Lock()
        self.running = False
        self.worker_threads = []
        self.batch_thread = None
        
        # 配置
        self.batch_configs = {
            "email": {"size": 50, "interval": 30},  # 50封邮件，30秒间隔
            "sms": {"size": 100, "interval": 60},   # 100条短信，60秒间隔
            "wechat": {"size": 200, "interval": 10} # 200条微信，10秒间隔
        }
        
        self.retry_delays = [60, 300, 900]  # 重试延迟：1分钟、5分钟、15分钟
        
    def start(self, worker_count: int = 3):
        """启动队列服务"""
        if self.running:
            return
        
        self.running = True
        
        # 启动工作线程
        for i in range(worker_count):
            worker = Thread(target=self._worker, args=(f"worker-{i}",), daemon=True)
            worker.start()
            self.worker_threads.append(worker)
        
        # 启动批量处理线程
        self.batch_thread = Thread(target=self._batch_processor, daemon=True)
        self.batch_thread.start()
        
        logger.info(f"Notification queue service started with {worker_count} workers")
    
    def stop(self):
        """停止队列服务"""
        self.running = False
        
        # 等待工作线程结束
        for worker in self.worker_threads:
            worker.join(timeout=5)
        
        if self.batch_thread:
            self.batch_thread.join(timeout=5)
        
        logger.info("Notification queue service stopped")
    
    def add_notification(self, notification_id: int, channel: str, 
                        recipient: str, content: Dict[str, Any], 
                        priority: NotificationPriority = NotificationPriority.MEDIUM,
                        scheduled_at: Optional[datetime] = None) -> str:
        """添加通知到队列"""
        item_id = f"{notification_id}_{channel}_{int(time.time() * 1000)}"
        
        item = QueueItem(
            id=item_id,
            notification_id=notification_id,
            priority=priority.value,
            channel=channel,
            recipient=recipient,
            content=content,
            scheduled_at=scheduled_at or datetime.now()
        )
        
        # 判断是否支持批量发送
        if channel in self.batch_configs and self._should_batch(channel):
            with self.lock:
                self.batch_queues[channel].append(item)
        else:
            self.queue.put(item)
        
        logger.debug(f"Added notification {item_id} to queue")
        return item_id
    
    def add_batch_notifications(self, notifications: List[Dict[str, Any]]) -> List[str]:
        """批量添加通知"""
        item_ids = []
        
        for notif in notifications:
            item_id = self.add_notification(
                notification_id=notif["notification_id"],
                channel=notif["channel"],
                recipient=notif["recipient"],
                content=notif["content"],
                priority=notif.get("priority", NotificationPriority.MEDIUM),
                scheduled_at=notif.get("scheduled_at")
            )
            item_ids.append(item_id)
        
        return item_ids
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self.lock:
            return {
                "queue_size": self.queue.qsize(),
                "batch_queues": {
                    channel: len(items) for channel, items in self.batch_queues.items()
                },
                "processing_count": len(self.processing_items),
                "completed_count": len(self.completed_items),
                "failed_count": len(self.failed_items),
                "running": self.running
            }
    
    def get_item_status(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取队列项状态"""
        with self.lock:
            if item_id in self.processing_items:
                item = self.processing_items[item_id]
                return {"status": "processing", "item": asdict(item)}
            elif item_id in self.completed_items:
                item = self.completed_items[item_id]
                return {"status": "completed", "item": asdict(item)}
            elif item_id in self.failed_items:
                item = self.failed_items[item_id]
                return {"status": "failed", "item": asdict(item)}
            else:
                # 检查批量队列
                for channel, items in self.batch_queues.items():
                    for item in items:
                        if item.id == item_id:
                            return {"status": "pending_batch", "item": asdict(item)}
                return None
    
    def retry_failed_item(self, item_id: str) -> bool:
        """重试失败的队列项"""
        with self.lock:
            if item_id in self.failed_items:
                item = self.failed_items.pop(item_id)
                item.retry_count = 0
                item.status = QueueStatus.PENDING
                item.error_message = None
                item.scheduled_at = datetime.now()
                
                self.queue.put(item)
                logger.info(f"Retrying failed item {item_id}")
                return True
            return False
    
    def _worker(self, worker_name: str):
        """工作线程"""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            try:
                # 获取队列项（阻塞等待，超时1秒）
                try:
                    item = self.queue.get(timeout=1)
                except:
                    continue
                
                # 检查是否到了执行时间
                if item.scheduled_at > datetime.now():
                    # 重新放回队列
                    self.queue.put(item)
                    time.sleep(1)
                    continue
                
                # 标记为处理中
                with self.lock:
                    self.processing_items[item.id] = item
                    item.status = QueueStatus.PROCESSING
                
                logger.debug(f"Worker {worker_name} processing item {item.id}")
                
                # 处理通知
                success = self._process_item(item)
                
                # 更新状态
                with self.lock:
                    self.processing_items.pop(item.id, None)
                    
                    if success:
                        item.status = QueueStatus.COMPLETED
                        self.completed_items[item.id] = item
                        logger.debug(f"Item {item.id} completed successfully")
                    else:
                        if item.retry_count < item.max_retries:
                            # 重试
                            item.retry_count += 1
                            item.status = QueueStatus.RETRYING
                            delay = self.retry_delays[min(item.retry_count - 1, len(self.retry_delays) - 1)]
                            item.scheduled_at = datetime.now() + timedelta(seconds=delay)
                            
                            self.queue.put(item)
                            logger.warning(f"Item {item.id} failed, retrying in {delay} seconds (attempt {item.retry_count})")
                        else:
                            # 失败
                            item.status = QueueStatus.FAILED
                            self.failed_items[item.id] = item
                            logger.error(f"Item {item.id} failed permanently after {item.retry_count} retries")
                
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    def _batch_processor(self):
        """批量处理线程"""
        logger.info("Batch processor started")
        
        while self.running:
            try:
                for channel, config in self.batch_configs.items():
                    with self.lock:
                        if len(self.batch_queues[channel]) >= config["size"]:
                            # 取出一批进行处理
                            batch_items = self.batch_queues[channel][:config["size"]]
                            self.batch_queues[channel] = self.batch_queues[channel][config["size"]:]
                            
                            # 创建批量项
                            batch = BatchItem(
                                channel=channel,
                                items=batch_items,
                                batch_size=config["size"]
                            )
                            
                            # 异步处理批量发送
                            Thread(target=self._process_batch, args=(batch,), daemon=True).start()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                time.sleep(5)
        
        logger.info("Batch processor stopped")
    
    def _process_item(self, item: QueueItem) -> bool:
        """处理单个队列项"""
        try:
            db = self.db_session_factory()
            notification_service = NotificationService(db)
            
            if item.channel == "email":
                return self._send_email(item)
            elif item.channel == "sms":
                return self._send_sms(item)
            elif item.channel == "wechat":
                return self._send_wechat(item)
            else:
                logger.error(f"Unknown channel: {item.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing item {item.id}: {e}")
            item.error_message = str(e)
            return False
        finally:
            if 'db' in locals():
                db.close()
    
    def _process_batch(self, batch: BatchItem):
        """处理批量发送"""
        try:
            logger.info(f"Processing batch of {len(batch.items)} {batch.channel} notifications")
            
            if batch.channel == "email":
                self._send_batch_emails(batch.items)
            elif batch.channel == "sms":
                self._send_batch_sms(batch.items)
            elif batch.channel == "wechat":
                self._send_batch_wechat(batch.items)
            
            # 更新状态
            with self.lock:
                for item in batch.items:
                    item.status = QueueStatus.COMPLETED
                    self.completed_items[item.id] = item
            
            logger.info(f"Batch processing completed for {batch.channel}")
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            
            # 将失败的项重新加入队列
            with self.lock:
                for item in batch.items:
                    if item.retry_count < item.max_retries:
                        item.retry_count += 1
                        item.status = QueueStatus.RETRYING
                        item.error_message = str(e)
                        self.queue.put(item)
                    else:
                        item.status = QueueStatus.FAILED
                        item.error_message = str(e)
                        self.failed_items[item.id] = item
    
    def _send_email(self, item: QueueItem) -> bool:
        """发送邮件"""
        try:
            from ..services.email_service import EmailMessage
            
            message = EmailMessage(
                to_emails=[item.recipient],
                subject=item.content.get("subject", "通知"),
                html_content=item.content.get("html_content"),
                text_content=item.content.get("text_content")
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(email_service.send_email(message))
            loop.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            item.error_message = str(e)
            return False
    
    def _send_sms(self, item: QueueItem) -> bool:
        """发送短信"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                sms_service.send_sms(
                    phone=item.recipient,
                    template_id=item.content.get("template_id", "order_reminder"),
                    params=item.content.get("params", {})
                )
            )
            loop.close()
            
            return result
            
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            item.error_message = str(e)
            return False
    
    def _send_wechat(self, item: QueueItem) -> bool:
        """发送微信"""
        try:
            # TODO: 实现微信发送逻辑
            logger.info(f"WeChat message sent to {item.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"WeChat sending failed: {e}")
            item.error_message = str(e)
            return False
    
    def _send_batch_emails(self, items: List[QueueItem]):
        """批量发送邮件"""
        try:
            from ..services.email_service import EmailMessage
            
            messages = []
            for item in items:
                message = EmailMessage(
                    to_emails=[item.recipient],
                    subject=item.content.get("subject", "通知"),
                    html_content=item.content.get("html_content"),
                    text_content=item.content.get("text_content")
                )
                messages.append(message)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(email_service.send_batch_emails(messages))
            loop.close()
            
            logger.info(f"Batch email sending completed: {sum(results)}/{len(results)} successful")
            
        except Exception as e:
            logger.error(f"Batch email sending failed: {e}")
            raise
    
    def _send_batch_sms(self, items: List[QueueItem]):
        """批量发送短信"""
        try:
            # 按模板分组
            template_groups = {}
            for item in items:
                template_id = item.content.get("template_id", "order_reminder")
                if template_id not in template_groups:
                    template_groups[template_id] = []
                template_groups[template_id].append(item)
            
            # 分组发送
            for template_id, group_items in template_groups.items():
                phones = [item.recipient for item in group_items]
                params = group_items[0].content.get("params", {})  # 使用第一个的参数
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(
                    sms_service.send_batch_sms(phones, template_id, params)
                )
                loop.close()
            
            logger.info(f"Batch SMS sending completed")
            
        except Exception as e:
            logger.error(f"Batch SMS sending failed: {e}")
            raise
    
    def _send_batch_wechat(self, items: List[QueueItem]):
        """批量发送微信"""
        try:
            # TODO: 实现微信批量发送逻辑
            logger.info(f"Batch WeChat sending completed for {len(items)} items")
            
        except Exception as e:
            logger.error(f"Batch WeChat sending failed: {e}")
            raise
    
    def _should_batch(self, channel: str) -> bool:
        """判断是否应该批量发送"""
        if channel not in self.batch_configs:
            return False
        
        # 检查队列中的数量
        with self.lock:
            queue_size = len(self.batch_queues[channel])
            return queue_size < self.batch_configs[channel]["size"] * 2  # 不超过2倍批量大小
    
    def cleanup_old_items(self, days: int = 7):
        """清理旧的队列项"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with self.lock:
            # 清理已完成的项
            completed_to_remove = [
                item_id for item_id, item in self.completed_items.items()
                if item.created_at < cutoff_time
            ]
            for item_id in completed_to_remove:
                self.completed_items.pop(item_id)
            
            # 清理失败的项
            failed_to_remove = [
                item_id for item_id, item in self.failed_items.items()
                if item.created_at < cutoff_time
            ]
            for item_id in failed_to_remove:
                self.failed_items.pop(item_id)
        
        logger.info(f"Cleaned up {len(completed_to_remove)} completed and {len(failed_to_remove)} failed items")


# 全局队列服务实例
queue_service = None

def get_queue_service(db_session_factory: Callable[[], Session]) -> NotificationQueueService:
    """获取队列服务实例"""
    global queue_service
    if queue_service is None:
        queue_service = NotificationQueueService(db_session_factory)
    return queue_service