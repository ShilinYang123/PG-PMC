"""PMC系统微信通知服务

实现PMC系统的自动微信通知功能，包括生产任务更新、异常预警、会议纪要等。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from ..notification import (
    NotificationManager,
    NotificationMessage,
    ChannelType,
    MessagePriority,
    NotificationConfig
)
from ..notification.integrations import get_wechat_integration
from .models import ProductionTask, MeetingMinutes, ExceptionAlert, DeliveryReminder

logger = logging.getLogger(__name__)


class PMCNotificationService:
    """PMC通知服务"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化PMC通知服务
        
        Args:
            config_path: 通知配置文件路径
        """
        # 加载配置
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "notification.yaml"
        
        self.config = NotificationConfig(str(config_path))
        
        # 初始化通知管理器
        self.notification_manager = NotificationManager(self.config)
        
        # 微信集成
        self.wechat_integration = get_wechat_integration()
        
        # 服务状态
        self._running = False
        self._tasks = []
    
    async def start(self):
        """启动通知服务"""
        if self._running:
            logger.warning("Notification service is already running")
            return
        
        logger.info("Starting PMC notification service...")
        
        # 启动通知管理器
        await self.notification_manager.start()
        
        # 启动定时任务
        self._running = True
        self._tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info("PMC notification service started successfully")
    
    async def stop(self):
        """停止通知服务"""
        if not self._running:
            return
        
        logger.info("Stopping PMC notification service...")
        
        self._running = False
        
        # 取消定时任务
        for task in self._tasks:
            task.cancel()
        
        # 等待任务完成
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # 停止通知管理器
        await self.notification_manager.stop()
        
        logger.info("PMC notification service stopped")
    
    async def send_production_task_notification(self, task: ProductionTask, 
                                              recipients: Optional[Dict[str, Any]] = None,
                                              priority: MessagePriority = MessagePriority.NORMAL):
        """发送生产任务通知
        
        Args:
            task: 生产任务对象
            recipients: 接收者信息
            priority: 消息优先级
        """
        try:
            # 构建消息内容
            template = self.config.get_template('production_task')
            content = template['content'].format(
                task_id=task.task_id,
                product_name=task.product_name,
                status=task.status,
                planned_completion=task.planned_completion.strftime('%Y-%m-%d %H:%M'),
                progress=task.progress,
                additional_info=task.additional_info or '无'
            )
            
            # 创建通知消息
            message = NotificationMessage(
                title=template['title'],
                content=content,
                message_type=template.get('message_type', 'text'),
                priority=priority,
                recipients=recipients or {'users': '@all'},
                metadata={
                    'task_id': task.task_id,
                    'notification_type': 'production_task',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 发送通知
            await self.notification_manager.send_message(message, routing_key='production')
            
            logger.info(f"Production task notification sent for task {task.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to send production task notification: {e}")
            raise
    
    async def send_exception_alert(self, alert: ExceptionAlert,
                                 recipients: Optional[Dict[str, Any]] = None):
        """发送异常预警通知
        
        Args:
            alert: 异常预警对象
            recipients: 接收者信息
        """
        try:
            # 构建消息内容
            template = self.config.get_template('exception_alert')
            content = template['content'].format(
                alert_type=alert.alert_type,
                occurrence_time=alert.occurrence_time.strftime('%Y-%m-%d %H:%M:%S'),
                affected_scope=alert.affected_scope,
                severity=alert.severity,
                description=alert.description,
                recommended_action=alert.recommended_action
            )
            
            # 根据严重程度确定优先级
            priority = MessagePriority.HIGH if alert.severity in ['高', 'critical'] else MessagePriority.NORMAL
            
            # 创建通知消息
            message = NotificationMessage(
                title=template['title'],
                content=content,
                message_type=template.get('message_type', 'text'),
                priority=priority,
                recipients=recipients or {'users': '@all'},
                metadata={
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'notification_type': 'exception_alert',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 紧急情况使用紧急路由
            routing_key = 'urgent' if priority == MessagePriority.HIGH else 'production'
            
            # 发送通知
            await self.notification_manager.send_message(message, routing_key=routing_key)
            
            logger.info(f"Exception alert sent for {alert.alert_type} (severity: {alert.severity})")
            
        except Exception as e:
            logger.error(f"Failed to send exception alert: {e}")
            raise
    
    async def send_meeting_minutes(self, minutes: MeetingMinutes,
                                 recipients: Optional[Dict[str, Any]] = None):
        """发送会议纪要通知
        
        Args:
            minutes: 会议纪要对象
            recipients: 接收者信息
        """
        try:
            # 构建消息内容
            template = self.config.get_template('meeting_minutes')
            content = template['content'].format(
                meeting_number=minutes.meeting_number,
                meeting_time=minutes.meeting_time.strftime('%Y-%m-%d %H:%M'),
                attendees=', '.join(minutes.attendees),
                main_topics='\n'.join([f"• {topic}" for topic in minutes.main_topics]),
                decisions='\n'.join([f"• {decision}" for decision in minutes.decisions]),
                action_items='\n'.join([f"• {item}" for item in minutes.action_items]),
                next_meeting=minutes.next_meeting.strftime('%Y-%m-%d %H:%M') if minutes.next_meeting else '待定'
            )
            
            # 创建通知消息
            message = NotificationMessage(
                title=template['title'],
                content=content,
                message_type=template.get('message_type', 'text'),
                priority=MessagePriority.NORMAL,
                recipients=recipients or {'users': '@all'},
                metadata={
                    'meeting_number': minutes.meeting_number,
                    'notification_type': 'meeting_minutes',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 发送通知
            await self.notification_manager.send_message(message, routing_key='management')
            
            logger.info(f"Meeting minutes sent for meeting #{minutes.meeting_number}")
            
        except Exception as e:
            logger.error(f"Failed to send meeting minutes: {e}")
            raise
    
    async def send_delivery_reminder(self, reminder: DeliveryReminder,
                                   recipients: Optional[Dict[str, Any]] = None):
        """发送供货提醒通知
        
        Args:
            reminder: 供货提醒对象
            recipients: 接收者信息
        """
        try:
            # 构建消息内容
            template = self.config.get_template('delivery_reminder')
            content = template['content'].format(
                order_id=reminder.order_id,
                customer_name=reminder.customer_name,
                product_info=reminder.product_info,
                original_delivery=reminder.original_delivery.strftime('%Y-%m-%d'),
                adjusted_delivery=reminder.adjusted_delivery.strftime('%Y-%m-%d'),
                advance_days=reminder.advance_days
            )
            
            # 创建通知消息
            message = NotificationMessage(
                title=template['title'],
                content=content,
                message_type=template.get('message_type', 'text'),
                priority=MessagePriority.HIGH,  # 供货提醒通常比较重要
                recipients=recipients or {'users': '@all'},
                metadata={
                    'order_id': reminder.order_id,
                    'advance_days': reminder.advance_days,
                    'notification_type': 'delivery_reminder',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 发送通知
            await self.notification_manager.send_message(message, routing_key='urgent')
            
            logger.info(f"Delivery reminder sent for order {reminder.order_id}")
            
        except Exception as e:
            logger.error(f"Failed to send delivery reminder: {e}")
            raise
    
    async def send_custom_notification(self, title: str, content: str,
                                     message_type: str = 'text',
                                     priority: MessagePriority = MessagePriority.NORMAL,
                                     recipients: Optional[Dict[str, Any]] = None,
                                     routing_key: str = 'default',
                                     metadata: Optional[Dict[str, Any]] = None):
        """发送自定义通知
        
        Args:
            title: 消息标题
            content: 消息内容
            message_type: 消息类型
            priority: 消息优先级
            recipients: 接收者信息
            routing_key: 路由键
            metadata: 元数据
        """
        try:
            # 创建通知消息
            message = NotificationMessage(
                title=title,
                content=content,
                message_type=message_type,
                priority=priority,
                recipients=recipients or {'users': '@all'},
                metadata=metadata or {
                    'notification_type': 'custom',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # 发送通知
            await self.notification_manager.send_message(message, routing_key=routing_key)
            
            logger.info(f"Custom notification sent: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send custom notification: {e}")
            raise
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        manager_status = await self.notification_manager.get_status()
        
        return {
            'service_running': self._running,
            'notification_manager': manager_status,
            'wechat_integration_available': self.wechat_integration is not None,
            'active_tasks': len(self._tasks),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _health_check_loop(self):
        """健康检查循环"""
        interval = self.config.get('scheduler', {}).get('health_check_interval', 60)
        
        while self._running:
            try:
                # 执行健康检查
                await self.notification_manager.health_check()
                logger.debug("Health check completed")
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
            
            # 等待下次检查
            await asyncio.sleep(interval)
    
    async def _cleanup_loop(self):
        """清理循环"""
        interval = self.config.get('queue', {}).get('cleanup_interval', 3600)
        
        while self._running:
            try:
                # 执行清理任务
                await self.notification_manager.cleanup()
                logger.debug("Cleanup completed")
                
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
            
            # 等待下次清理
            await asyncio.sleep(interval)


# 全局服务实例
_notification_service: Optional[PMCNotificationService] = None


def get_notification_service(config_path: Optional[str] = None) -> PMCNotificationService:
    """获取通知服务实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        PMCNotificationService: 通知服务实例
    """
    global _notification_service
    
    if _notification_service is None:
        _notification_service = PMCNotificationService(config_path)
    
    return _notification_service


async def start_notification_service(config_path: Optional[str] = None):
    """启动通知服务
    
    Args:
        config_path: 配置文件路径
    """
    service = get_notification_service(config_path)
    await service.start()


async def stop_notification_service():
    """停止通知服务"""
    global _notification_service
    
    if _notification_service:
        await _notification_service.stop()
        _notification_service = None