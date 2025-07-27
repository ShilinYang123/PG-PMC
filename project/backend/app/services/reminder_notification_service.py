"""催办通知集成服务

将催办系统与多渠道通知系统整合，实现：
- 催办创建时的通知
- 催办升级时的通知
- 催办响应时的通知
- 定时催办检查和通知
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from loguru import logger

from ..models.reminder import Reminder, ReminderType, ReminderLevel, ReminderStatus
from ..models.user import User
from ..models.order import Order
from ..models.production_plan import ProductionPlan
from .multi_channel_notification_service import (
    MultiChannelNotificationService, 
    NotificationLevel, 
    ChannelType
)
from .reminder_service import ReminderService
from ..core.config import settings


class ReminderNotificationService:
    """催办通知集成服务"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.reminder_service = ReminderService(db) if db else None
        self.notification_service = MultiChannelNotificationService(db)
        
        # 催办级别与通知级别的映射
        self.level_mapping = {
            ReminderLevel.LOW: NotificationLevel.INFO,
            ReminderLevel.NORMAL: NotificationLevel.WARNING,
            ReminderLevel.HIGH: NotificationLevel.ERROR,
            ReminderLevel.URGENT: NotificationLevel.URGENT
        }
    
    async def create_reminder_with_notification(
        self,
        reminder_type: ReminderType,
        target_id: int,
        title: str,
        content: str,
        level: ReminderLevel = ReminderLevel.NORMAL,
        assignee_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
        notify_channels: Optional[List[ChannelType]] = None
    ) -> Dict[str, Any]:
        """创建催办并发送通知
        
        Args:
            reminder_type: 催办类型
            target_id: 目标对象ID
            title: 催办标题
            content: 催办内容
            level: 催办级别
            assignee_id: 指定处理人ID
            due_date: 截止时间
            notify_channels: 指定通知渠道
            
        Returns:
            创建结果和通知结果
        """
        try:
            # 创建催办记录
            reminder_id = self.reminder_service.create_reminder(
                reminder_type=reminder_type,
                target_id=target_id,
                title=title,
                content=content,
                level=level,
                assignee_id=assignee_id,
                due_date=due_date
            )
            
            if not reminder_id:
                return {
                    "success": False,
                    "error": "Failed to create reminder"
                }
            
            # 获取催办记录
            reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if not reminder:
                return {
                    "success": False,
                    "error": "Reminder not found after creation"
                }
            
            # 确定通知接收者
            recipients = self._get_notification_recipients(reminder)
            
            # 生成通知内容
            notification_title, notification_content = self._generate_notification_content(
                reminder, "created"
            )
            
            # 发送通知
            notification_level = self.level_mapping.get(level, NotificationLevel.WARNING)
            notification_result = await self.notification_service.send_notification(
                title=notification_title,
                content=notification_content,
                level=notification_level,
                recipients=recipients,
                channels=notify_channels,
                template_data={
                    "reminder_id": reminder_id,
                    "reminder_type": reminder_type.value,
                    "target_id": target_id,
                    "level": level.value,
                    "due_date": due_date.isoformat() if due_date else None
                }
            )
            
            logger.info(f"催办创建成功并发送通知: ID={reminder_id}, 类型={reminder_type.value}")
            
            return {
                "success": True,
                "reminder_id": reminder_id,
                "notification_result": notification_result,
                "recipients": recipients
            }
            
        except Exception as e:
            logger.error(f"创建催办通知失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_urgent(self, title: str, content: str, recipients: List[str]) -> Dict[str, Any]:
        """发送紧急通知"""
        return await self.send_notification(
            title=title,
            content=content,
            level="urgent",
            recipients=recipients
        )
    
    async def send_reminder_created_notification(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送催办创建通知"""
        try:
            # 构建通知内容
            content = f"""催办详情：
类型：{reminder_data.get('type', '未知')}
级别：{reminder_data.get('level', '普通')}
内容：{reminder_data.get('content', '')}
截止时间：{reminder_data.get('due_date', '未设置')}

请及时处理此催办事项。"""
            
            # 根据催办级别选择通知级别
            notification_level = self._get_notification_level(reminder_data.get('level'))
            
            # 发送通知
            result = await self.notification_service.send_notification(
                title=f"新催办通知 - {reminder_data.get('title', '未命名催办')}",
                content=content,
                level=notification_level,
                recipients=[reminder_data.get('assignee_id', 'unknown')]
            )
            
            return {
                "success": True,
                "notification_result": result,
                "message": "催办创建通知发送成功"
            }
            
        except Exception as e:
            logger.error(f"发送催办创建通知失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "催办创建通知发送失败"
            }
    
    async def send_reminder_escalated_notification(self, reminder_data: Dict[str, Any], new_level) -> Dict[str, Any]:
        """发送催办升级通知"""
        try:
            # 构建通知内容
            content = f"""催办升级详情：
原级别：{reminder_data.get('level', '未知')}
新级别：{new_level}
催办内容：{reminder_data.get('content', '')}

此催办已升级，请优先处理。"""
            
            # 发送紧急通知
            result = await self.notification_service.send_urgent(
                title=f"催办升级通知 - {reminder_data.get('title', '未命名催办')}",
                content=content,
                recipients=[reminder_data.get('assignee_id', 'unknown')]
            )
            
            return {
                "success": True,
                "notification_result": result,
                "message": "催办升级通知发送成功"
            }
            
        except Exception as e:
            logger.error(f"发送催办升级通知失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "催办升级通知发送失败"
            }
    
    def _get_notification_level(self, reminder_level: str) -> str:
        """根据催办级别获取通知级别"""
        level_mapping = {
            "低": "info",
            "普通": "warning", 
            "高": "error",
            "紧急": "urgent"
        }
        return level_mapping.get(reminder_level, "warning")
    
    async def check_overdue_reminders(self) -> Dict[str, Any]:
        """检查逾期催办并发送通知"""
        try:
            logger.info("开始检查逾期催办")
            return {
                "success": True,
                "processed_count": 0,
                "message": "逾期催办检查完成"
            }
        except Exception as e:
            logger.error(f"检查逾期催办失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_count": 0
            }
    
    async def send_daily_reminder_summary(self) -> Dict[str, Any]:
        """发送每日催办汇总"""
        try:
            from datetime import date
            today = date.today()
            logger.info(f"发送每日催办汇总: {today}")
            return {
                "success": True,
                "date": today.isoformat(),
                "message": "每日催办汇总发送成功"
            }
        except Exception as e:
            logger.error(f"发送每日催办汇总失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def escalate_reminder_with_notification(
        self,
        reminder_id: int,
        new_level: ReminderLevel,
        escalation_reason: str = ""
    ) -> Dict[str, Any]:
        """升级催办并发送通知"""
        try:
            # 获取催办记录
            reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if not reminder:
                return {
                    "success": False,
                    "error": "Reminder not found"
                }
            
            old_level = reminder.level
            
            # 升级催办
            success = self.reminder_service.escalate_reminder(reminder_id, new_level)
            if not success:
                return {
                    "success": False,
                    "error": "Failed to escalate reminder"
                }
            
            # 刷新催办记录
            self.db.refresh(reminder)
            
            # 确定通知接收者（升级时通知更多人）
            recipients = self._get_escalation_recipients(reminder, old_level, new_level)
            
            # 生成通知内容
            notification_title, notification_content = self._generate_notification_content(
                reminder, "escalated", {
                    "old_level": old_level.value,
                    "new_level": new_level.value,
                    "escalation_reason": escalation_reason
                }
            )
            
            # 发送通知
            notification_level = self.level_mapping.get(new_level, NotificationLevel.WARNING)
            notification_result = await self.notification_service.send_notification(
                title=notification_title,
                content=notification_content,
                level=notification_level,
                recipients=recipients,
                template_data={
                    "reminder_id": reminder_id,
                    "old_level": old_level.value,
                    "new_level": new_level.value,
                    "escalation_reason": escalation_reason
                }
            )
            
            logger.warning(f"催办已升级: ID={reminder_id}, {old_level.value} -> {new_level.value}")
            
            return {
                "success": True,
                "reminder_id": reminder_id,
                "old_level": old_level.value,
                "new_level": new_level.value,
                "notification_result": notification_result,
                "recipients": recipients
            }
            
        except Exception as e:
            logger.error(f"升级催办通知失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def respond_reminder_with_notification(
        self,
        reminder_id: int,
        response_content: str,
        responder_id: int
    ) -> Dict[str, Any]:
        """响应催办并发送通知"""
        try:
            # 响应催办
            success = self.reminder_service.mark_reminder_responded(
                record_id=reminder_id,
                response_content=response_content,
                responder_id=responder_id
            )
            
            if not success:
                return {
                    "success": False,
                    "error": "Failed to respond to reminder"
                }
            
            # 获取催办记录
            reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if not reminder:
                return {
                    "success": False,
                    "error": "Reminder not found after response"
                }
            
            # 确定通知接收者（通知创建者和相关人员）
            recipients = self._get_response_recipients(reminder, responder_id)
            
            # 生成通知内容
            notification_title, notification_content = self._generate_notification_content(
                reminder, "responded", {
                    "response_content": response_content,
                    "responder_id": responder_id
                }
            )
            
            # 发送通知
            notification_result = await self.notification_service.send_notification(
                title=notification_title,
                content=notification_content,
                level=NotificationLevel.INFO,
                recipients=recipients,
                template_data={
                    "reminder_id": reminder_id,
                    "response_content": response_content,
                    "responder_id": responder_id
                }
            )
            
            logger.info(f"催办已响应: ID={reminder_id}, 响应人={responder_id}")
            
            return {
                "success": True,
                "reminder_id": reminder_id,
                "notification_result": notification_result,
                "recipients": recipients
            }
            
        except Exception as e:
            logger.error(f"响应催办通知失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_overdue_reminders(self) -> Dict[str, Any]:
        """检查逾期催办并发送通知"""
        try:
            now = datetime.now()
            
            # 查找逾期的催办
            overdue_reminders = self.db.query(Reminder).filter(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_date.isnot(None),
                Reminder.due_date < now
            ).all()
            
            results = []
            
            for reminder in overdue_reminders:
                # 计算逾期时间
                overdue_hours = int((now - reminder.due_date).total_seconds() / 3600)
                
                # 确定是否需要升级
                should_escalate = self._should_escalate_overdue(reminder, overdue_hours)
                
                if should_escalate:
                    # 升级催办
                    new_level = self._get_escalated_level(reminder.level)
                    escalation_result = await self.escalate_reminder_with_notification(
                        reminder.id,
                        new_level,
                        f"逾期 {overdue_hours} 小时自动升级"
                    )
                    results.append({
                        "reminder_id": reminder.id,
                        "action": "escalated",
                        "overdue_hours": overdue_hours,
                        "result": escalation_result
                    })
                else:
                    # 发送逾期提醒
                    recipients = self._get_notification_recipients(reminder)
                    notification_title = f"催办逾期提醒: {reminder.title}"
                    notification_content = f"催办已逾期 {overdue_hours} 小时，请及时处理。\n\n原内容: {reminder.content}"
                    
                    notification_result = await self.notification_service.send_notification(
                        title=notification_title,
                        content=notification_content,
                        level=self.level_mapping.get(reminder.level, NotificationLevel.WARNING),
                        recipients=recipients,
                        template_data={
                            "reminder_id": reminder.id,
                            "overdue_hours": overdue_hours
                        }
                    )
                    
                    results.append({
                        "reminder_id": reminder.id,
                        "action": "notified",
                        "overdue_hours": overdue_hours,
                        "result": notification_result
                    })
            
            logger.info(f"逾期催办检查完成，处理了 {len(results)} 个逾期催办")
            
            return {
                "success": True,
                "processed_count": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"检查逾期催办失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_notification_recipients(self, reminder: Reminder) -> List[str]:
        """获取通知接收者"""
        recipients = []
        
        # 添加指定处理人
        if reminder.assignee_id:
            recipients.append(str(reminder.assignee_id))
        
        # 添加创建者
        if reminder.created_by:
            recipients.append(str(reminder.created_by))
        
        # 根据催办类型添加相关人员
        if reminder.reminder_type == ReminderType.ORDER_DUE:
            # 订单催办：添加销售和生产负责人
            order = self.db.query(Order).filter(Order.id == reminder.target_id).first()
            if order:
                if order.salesperson_id:
                    recipients.append(str(order.salesperson_id))
                # 可以添加更多相关人员
        
        elif reminder.reminder_type == ReminderType.PRODUCTION_DELAY:
            # 生产延期催办：添加生产负责人
            plan = self.db.query(ProductionPlan).filter(ProductionPlan.id == reminder.target_id).first()
            if plan:
                if plan.responsible_person_id:
                    recipients.append(str(plan.responsible_person_id))
        
        # 去重
        return list(set(recipients))
    
    def _get_escalation_recipients(self, reminder: Reminder, old_level: ReminderLevel, new_level: ReminderLevel) -> List[str]:
        """获取升级通知接收者（包含更多管理人员）"""
        recipients = self._get_notification_recipients(reminder)
        
        # 升级到高级别时，添加管理人员
        if new_level in [ReminderLevel.HIGH, ReminderLevel.URGENT]:
            # 查找管理员用户
            managers = self.db.query(User).filter(
                User.is_active == True,
                User.role.in_(['admin', 'manager'])
            ).all()
            
            for manager in managers:
                recipients.append(str(manager.id))
        
        return list(set(recipients))
    
    def _get_response_recipients(self, reminder: Reminder, responder_id: int) -> List[str]:
        """获取响应通知接收者"""
        recipients = []
        
        # 添加创建者
        if reminder.created_by and reminder.created_by != responder_id:
            recipients.append(str(reminder.created_by))
        
        # 添加指定处理人（如果不是响应者）
        if reminder.assignee_id and reminder.assignee_id != responder_id:
            recipients.append(str(reminder.assignee_id))
        
        return list(set(recipients))
    
    def _generate_notification_content(self, reminder: Reminder, action: str, extra_data: Dict = None) -> tuple:
        """生成通知内容"""
        extra_data = extra_data or {}
        
        if action == "created":
            title = f"新催办: {reminder.title}"
            content = f"催办类型: {reminder.reminder_type.value}\n"
            content += f"催办级别: {reminder.level.value}\n"
            content += f"催办内容: {reminder.content}\n"
            if reminder.due_date:
                content += f"截止时间: {reminder.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            content += f"创建时间: {reminder.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        elif action == "escalated":
            title = f"催办升级: {reminder.title}"
            content = f"催办已从 {extra_data.get('old_level', '')} 升级到 {extra_data.get('new_level', '')}\n"
            if extra_data.get('escalation_reason'):
                content += f"升级原因: {extra_data['escalation_reason']}\n"
            content += f"催办内容: {reminder.content}\n"
            content += f"升级时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        elif action == "responded":
            title = f"催办已响应: {reminder.title}"
            content = f"响应内容: {extra_data.get('response_content', '')}\n"
            content += f"响应时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        else:
            title = f"催办通知: {reminder.title}"
            content = reminder.content
        
        return title, content
    
    def _should_escalate_overdue(self, reminder: Reminder, overdue_hours: int) -> bool:
        """判断是否应该升级逾期催办"""
        # 根据当前级别和逾期时间决定是否升级
        if reminder.level == ReminderLevel.LOW and overdue_hours >= 24:  # 低级别逾期24小时升级
            return True
        elif reminder.level == ReminderLevel.NORMAL and overdue_hours >= 12:  # 普通级别逾期12小时升级
            return True
        elif reminder.level == ReminderLevel.HIGH and overdue_hours >= 6:  # 高级别逾期6小时升级
            return True
        
        return False
    
    def _get_escalated_level(self, current_level: ReminderLevel) -> ReminderLevel:
        """获取升级后的级别"""
        if current_level == ReminderLevel.LOW:
            return ReminderLevel.NORMAL
        elif current_level == ReminderLevel.NORMAL:
            return ReminderLevel.HIGH
        elif current_level == ReminderLevel.HIGH:
            return ReminderLevel.URGENT
        else:
            return current_level  # 已经是最高级别
    
    async def send_daily_reminder_summary(self, target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """发送每日催办汇总"""
        try:
            if not target_date:
                target_date = datetime.now().date()
            
            # 统计当日催办情况
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date, datetime.max.time())
            
            # 新增催办
            new_reminders = self.db.query(Reminder).filter(
                Reminder.created_at >= start_time,
                Reminder.created_at <= end_time
            ).all()
            
            # 已响应催办
            responded_reminders = self.db.query(Reminder).filter(
                Reminder.responded_at >= start_time,
                Reminder.responded_at <= end_time,
                Reminder.status == ReminderStatus.RESPONDED
            ).all()
            
            # 待处理催办
            pending_reminders = self.db.query(Reminder).filter(
                Reminder.status == ReminderStatus.PENDING
            ).all()
            
            # 逾期催办
            overdue_reminders = self.db.query(Reminder).filter(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_date.isnot(None),
                Reminder.due_date < datetime.now()
            ).all()
            
            # 生成汇总内容
            title = f"催办系统日报 - {target_date.strftime('%Y年%m月%d日')}"
            content = f"📊 催办系统日报\n\n"
            content += f"📝 新增催办: {len(new_reminders)} 个\n"
            content += f"✅ 已响应催办: {len(responded_reminders)} 个\n"
            content += f"⏳ 待处理催办: {len(pending_reminders)} 个\n"
            content += f"🚨 逾期催办: {len(overdue_reminders)} 个\n\n"
            
            if overdue_reminders:
                content += "⚠️ 逾期催办详情:\n"
                for reminder in overdue_reminders[:5]:  # 只显示前5个
                    overdue_hours = int((datetime.now() - reminder.due_date).total_seconds() / 3600)
                    content += f"• {reminder.title} (逾期{overdue_hours}小时)\n"
                if len(overdue_reminders) > 5:
                    content += f"• ... 还有 {len(overdue_reminders) - 5} 个逾期催办\n"
            
            # 发送给管理员
            managers = self.db.query(User).filter(
                User.is_active == True,
                User.role.in_(['admin', 'manager'])
            ).all()
            
            recipients = [str(manager.id) for manager in managers]
            
            notification_result = await self.notification_service.send_notification(
                title=title,
                content=content,
                level=NotificationLevel.INFO,
                recipients=recipients,
                channels=[ChannelType.SYSTEM, ChannelType.EMAIL],
                template_data={
                    "date": target_date.isoformat(),
                    "new_count": len(new_reminders),
                    "responded_count": len(responded_reminders),
                    "pending_count": len(pending_reminders),
                    "overdue_count": len(overdue_reminders)
                }
            )
            
            logger.info(f"每日催办汇总已发送: {target_date}")
            
            return {
                "success": True,
                "date": target_date.isoformat(),
                "statistics": {
                    "new_count": len(new_reminders),
                    "responded_count": len(responded_reminders),
                    "pending_count": len(pending_reminders),
                    "overdue_count": len(overdue_reminders)
                },
                "notification_result": notification_result
            }
            
        except Exception as e:
            logger.error(f"发送每日催办汇总失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }