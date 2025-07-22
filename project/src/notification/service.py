"""通知服务

提供统一的通知服务接口，整合调度器、渠道管理器和队列。
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import logging

from .models import (
    NotificationMessage, NotificationTemplate, ChannelConfig, 
    NotificationStatus, NotificationPriority, ChannelType
)
from .channels.manager import ChannelManager
from .channels.wechat_api import WeChatAPIChannel
from .channels.wechat_bot import WeChatBotChannel
from .scheduler import NotificationScheduler
from .exceptions import NotificationError, ChannelError

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化通知服务
        
        Args:
            config: 服务配置
        """
        self.config = config or {}
        
        # 初始化渠道管理器
        self.channel_manager = ChannelManager()
        
        # 注册渠道类型
        self._register_channel_classes()
        
        # 初始化调度器
        queue_config = self.config.get('queue', {})
        self.scheduler = NotificationScheduler(self.channel_manager, queue_config)
        
        # 模板存储
        self._templates: Dict[str, NotificationTemplate] = {}
        
        # 运行状态
        self._initialized = False
        self._running = False
    
    def _register_channel_classes(self):
        """注册渠道类型"""
        self.channel_manager.register_channel_class(ChannelType.WECHAT_API, WeChatAPIChannel)
        self.channel_manager.register_channel_class(ChannelType.WECHAT_BOT, WeChatBotChannel)
        # 可以在这里注册更多渠道类型
    
    async def initialize(self, channels_config: Optional[List[Dict[str, Any]]] = None):
        """初始化服务
        
        Args:
            channels_config: 渠道配置列表
        """
        if self._initialized:
            return
        
        # 配置渠道
        if channels_config:
            await self._configure_channels(channels_config)
        
        # 加载默认模板
        self._load_default_templates()
        
        self._initialized = True
        logger.info("Notification service initialized")
    
    async def _configure_channels(self, channels_config: List[Dict[str, Any]]):
        """配置渠道"""
        for channel_config in channels_config:
            try:
                config = ChannelConfig(
                    name=channel_config['name'],
                    channel_type=ChannelType(channel_config['type']),
                    enabled=channel_config.get('enabled', True),
                    settings=channel_config.get('settings', {}),
                    rate_limit=channel_config.get('rate_limit', 60),
                    timeout=channel_config.get('timeout', 30)
                )
                
                self.channel_manager.add_channel(config)
                logger.info(f"Channel configured: {config.name} ({config.channel_type.value})")
                
            except Exception as e:
                logger.error(f"Failed to configure channel {channel_config.get('name', 'unknown')}: {e}")
    
    def _load_default_templates(self):
        """加载默认模板"""
        # 系统通知模板
        self._templates['system_alert'] = NotificationTemplate(
            template_id='system_alert',
            name='系统告警',
            content='**系统告警**\n\n{message}\n\n时间：{timestamp}',
            message_type='markdown',
            variables=['message', 'timestamp']
        )
        
        # 任务完成模板
        self._templates['task_completed'] = NotificationTemplate(
            template_id='task_completed',
            name='任务完成',
            content='**任务完成通知**\n\n任务：{task_name}\n状态：{status}\n完成时间：{completed_at}',
            message_type='markdown',
            variables=['task_name', 'status', 'completed_at']
        )
        
        # 数据报告模板
        self._templates['data_report'] = NotificationTemplate(
            template_id='data_report',
            name='数据报告',
            content='**数据报告**\n\n{report_content}\n\n生成时间：{generated_at}',
            message_type='markdown',
            variables=['report_content', 'generated_at']
        )
        
        logger.info(f"Loaded {len(self._templates)} default templates")
    
    async def start(self):
        """启动服务"""
        if not self._initialized:
            raise NotificationError("Service not initialized. Call initialize() first.")
        
        if self._running:
            return
        
        await self.scheduler.start()
        self._running = True
        
        logger.info("Notification service started")
    
    async def stop(self):
        """停止服务"""
        if not self._running:
            return
        
        await self.scheduler.stop()
        self._running = False
        
        logger.info("Notification service stopped")
    
    async def send_notification(self, 
                              title: Optional[str] = None,
                              content: str = "",
                              message_type: str = "text",
                              recipients: Optional[Dict[str, Any]] = None,
                              priority: NotificationPriority = NotificationPriority.NORMAL,
                              channel_name: Optional[str] = None,
                              channel_type: Optional[ChannelType] = None,
                              scheduled_time: Optional[datetime] = None,
                              metadata: Optional[Dict[str, Any]] = None,
                              template_id: Optional[str] = None,
                              template_vars: Optional[Dict[str, Any]] = None,
                              max_retries: int = 3,
                              callback: Optional[Callable] = None) -> str:
        """发送通知
        
        Args:
            title: 标题
            content: 内容
            message_type: 消息类型
            recipients: 接收者
            priority: 优先级
            channel_name: 指定渠道名称
            channel_type: 指定渠道类型
            scheduled_time: 计划发送时间
            metadata: 元数据
            template_id: 模板ID
            template_vars: 模板变量
            max_retries: 最大重试次数
            callback: 完成回调
            
        Returns:
            str: 消息ID
        """
        if not self._running:
            raise NotificationError("Service is not running")
        
        # 如果使用模板，渲染消息内容
        if template_id:
            title, content, message_type = self._render_template(template_id, template_vars or {})
        
        # 创建消息
        message = NotificationMessage(
            title=title,
            content=content,
            message_type=message_type,
            recipients=recipients or {},
            priority=priority,
            metadata=metadata or {}
        )
        
        # 发送消息
        return await self.scheduler.send_message(
            message=message,
            channel_name=channel_name,
            channel_type=channel_type,
            priority=priority,
            scheduled_time=scheduled_time,
            max_retries=max_retries,
            callback=callback
        )
    
    async def send_batch_notifications(self, 
                                     notifications: List[Dict[str, Any]],
                                     channel_name: Optional[str] = None,
                                     channel_type: Optional[ChannelType] = None) -> List[str]:
        """批量发送通知
        
        Args:
            notifications: 通知列表
            channel_name: 指定渠道名称
            channel_type: 指定渠道类型
            
        Returns:
            List[str]: 消息ID列表
        """
        messages = []
        
        for notification in notifications:
            # 处理模板
            if 'template_id' in notification:
                title, content, message_type = self._render_template(
                    notification['template_id'], 
                    notification.get('template_vars', {})
                )
            else:
                title = notification.get('title')
                content = notification.get('content', '')
                message_type = notification.get('message_type', 'text')
            
            # 创建消息
            message = NotificationMessage(
                title=title,
                content=content,
                message_type=message_type,
                recipients=notification.get('recipients', {}),
                priority=NotificationPriority(notification.get('priority', 'normal')),
                metadata=notification.get('metadata', {})
            )
            
            messages.append(message)
        
        return await self.scheduler.send_batch(
            messages=messages,
            channel_name=channel_name,
            channel_type=channel_type
        )
    
    async def broadcast_notification(self, 
                                   title: Optional[str] = None,
                                   content: str = "",
                                   message_type: str = "text",
                                   recipients: Optional[Dict[str, Any]] = None,
                                   priority: NotificationPriority = NotificationPriority.NORMAL,
                                   channel_type: Optional[ChannelType] = None,
                                   exclude_channels: Optional[List[str]] = None,
                                   template_id: Optional[str] = None,
                                   template_vars: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """广播通知到多个渠道
        
        Args:
            title: 标题
            content: 内容
            message_type: 消息类型
            recipients: 接收者
            priority: 优先级
            channel_type: 渠道类型过滤
            exclude_channels: 排除的渠道列表
            template_id: 模板ID
            template_vars: 模板变量
            
        Returns:
            Dict[str, str]: 各渠道的消息ID
        """
        if not self._running:
            raise NotificationError("Service is not running")
        
        # 如果使用模板，渲染消息内容
        if template_id:
            title, content, message_type = self._render_template(template_id, template_vars or {})
        
        # 创建消息
        message = NotificationMessage(
            title=title,
            content=content,
            message_type=message_type,
            recipients=recipients or {},
            priority=priority
        )
        
        # 广播消息
        return await self.scheduler.broadcast_message(
            message=message,
            channel_type=channel_type,
            exclude_channels=exclude_channels,
            priority=priority
        )
    
    def _render_template(self, template_id: str, variables: Dict[str, Any]) -> tuple[str, str, str]:
        """渲染模板
        
        Args:
            template_id: 模板ID
            variables: 模板变量
            
        Returns:
            (title, content, message_type): 渲染后的内容
        """
        if template_id not in self._templates:
            raise NotificationError(f"Template not found: {template_id}")
        
        template = self._templates[template_id]
        
        try:
            # 简单的变量替换
            content = template.content
            for var, value in variables.items():
                content = content.replace(f'{{{var}}}', str(value))
            
            return template.title, content, template.message_type
            
        except Exception as e:
            raise NotificationError(f"Template rendering failed: {str(e)}")
    
    def add_template(self, template: NotificationTemplate):
        """添加模板
        
        Args:
            template: 通知模板
        """
        self._templates[template.template_id] = template
        logger.info(f"Template added: {template.template_id}")
    
    def remove_template(self, template_id: str) -> bool:
        """移除模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            bool: 是否成功移除
        """
        if template_id in self._templates:
            del self._templates[template_id]
            logger.info(f"Template removed: {template_id}")
            return True
        return False
    
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """获取模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            Optional[NotificationTemplate]: 模板对象
        """
        return self._templates.get(template_id)
    
    def list_templates(self) -> List[NotificationTemplate]:
        """列出所有模板
        
        Returns:
            List[NotificationTemplate]: 模板列表
        """
        return list(self._templates.values())
    
    async def add_channel(self, config: ChannelConfig) -> bool:
        """添加渠道
        
        Args:
            config: 渠道配置
            
        Returns:
            bool: 是否成功添加
        """
        try:
            self.channel_manager.add_channel(config)
            return True
        except Exception as e:
            logger.error(f"Failed to add channel: {e}")
            return False
    
    def remove_channel(self, name: str) -> bool:
        """移除渠道
        
        Args:
            name: 渠道名称
            
        Returns:
            bool: 是否成功移除
        """
        return self.channel_manager.remove_channel(name)
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """列出所有渠道
        
        Returns:
            List[Dict[str, Any]]: 渠道信息列表
        """
        return self.channel_manager.list_channels()
    
    async def get_message_status(self, message_id: str) -> Optional[NotificationMessage]:
        """获取消息状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[NotificationMessage]: 消息对象
        """
        return await self.scheduler.get_message_status(message_id)
    
    async def cancel_message(self, message_id: str) -> bool:
        """取消消息发送
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否成功取消
        """
        return await self.scheduler.cancel_message(message_id)
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """添加事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.scheduler.add_event_callback(event_type, callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """移除事件回调
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.scheduler.remove_event_callback(event_type, callback)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return await self.scheduler.health_check()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.scheduler.get_stats()
        stats['service'] = {
            'initialized': self._initialized,
            'running': self._running,
            'total_templates': len(self._templates)
        }
        return stats
    
    async def pause(self):
        """暂停服务"""
        await self.scheduler.pause_queue()
        logger.info("Notification service paused")
    
    async def resume(self):
        """恢复服务"""
        await self.scheduler.resume_queue()
        logger.info("Notification service resumed")
    
    async def clear_queue(self):
        """清空队列"""
        await self.scheduler.clear_queue()
        logger.info("Notification queue cleared")
    
    async def cleanup_old_messages(self, days: int = 7):
        """清理旧消息
        
        Args:
            days: 保留天数
        """
        await self.scheduler.cleanup_old_messages(days)
    
    # 便捷方法
    async def send_text(self, content: str, **kwargs) -> str:
        """发送文本消息"""
        return await self.send_notification(content=content, message_type="text", **kwargs)
    
    async def send_markdown(self, content: str, **kwargs) -> str:
        """发送Markdown消息"""
        return await self.send_notification(content=content, message_type="markdown", **kwargs)
    
    async def send_alert(self, message: str, level: str = "info", **kwargs) -> str:
        """发送告警消息"""
        priority_map = {
            "info": NotificationPriority.NORMAL,
            "warning": NotificationPriority.HIGH,
            "error": NotificationPriority.URGENT,
            "critical": NotificationPriority.URGENT
        }
        
        return await self.send_notification(
            template_id="system_alert",
            template_vars={
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            priority=priority_map.get(level, NotificationPriority.NORMAL),
            **kwargs
        )
    
    async def send_task_completion(self, task_name: str, status: str, **kwargs) -> str:
        """发送任务完成通知"""
        return await self.send_notification(
            template_id="task_completed",
            template_vars={
                "task_name": task_name,
                "status": status,
                "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            **kwargs
        )
    
    async def send_data_report(self, report_content: str, **kwargs) -> str:
        """发送数据报告"""
        return await self.send_notification(
            template_id="data_report",
            template_vars={
                "report_content": report_content,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            **kwargs
        )


# 全局服务实例
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取全局通知服务实例
    
    Returns:
        NotificationService: 通知服务实例
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def set_notification_service(service: NotificationService):
    """设置全局通知服务实例
    
    Args:
        service: 通知服务实例
    """
    global _notification_service
    _notification_service = service