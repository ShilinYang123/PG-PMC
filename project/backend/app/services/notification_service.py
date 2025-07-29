import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.notification import (
    Notification, NotificationTemplate, NotificationRule,
    NotificationType, NotificationStatus, NotificationPriority
)
from ..models.user import User
from ..schemas.notification import (
    NotificationCreate, NotificationUpdate, BatchNotificationCreate,
    NotificationQuery, NotificationStats
)
from ..core.config import settings
from ..services.wechat_service import WeChatService
from ..services.sms_service import sms_service
from ..services.email_service import email_service

class NotificationService:
    """通知服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        # 创建默认的微信配置
        from ..services.wechat_service import WeChatConfig
        wechat_config = WeChatConfig(
            corp_id=getattr(settings, 'WECHAT_CORP_ID', ''),
            corp_secret=getattr(settings, 'WECHAT_CORP_SECRET', ''),
            agent_id=getattr(settings, 'WECHAT_AGENT_ID', '')
        )
        self.wechat_service = WeChatService(wechat_config)
    
    def create_notification(self, notification_data: NotificationCreate, sender_id: Optional[int] = None) -> Notification:
        """创建单个通知"""
        notification = Notification(
            title=notification_data.title,
            content=notification_data.content,
            notification_type=notification_data.notification_type,
            priority=notification_data.priority,
            sender_id=sender_id or notification_data.sender_id,
            recipient_id=notification_data.recipient_id,
            recipient_email=notification_data.recipient_email,
            recipient_phone=notification_data.recipient_phone,
            recipient_wechat=notification_data.recipient_wechat,
            related_type=notification_data.related_type,
            related_id=notification_data.related_id,
            scheduled_at=notification_data.scheduled_at
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # 如果没有设置计划发送时间，立即发送
        if not notification.scheduled_at:
            self._send_notification(notification)
        
        return notification
    
    def create_batch_notifications(self, batch_data: BatchNotificationCreate, sender_id: Optional[int] = None) -> List[Notification]:
        """批量创建通知"""
        template = self.get_template(batch_data.template_id)
        if not template:
            raise ValueError(f"Template {batch_data.template_id} not found")
        
        notifications = []
        
        for recipient_id in batch_data.recipients:
            # 获取接收者信息
            recipient = self.db.query(User).filter(User.id == recipient_id).first()
            if not recipient:
                continue
            
            # 渲染模板
            title = self._render_template(template.title_template, batch_data.template_data)
            content = self._render_template(template.content_template, batch_data.template_data)
            
            # 为每种通知类型创建通知
            for notification_type in batch_data.notification_types:
                notification = Notification(
                    title=title,
                    content=content,
                    notification_type=notification_type,
                    priority=batch_data.priority,
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    recipient_email=recipient.email,
                    recipient_phone=getattr(recipient, 'phone', None),
                    recipient_wechat=getattr(recipient, 'wechat_id', None),
                    related_type=batch_data.related_type,
                    related_id=batch_data.related_id,
                    scheduled_at=batch_data.scheduled_at
                )
                
                self.db.add(notification)
                notifications.append(notification)
        
        self.db.commit()
        
        # 发送未计划的通知
        for notification in notifications:
            if not notification.scheduled_at:
                self._send_notification(notification)
        
        return notifications
    
    def send_notification(self, notification_id: int) -> bool:
        """发送指定通知"""
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return False
        
        return self._send_notification(notification)
    
    def _send_notification(self, notification: Notification) -> bool:
        """内部发送通知方法"""
        try:
            notification.status = NotificationStatus.SENDING
            self.db.commit()
            
            success = False
            
            if notification.notification_type == NotificationType.EMAIL:
                success = self._send_email(notification)
            elif notification.notification_type == NotificationType.WECHAT:
                success = self._send_wechat(notification)
            elif notification.notification_type == NotificationType.SMS:
                success = self._send_sms(notification)
            elif notification.notification_type == NotificationType.SYSTEM:
                success = True  # 系统通知只需要存储在数据库中
            
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                notification.error_message = None
            else:
                notification.status = NotificationStatus.FAILED
                notification.retry_count += 1
            
            self.db.commit()
            return success
            
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.retry_count += 1
            notification.error_message = str(e)
            self.db.commit()
            return False
    
    def _send_email(self, notification: Notification) -> bool:
        """发送邮件通知"""
        try:
            if not notification.recipient_email:
                return False
            
            # 使用新的邮件服务
            import asyncio
            from ..services.email_service import EmailMessage
            
            message = EmailMessage(
                to_emails=[notification.recipient_email],
                subject=notification.title,
                html_content=f"<html><body><h3>{notification.title}</h3><p>{notification.content}</p></body></html>",
                text_content=notification.content
            )
            
            # 在同步函数中运行异步代码
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(email_service.send_email(message))
            loop.close()
            
            return result
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def _send_wechat(self, notification: Notification) -> bool:
        """发送微信通知"""
        try:
            if not notification.recipient_wechat:
                return False
            
            return self.wechat_service.send_message(
                to_user=notification.recipient_wechat,
                message=f"{notification.title}\n\n{notification.content}"
            )
            
        except Exception as e:
            print(f"WeChat sending failed: {e}")
            return False
    
    def _send_sms(self, notification: Notification) -> bool:
        """发送短信通知"""
        try:
            if not notification.recipient_phone:
                return False
            
            # 使用新的短信服务
            import asyncio
            
            # 根据通知类型选择合适的短信模板
            template_id = "order_reminder"  # 默认模板
            params = {
                "message": notification.content,
                "title": notification.title
            }
            
            if "订单" in notification.title:
                template_id = "order_reminder"
            elif "生产" in notification.title or "异常" in notification.title:
                template_id = "production_alert"
            elif "交期" in notification.title:
                template_id = "delivery_warning"
            elif "质量" in notification.title:
                template_id = "quality_alert"
            
            # 在同步函数中运行异步代码
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                sms_service.send_sms(
                    phone=notification.recipient_phone,
                    template_id=template_id,
                    params=params
                )
            )
            loop.close()
            
            return result
            
        except Exception as e:
            print(f"SMS sending failed: {e}")
            return False
    
    def retry_failed_notifications(self) -> int:
        """重试失败的通知"""
        failed_notifications = self.db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.FAILED,
                Notification.retry_count < Notification.max_retry
            )
        ).all()
        
        retry_count = 0
        for notification in failed_notifications:
            if self._send_notification(notification):
                retry_count += 1
        
        return retry_count
    
    def process_scheduled_notifications(self) -> int:
        """处理计划发送的通知"""
        now = datetime.utcnow()
        scheduled_notifications = self.db.query(Notification).filter(
            and_(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_at <= now
            )
        ).all()
        
        sent_count = 0
        for notification in scheduled_notifications:
            if self._send_notification(notification):
                sent_count += 1
        
        return sent_count
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读"""
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == user_id
            )
        ).first()
        
        if notification and notification.status == NotificationStatus.SENT:
            notification.status = NotificationStatus.read
            notification.read_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def get_user_notifications(self, user_id: int, query: NotificationQuery) -> Dict[str, Any]:
        """获取用户通知列表"""
        base_query = self.db.query(Notification).filter(Notification.recipient_id == user_id)
        
        # 应用过滤条件
        if query.notification_type:
            base_query = base_query.filter(Notification.notification_type == query.notification_type)
        if query.status:
            base_query = base_query.filter(Notification.status == query.status)
        if query.priority:
            base_query = base_query.filter(Notification.priority == query.priority)
        if query.start_date:
            base_query = base_query.filter(Notification.created_at >= query.start_date)
        if query.end_date:
            base_query = base_query.filter(Notification.created_at <= query.end_date)
        
        # 计算总数
        total = base_query.count()
        
        # 分页查询
        notifications = base_query.order_by(Notification.created_at.desc()).offset(
            (query.page - 1) * query.size
        ).limit(query.size).all()
        
        return {
            "notifications": notifications,
            "total": total,
            "page": query.page,
            "size": query.size,
            "pages": (total + query.size - 1) // query.size
        }
    
    def get_notification_stats(self, user_id: Optional[int] = None) -> NotificationStats:
        """获取通知统计信息"""
        base_query = self.db.query(Notification)
        
        if user_id:
            base_query = base_query.filter(Notification.recipient_id == user_id)
        
        total_count = base_query.count()
        pending_count = base_query.filter(Notification.status == NotificationStatus.PENDING).count()
        sent_count = base_query.filter(Notification.status == NotificationStatus.SENT).count()
        failed_count = base_query.filter(Notification.status == NotificationStatus.FAILED).count()
        read_count = base_query.filter(Notification.status == NotificationStatus.read).count()
        unread_count = sent_count  # 已发送但未读的
        
        return NotificationStats(
            total_count=total_count,
            pending_count=pending_count,
            sent_count=sent_count,
            failed_count=failed_count,
            read_count=read_count,
            unread_count=unread_count
        )
    
    def get_template(self, template_id: int) -> Optional[NotificationTemplate]:
        """获取通知模板"""
        return self.db.query(NotificationTemplate).filter(
            and_(
                NotificationTemplate.id == template_id,
                NotificationTemplate.is_active == True
            )
        ).first()
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            # 简单的模板渲染，支持 {variable} 格式
            for key, value in data.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        except Exception:
            return template
    
    def trigger_notification_by_event(self, event: str, event_data: Dict[str, Any]) -> List[Notification]:
        """根据事件触发通知"""
        # 查找匹配的通知规则
        rules = self.db.query(NotificationRule).filter(
            and_(
                NotificationRule.trigger_event == event,
                NotificationRule.is_active == True
            )
        ).all()
        
        notifications = []
        
        for rule in rules:
            try:
                # 检查触发条件
                if rule.trigger_conditions:
                    conditions = json.loads(rule.trigger_conditions)
                    if not self._check_conditions(conditions, event_data):
                        continue
                
                # 解析接收者规则
                recipient_rules = json.loads(rule.recipient_rules)
                recipients = self._get_recipients_by_rules(recipient_rules, event_data)
                
                if recipients:
                    # 解析通知类型
                    notification_types = [NotificationType(t.strip()) for t in rule.notification_types.split(',')]
                    
                    # 创建批量通知
                    batch_data = BatchNotificationCreate(
                        template_id=rule.template_id,
                        notification_types=notification_types,
                        priority=rule.priority,
                        recipients=recipients,
                        template_data=event_data,
                        related_type=event_data.get('related_type'),
                        related_id=event_data.get('related_id')
                    )
                    
                    batch_notifications = self.create_batch_notifications(batch_data)
                    notifications.extend(batch_notifications)
                    
            except Exception as e:
                print(f"Error processing notification rule {rule.id}: {e}")
                continue
        
        return notifications
    
    def _check_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """检查触发条件"""
        # 简单的条件检查逻辑
        for key, expected_value in conditions.items():
            if key not in event_data or event_data[key] != expected_value:
                return False
        return True
    
    def _get_recipients_by_rules(self, recipient_rules: Dict[str, Any], event_data: Dict[str, Any]) -> List[int]:
        """根据规则获取接收者列表"""
        recipients = []
        
        # 支持多种接收者规则
        if 'user_ids' in recipient_rules:
            recipients.extend(recipient_rules['user_ids'])
        
        if 'roles' in recipient_rules:
            # 根据角色查找用户
            role_users = self.db.query(User).filter(User.role.in_(recipient_rules['roles'])).all()
            recipients.extend([user.id for user in role_users])
        
        if 'departments' in recipient_rules:
            # 根据部门查找用户
            dept_users = self.db.query(User).filter(User.department.in_(recipient_rules['departments'])).all()
            recipients.extend([user.id for user in dept_users])
        
        if 'dynamic' in recipient_rules:
            # 动态规则，从事件数据中获取
            dynamic_rule = recipient_rules['dynamic']
            if dynamic_rule in event_data:
                dynamic_recipients = event_data[dynamic_rule]
                if isinstance(dynamic_recipients, list):
                    recipients.extend(dynamic_recipients)
                else:
                    recipients.append(dynamic_recipients)
        
        return list(set(recipients))  # 去重