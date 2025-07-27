"""多渠道通知服务

统一管理多种通知渠道，包括：
- 系统内通知
- 邮件通知
- 微信通知
- 短信通知（预留）
- 钉钉通知（预留）
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from loguru import logger

from ..models.notification import (
    Notification, NotificationTemplate, NotificationRule,
    NotificationType, NotificationStatus, NotificationPriority
)
from ..models.user import User
from ..schemas.notification import NotificationCreate
from .notification_service import NotificationService
from .wechat_service import WeChatService, WeChatConfig, MessageType, Priority
from ..core.config import settings


class ChannelType(str, Enum):
    """通知渠道类型"""
    SYSTEM = "system"  # 系统内通知
    EMAIL = "email"    # 邮件通知
    WECHAT = "wechat"  # 微信通知
    SMS = "sms"        # 短信通知
    DINGTALK = "dingtalk"  # 钉钉通知


class NotificationLevel(str, Enum):
    """通知级别"""
    INFO = "info"      # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"    # 错误
    URGENT = "urgent"  # 紧急


@dataclass
class ChannelConfig:
    """渠道配置"""
    channel_type: ChannelType
    is_enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高
    retry_count: int = 3
    retry_interval: int = 60  # 重试间隔（秒）
    config_data: Dict[str, Any] = None


@dataclass
class NotificationMessage:
    """通知消息"""
    message_id: str
    title: str
    content: str
    level: NotificationLevel
    channels: List[ChannelType]
    recipients: List[str]  # 接收者列表
    template_data: Dict[str, Any] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SendResult:
    """发送结果"""
    channel: ChannelType
    success: bool
    message: str = ""
    sent_at: Optional[datetime] = None
    error: Optional[str] = None


class MultiChannelNotificationService:
    """多渠道通知服务"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.notification_service = NotificationService(db) if db else None
        self.channels: Dict[ChannelType, ChannelConfig] = {}
        self.message_queue: List[NotificationMessage] = []
        self.sent_messages: List[NotificationMessage] = []
        
        # 初始化各种通知渠道
        self._init_channels()
        
    def _init_channels(self):
        """初始化通知渠道"""
        # 系统内通知
        self.channels[ChannelType.SYSTEM] = ChannelConfig(
            channel_type=ChannelType.SYSTEM,
            is_enabled=True,
            priority=1
        )
        
        # 邮件通知
        self.channels[ChannelType.EMAIL] = ChannelConfig(
            channel_type=ChannelType.EMAIL,
            is_enabled=bool(getattr(settings, 'SMTP_HOST', None)),
            priority=2,
            config_data={
                'smtp_host': getattr(settings, 'SMTP_HOST', ''),
                'smtp_port': getattr(settings, 'SMTP_PORT', 587),
                'smtp_user': getattr(settings, 'SMTP_USER', ''),
                'smtp_password': getattr(settings, 'SMTP_PASSWORD', '')
            }
        )
        
        # 微信通知
        wechat_enabled = all([
            getattr(settings, 'WECHAT_CORP_ID', None),
            getattr(settings, 'WECHAT_CORP_SECRET', None),
            getattr(settings, 'WECHAT_AGENT_ID', None)
        ])
        
        self.channels[ChannelType.WECHAT] = ChannelConfig(
            channel_type=ChannelType.WECHAT,
            is_enabled=wechat_enabled,
            priority=3,
            config_data={
                'corp_id': getattr(settings, 'WECHAT_CORP_ID', ''),
                'corp_secret': getattr(settings, 'WECHAT_CORP_SECRET', ''),
                'agent_id': getattr(settings, 'WECHAT_AGENT_ID', '')
            }
        )
        
        # 初始化微信服务
        if wechat_enabled:
            wechat_config = WeChatConfig(
                corp_id=getattr(settings, 'WECHAT_CORP_ID', ''),
                corp_secret=getattr(settings, 'WECHAT_CORP_SECRET', ''),
                agent_id=getattr(settings, 'WECHAT_AGENT_ID', '')
            )
            self.wechat_service = WeChatService(wechat_config)
        else:
            self.wechat_service = None
        
        # 短信通知（预留）
        self.channels[ChannelType.SMS] = ChannelConfig(
            channel_type=ChannelType.SMS,
            is_enabled=False,  # 暂未实现
            priority=4
        )
        
        logger.info(f"初始化通知渠道完成，启用渠道: {[ch.value for ch, config in self.channels.items() if config.is_enabled]}")
    
    async def send_notification(
        self,
        title: str,
        content: str,
        level: NotificationLevel,
        recipients: List[str],
        channels: Optional[List[ChannelType]] = None,
        template_data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """发送通知
        
        Args:
            title: 通知标题
            content: 通知内容
            level: 通知级别
            recipients: 接收者列表（用户ID或特殊标识如@all）
            channels: 指定发送渠道，为空则根据级别自动选择
            template_data: 模板数据
            scheduled_at: 计划发送时间
            
        Returns:
            发送结果
        """
        # 生成消息ID
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 如果未指定渠道，根据级别自动选择
        if not channels:
            channels = self._select_channels_by_level(level)
        
        # 创建通知消息
        message = NotificationMessage(
            message_id=message_id,
            title=title,
            content=content,
            level=level,
            channels=channels,
            recipients=recipients,
            template_data=template_data or {},
            scheduled_at=scheduled_at
        )
        
        # 如果是立即发送
        if not scheduled_at:
            results = await self._send_message(message)
        else:
            # 加入计划发送队列
            self.message_queue.append(message)
            results = {"status": "scheduled", "message_id": message_id}
        
        return {
            "message_id": message_id,
            "results": results,
            "channels": [ch.value for ch in channels],
            "recipients_count": len(recipients)
        }
    
    def _select_channels_by_level(self, level: NotificationLevel) -> List[ChannelType]:
        """根据通知级别选择渠道"""
        enabled_channels = [ch for ch, config in self.channels.items() if config.is_enabled]
        
        if level == NotificationLevel.INFO:
            return [ChannelType.SYSTEM]
        elif level == NotificationLevel.WARNING:
            return [ChannelType.SYSTEM, ChannelType.EMAIL]
        elif level == NotificationLevel.ERROR:
            return [ChannelType.SYSTEM, ChannelType.EMAIL, ChannelType.WECHAT]
        elif level == NotificationLevel.URGENT:
            return enabled_channels  # 所有可用渠道
        else:
            return [ChannelType.SYSTEM]
    
    async def _send_message(self, message: NotificationMessage) -> List[SendResult]:
        """发送消息到指定渠道"""
        results = []
        
        # 按优先级排序渠道
        sorted_channels = sorted(
            message.channels,
            key=lambda ch: self.channels[ch].priority
        )
        
        for channel in sorted_channels:
            if not self.channels[channel].is_enabled:
                results.append(SendResult(
                    channel=channel,
                    success=False,
                    error="Channel is disabled"
                ))
                continue
            
            try:
                result = await self._send_to_channel(channel, message)
                results.append(result)
                
                # 如果是紧急通知且发送成功，记录日志
                if message.level == NotificationLevel.URGENT and result.success:
                    logger.warning(f"紧急通知已发送: {message.title} -> {channel.value}")
                    
            except Exception as e:
                logger.error(f"发送到渠道 {channel.value} 失败: {str(e)}")
                results.append(SendResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                ))
        
        # 记录发送历史
        self.sent_messages.append(message)
        
        return results
    
    async def _send_to_channel(self, channel: ChannelType, message: NotificationMessage) -> SendResult:
        """发送到指定渠道"""
        if channel == ChannelType.SYSTEM:
            return await self._send_system_notification(message)
        elif channel == ChannelType.EMAIL:
            return await self._send_email_notification(message)
        elif channel == ChannelType.WECHAT:
            return await self._send_wechat_notification(message)
        elif channel == ChannelType.SMS:
            return await self._send_sms_notification(message)
        else:
            return SendResult(
                channel=channel,
                success=False,
                error="Unsupported channel"
            )
    
    async def _send_system_notification(self, message: NotificationMessage) -> SendResult:
        """发送系统内通知"""
        try:
            # 为每个接收者创建系统通知
            for recipient in message.recipients:
                if recipient == "@all":
                    # 发送给所有用户
                    users = self.db.query(User).filter(User.is_active == True).all()
                    for user in users:
                        notification_data = NotificationCreate(
                            title=message.title,
                            content=message.content,
                            notification_type=NotificationType.SYSTEM,
                            priority=self._get_notification_priority(message.level),
                            recipient_id=user.id
                        )
                        self.notification_service.create_notification(notification_data)
                else:
                    # 发送给指定用户
                    try:
                        user_id = int(recipient)
                        notification_data = NotificationCreate(
                            title=message.title,
                            content=message.content,
                            notification_type=NotificationType.SYSTEM,
                            priority=self._get_notification_priority(message.level),
                            recipient_id=user_id
                        )
                        self.notification_service.create_notification(notification_data)
                    except ValueError:
                        logger.warning(f"无效的用户ID: {recipient}")
                        continue
            
            return SendResult(
                channel=ChannelType.SYSTEM,
                success=True,
                message="System notification sent",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            return SendResult(
                channel=ChannelType.SYSTEM,
                success=False,
                error=str(e)
            )
    
    async def _send_email_notification(self, message: NotificationMessage) -> SendResult:
        """发送邮件通知"""
        try:
            # 获取接收者邮箱
            email_recipients = []
            for recipient in message.recipients:
                if recipient == "@all":
                    users = self.db.query(User).filter(
                        User.is_active == True,
                        User.email.isnot(None)
                    ).all()
                    email_recipients.extend([user.email for user in users if user.email])
                else:
                    try:
                        user_id = int(recipient)
                        user = self.db.query(User).filter(User.id == user_id).first()
                        if user and user.email:
                            email_recipients.append(user.email)
                    except ValueError:
                        # 可能直接是邮箱地址
                        if "@" in recipient:
                            email_recipients.append(recipient)
            
            if not email_recipients:
                return SendResult(
                    channel=ChannelType.EMAIL,
                    success=False,
                    error="No valid email recipients"
                )
            
            # 为每个邮箱创建邮件通知
            for email in email_recipients:
                notification_data = NotificationCreate(
                    title=message.title,
                    content=message.content,
                    notification_type=NotificationType.EMAIL,
                    priority=self._get_notification_priority(message.level),
                    recipient_email=email
                )
                self.notification_service.create_notification(notification_data)
            
            return SendResult(
                channel=ChannelType.EMAIL,
                success=True,
                message=f"Email sent to {len(email_recipients)} recipients",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            return SendResult(
                channel=ChannelType.EMAIL,
                success=False,
                error=str(e)
            )
    
    async def _send_wechat_notification(self, message: NotificationMessage) -> SendResult:
        """发送微信通知"""
        try:
            if not self.wechat_service:
                return SendResult(
                    channel=ChannelType.WECHAT,
                    success=False,
                    error="WeChat service not initialized"
                )
            
            # 获取微信接收者
            wechat_recipients = []
            for recipient in message.recipients:
                if recipient == "@all":
                    wechat_recipients = ["@all"]
                    break
                else:
                    try:
                        user_id = int(recipient)
                        user = self.db.query(User).filter(User.id == user_id).first()
                        if user and hasattr(user, 'wechat_id') and user.wechat_id:
                            wechat_recipients.append(user.wechat_id)
                    except ValueError:
                        # 可能直接是微信ID
                        wechat_recipients.append(recipient)
            
            if not wechat_recipients:
                return SendResult(
                    channel=ChannelType.WECHAT,
                    success=False,
                    error="No valid WeChat recipients"
                )
            
            # 发送微信消息
            content = f"{message.title}\n\n{message.content}"
            success = await self.wechat_service.send_text_message(wechat_recipients, content)
            
            return SendResult(
                channel=ChannelType.WECHAT,
                success=success,
                message="WeChat message sent" if success else "WeChat message failed",
                sent_at=datetime.now() if success else None
            )
            
        except Exception as e:
            return SendResult(
                channel=ChannelType.WECHAT,
                success=False,
                error=str(e)
            )
    
    async def _send_sms_notification(self, message: NotificationMessage) -> SendResult:
        """发送短信通知（预留）"""
        return SendResult(
            channel=ChannelType.SMS,
            success=False,
            error="SMS channel not implemented yet"
        )
    
    def _get_notification_priority(self, level: NotificationLevel) -> NotificationPriority:
        """将通知级别转换为通知优先级"""
        mapping = {
            NotificationLevel.INFO: NotificationPriority.LOW,
            NotificationLevel.WARNING: NotificationPriority.MEDIUM,
            NotificationLevel.ERROR: NotificationPriority.HIGH,
            NotificationLevel.URGENT: NotificationPriority.URGENT
        }
        return mapping.get(level, NotificationPriority.MEDIUM)
    
    async def process_scheduled_messages(self) -> Dict[str, Any]:
        """处理计划发送的通知消息"""
        try:
            logger.info("开始处理计划发送的通知")
            now = datetime.now()
            ready_messages = [
                msg for msg in self.message_queue
                if msg.scheduled_at and msg.scheduled_at <= now
            ]
            
            processed_count = 0
            for message in ready_messages:
                try:
                    await self._send_message(message)
                    self.message_queue.remove(message)
                    processed_count += 1
                    logger.info(f"计划消息已发送: {message.message_id}")
                except Exception as e:
                    logger.error(f"发送计划消息失败: {message.message_id}, 错误: {str(e)}")
            
            return {
                "success": True,
                "processed_count": processed_count,
                "message": "计划通知处理完成"
            }
        except Exception as e:
            logger.error(f"处理计划通知失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_count": 0
            }
    
    def get_channel_status(self) -> Dict[str, Any]:
        """获取渠道状态"""
        status = {}
        for channel_type, config in self.channels.items():
            status[channel_type.value] = {
                "enabled": config.is_enabled,
                "priority": config.priority,
                "retry_count": config.retry_count,
                "retry_interval": config.retry_interval
            }
        return status
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取发送统计"""
        total_sent = len(self.sent_messages)
        pending_count = len(self.message_queue)
        
        # 按渠道统计
        channel_stats = {}
        for channel in ChannelType:
            channel_stats[channel.value] = {
                "sent_count": sum(1 for msg in self.sent_messages if channel in msg.channels),
                "enabled": self.channels[channel].is_enabled
            }
        
        # 按级别统计
        level_stats = {}
        for level in NotificationLevel:
            level_stats[level.value] = sum(1 for msg in self.sent_messages if msg.level == level)
        
        return {
            "total_sent": total_sent,
            "pending_count": pending_count,
            "channel_stats": channel_stats,
            "level_stats": level_stats,
            "last_sent_at": max([msg.created_at for msg in self.sent_messages]) if self.sent_messages else None
        }
    
    def get_channels_for_level(self, level: NotificationLevel) -> List[ChannelType]:
        """根据通知级别获取应使用的渠道列表"""
        if level == NotificationLevel.URGENT:
            return [ChannelType.SYSTEM, ChannelType.EMAIL, ChannelType.WECHAT, ChannelType.SMS]
        elif level == NotificationLevel.ERROR:
            return [ChannelType.SYSTEM, ChannelType.EMAIL, ChannelType.WECHAT]
        elif level == NotificationLevel.WARNING:
            return [ChannelType.SYSTEM, ChannelType.EMAIL]
        else:  # INFO
            return [ChannelType.SYSTEM]
    
    # 便捷方法
    async def send_info(self, title: str, content: str, recipients: List[str], **kwargs):
        """发送信息级通知"""
        return await self.send_notification(title, content, NotificationLevel.INFO, recipients, **kwargs)
    
    async def send_warning(self, title: str, content: str, recipients: List[str], **kwargs):
        """发送警告级通知"""
        return await self.send_notification(title, content, NotificationLevel.WARNING, recipients, **kwargs)
    
    async def send_error(self, title: str, content: str, recipients: List[str], **kwargs):
        """发送错误级通知"""
        return await self.send_notification(title, content, NotificationLevel.ERROR, recipients, **kwargs)
    
    async def send_urgent(self, title: str, content: str, recipients: List[str], **kwargs):
        """发送紧急级通知"""
        return await self.send_notification(title, content, NotificationLevel.URGENT, recipients, **kwargs)