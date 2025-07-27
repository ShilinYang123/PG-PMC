"""催办服务

实现智能催办功能，包括：
- 自动催办规则
- 多级催办升级
- 催办记录跟踪
- 催办效果分析
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from ..models.notification import (
    Notification, NotificationTemplate, NotificationRule,
    NotificationType, NotificationStatus, NotificationPriority
)
from ..models.user import User
from ..models.reminder import ReminderRecord, ReminderRule, ReminderResponse, ReminderType, ReminderLevel, ReminderStatus
from ..schemas.notification import NotificationCreate, BatchNotificationCreate
from .notification_service import NotificationService


# 导入枚举类型和数据类（从模型中导入）
# ReminderType, ReminderLevel, ReminderStatus, ReminderRecord, ReminderRule 已从模型导入


class ReminderService:
    """催办服务类"""
    
    def __init__(self, db: Session, notification_service: NotificationService = None):
        self.db = db
        self.notification_service = notification_service
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认催办规则"""
        # 检查是否已存在默认规则
        existing_rules = self.db.query(ReminderRule).filter(
            ReminderRule.name.like("%默认%")
        ).count()
        
        if existing_rules > 0:
            return
        
        default_rules_data = [
            {
                "name": "订单交期3天催办（默认）",
                "description": "订单交期前3天自动催办",
                "reminder_type": ReminderType.ORDER_DUE,
                "trigger_conditions": {
                    "days_before_due": 3,
                    "order_status": ["in_progress", "pending"]
                },
                "initial_level": ReminderLevel.NORMAL,
                "escalation_intervals": [24, 12, 6],  # 24小时、12小时、6小时后升级
                "max_escalations": 3,
                "recipient_config": {
                    "primary": "order_responsible",
                    "escalate_to": ["production_manager", "general_manager"]
                },
                "title_template": "订单交期催办：{order_number}",
                "content_template": "订单 {order_number} 将在 {days_before_due} 天后到期，请及时处理。",
                "is_active": True,
                "created_by": 1  # 系统用户
            },
            {
                "name": "订单交期1天紧急催办（默认）",
                "description": "订单交期前1天紧急催办",
                "reminder_type": ReminderType.ORDER_DUE,
                "trigger_conditions": {
                    "days_before_due": 1,
                    "order_status": ["in_progress", "pending"]
                },
                "initial_level": ReminderLevel.URGENT,
                "escalation_intervals": [6, 3, 1],  # 6小时、3小时、1小时后升级
                "max_escalations": 3,
                "recipient_config": {
                    "primary": "order_responsible",
                    "escalate_to": ["production_manager", "general_manager", "ceo"]
                },
                "title_template": "订单交期紧急催办：{order_number}",
                "content_template": "订单 {order_number} 将在 {days_before_due} 天后到期，请紧急处理！",
                "is_active": True,
                "created_by": 1
            },
            {
                "name": "任务逾期催办（默认）",
                "description": "任务逾期2小时后自动催办",
                "reminder_type": ReminderType.TASK_OVERDUE,
                "trigger_conditions": {
                    "overdue_hours": 2,
                    "task_status": ["pending", "in_progress"]
                },
                "initial_level": ReminderLevel.HIGH,
                "escalation_intervals": [4, 8, 12],  # 4小时、8小时、12小时后升级
                "max_escalations": 3,
                "recipient_config": {
                    "primary": "task_assignee",
                    "escalate_to": ["team_leader", "department_manager"]
                },
                "title_template": "任务逾期催办：{task_name}",
                "content_template": "任务 {task_name} 已逾期 {overdue_hours} 小时，请立即处理。",
                "is_active": True,
                "created_by": 1
            },
            {
                "name": "质量问题催办（默认）",
                "description": "高严重性质量问题催办",
                "reminder_type": ReminderType.QUALITY_ISSUE,
                "trigger_conditions": {
                    "severity": "high",
                    "status": ["open", "investigating"]
                },
                "initial_level": ReminderLevel.URGENT,
                "escalation_intervals": [2, 4, 6],  # 2小时、4小时、6小时后升级
                "max_escalations": 3,
                "recipient_config": {
                    "primary": "quality_inspector",
                    "escalate_to": ["quality_manager", "production_manager"]
                },
                "title_template": "质量问题催办：{issue_description}",
                "content_template": "高严重性质量问题需要处理，问题描述：{issue_description}",
                "is_active": True,
                "created_by": 1
            },
            {
                "name": "设备维护催办（默认）",
                "description": "设备维护逾期1天后催办",
                "reminder_type": ReminderType.EQUIPMENT_MAINTENANCE,
                "trigger_conditions": {
                    "days_overdue": 1,
                    "equipment_status": "active"
                },
                "initial_level": ReminderLevel.HIGH,
                "escalation_intervals": [24, 48, 72],  # 1天、2天、3天后升级
                "max_escalations": 3,
                "recipient_config": {
                    "primary": "equipment_responsible",
                    "escalate_to": ["maintenance_manager", "production_manager"]
                },
                "title_template": "设备维护催办：{equipment_name}",
                "content_template": "设备 {equipment_name} 维护已逾期 {days_overdue} 天，请安排维护。",
                "is_active": True,
                "created_by": 1
            }
        ]
        
        # 创建默认规则
        for rule_data in default_rules_data:
            rule = ReminderRule(**rule_data)
            self.db.add(rule)
        
        try:
            self.db.commit()
            logger.info(f"初始化了 {len(default_rules_data)} 个默认催办规则")
        except Exception as e:
            self.db.rollback()
            logger.error(f"初始化默认催办规则失败: {str(e)}")
    
    def create_reminder(self, reminder_type: ReminderType, related_type: str, 
                       related_id: int, recipient_user_id: int, 
                       data: Dict[str, Any] = None, sender_user_id: int = None) -> Optional[int]:
        """创建催办记录
        
        Args:
            reminder_type: 催办类型
            related_type: 关联对象类型
            related_id: 关联对象ID
            recipient_user_id: 接收者用户ID
            data: 催办相关数据
            sender_user_id: 发送者用户ID
            
        Returns:
            催办记录ID
        """
        if data is None:
            data = {}
            
        # 查找匹配的规则
        matching_rule = self._find_matching_rule(reminder_type, data)
        if not matching_rule:
            logger.warning(f"未找到匹配的催办规则: {reminder_type}")
            return None
            
        # 生成催办内容
        title, content = self._generate_reminder_content(matching_rule, data)
        
        # 创建催办记录
        reminder_record = ReminderRecord(
            reminder_type=reminder_type,
            level=matching_rule.initial_level,
            related_type=related_type,
            related_id=related_id,
            recipient_user_id=recipient_user_id,
            sender_user_id=sender_user_id,
            title=title,
            content=content,
            data=data,
            rule_id=matching_rule.id,
            status=ReminderStatus.PENDING
        )
        
        self.db.add(reminder_record)
        
        try:
            self.db.commit()
            self.db.refresh(reminder_record)
            logger.info(f"创建催办记录: {reminder_record.id}, 类型: {reminder_type}, 接收者: {recipient_user_id}")
            return reminder_record.id
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建催办记录失败: {str(e)}")
            return None
    
    def process_pending_reminders(self) -> int:
        """处理待催办的记录"""
        now = datetime.now()
        processed_count = 0
        
        # 查询待处理的催办记录
        pending_records = self.db.query(ReminderRecord).filter(
            ReminderRecord.status == ReminderStatus.PENDING,
            ReminderRecord.next_reminder_time <= now
        ).all()
        
        for record in pending_records:
            rule = self.db.query(ReminderRule).filter(
                ReminderRule.id == record.rule_id
            ).first()
            
            if not rule:
                continue
            
            # 检查是否需要升级
            hours_since_created = (now - record.created_at).total_seconds() / 3600
            max_escalation_hours = sum(rule.escalation_intervals)
            
            if hours_since_created >= max_escalation_hours:
                self._escalate_reminder(record, rule)
                processed_count += 1
                continue
            
            # 进行下一级催办
            self._send_next_level_reminder(record, rule)
            processed_count += 1
        
        return processed_count
    
    def _send_reminder_notification(self, rule: ReminderRule, record: ReminderRecord, data: Dict[str, Any]):
        """发送催办通知"""
        # 构建通知内容
        title = record.title
        content = record.content
        
        # 这里应该调用通知服务发送通知
        # notification_service.send_notification(
        #     notification_type=NotificationType.SYSTEM,
        #     recipients=[record.recipient_user_id],
        #     title=title,
        #     content=content,
        #     priority=self._get_notification_priority(record.level)
        # )
        
        logger.info(f"发送催办通知: {record.id}, 接收者: {record.recipient_user_id}")
    
    def _send_next_level_reminder(self, record: ReminderRecord, rule: ReminderRule):
        """发送下一级催办"""
        # 升级催办级别
        if record.level == ReminderLevel.LOW:
            record.level = ReminderLevel.NORMAL
        elif record.level == ReminderLevel.NORMAL:
            record.level = ReminderLevel.HIGH
        elif record.level == ReminderLevel.HIGH:
            record.level = ReminderLevel.URGENT
        
        record.last_reminder_time = datetime.now()
        
        # 计算下次催办时间
        level_index = list(ReminderLevel).index(record.level)
        if level_index < len(rule.escalation_intervals):
            interval_hours = rule.escalation_intervals[level_index]
            record.next_reminder_time = datetime.now() + timedelta(hours=interval_hours)
        
        # 发送催办通知
        self._send_reminder_notification(rule, record, record.data or {})
        
        try:
            self.db.commit()
            logger.info(f"发送 {record.level.value} 级催办: {record.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"发送催办失败: {str(e)}")
    
    def _escalate_reminder(self, record: ReminderRecord, rule: ReminderRule):
        """升级催办"""
        record.status = ReminderStatus.ESCALATED
        record.escalation_time = datetime.now()
        
        # 发送升级通知
        escalation_recipients = rule.escalation_recipients or []
        if escalation_recipients:
            # 这里应该调用通知服务发送升级通知
            pass
        
        try:
            self.db.commit()
            logger.warning(f"催办已升级: {record.id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"升级催办失败: {str(e)}")
    
    def mark_reminder_responded(self, record_id: int, response_content: str = None, 
                               response_time: Optional[datetime] = None) -> bool:
        """标记催办已响应"""
        record = self.db.query(ReminderRecord).filter(
            ReminderRecord.id == record_id
        ).first()
        
        if not record:
            return False
        
        record.status = ReminderStatus.RESPONDED
        record.response_time = response_time or datetime.now()
        
        # 创建响应记录
        if response_content:
            response = ReminderResponse(
                reminder_id=record_id,
                response_content=response_content,
                response_time=record.response_time
            )
            self.db.add(response)
        
        try:
            self.db.commit()
            logger.info(f"催办已响应: {record_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"标记催办响应失败: {str(e)}")
            return False
    
    def get_reminder_statistics(self) -> Dict[str, Any]:
        """获取催办统计"""
        # 基础统计
        total_reminders = self.db.query(ReminderRecord).count()
        responded_reminders = self.db.query(ReminderRecord).filter(
            ReminderRecord.status == ReminderStatus.RESPONDED
        ).count()
        escalated_reminders = self.db.query(ReminderRecord).filter(
            ReminderRecord.status == ReminderStatus.ESCALATED
        ).count()
        pending_reminders = self.db.query(ReminderRecord).filter(
            ReminderRecord.status == ReminderStatus.PENDING
        ).count()
        
        # 计算平均响应时间
        responded_records = self.db.query(ReminderRecord).filter(
            ReminderRecord.status == ReminderStatus.RESPONDED,
            ReminderRecord.response_time.isnot(None)
        ).all()
        
        avg_response_time = 0
        if responded_records:
            total_response_time = sum([
                (r.response_time - r.created_at).total_seconds() / 3600 
                for r in responded_records
            ])
            avg_response_time = total_response_time / len(responded_records)
        
        # 按类型统计
        type_stats = {}
        for reminder_type in ReminderType:
            type_total = self.db.query(ReminderRecord).filter(
                ReminderRecord.reminder_type == reminder_type
            ).count()
            type_responded = self.db.query(ReminderRecord).filter(
                ReminderRecord.reminder_type == reminder_type,
                ReminderRecord.status == ReminderStatus.RESPONDED
            ).count()
            type_escalated = self.db.query(ReminderRecord).filter(
                ReminderRecord.reminder_type == reminder_type,
                ReminderRecord.status == ReminderStatus.ESCALATED
            ).count()
            
            type_stats[reminder_type.value] = {
                "total": type_total,
                "responded": type_responded,
                "escalated": type_escalated
            }
        
        return {
            "total_reminders": total_reminders,
            "responded_reminders": responded_reminders,
            "escalated_reminders": escalated_reminders,
            "pending_reminders": pending_reminders,
            "response_rate": round((responded_reminders / total_reminders * 100) if total_reminders > 0 else 0, 2),
            "escalation_rate": round((escalated_reminders / total_reminders * 100) if total_reminders > 0 else 0, 2),
            "avg_response_time_hours": round(avg_response_time, 2),
            "type_statistics": type_stats
        }
    
    def _check_trigger_conditions(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """检查触发条件"""
        for key, expected_value in conditions.items():
            if key not in data:
                return False
            
            actual_value = data[key]
            
            # 支持不同类型的比较
            if isinstance(expected_value, dict):
                # 支持范围比较
                if "min" in expected_value and actual_value < expected_value["min"]:
                    return False
                if "max" in expected_value and actual_value > expected_value["max"]:
                    return False
            else:
                # 直接比较
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _get_reminder_recipients(self, rule: ReminderRule, data: Dict[str, Any]) -> List[int]:
        """获取催办接收者"""
        recipients = []
        
        # 从数据中获取直接指定的接收者
        if "recipient_ids" in data:
            recipients.extend(data["recipient_ids"])
        
        # 根据业务逻辑获取接收者
        if "responsible_user_id" in data:
            recipients.append(data["responsible_user_id"])
        
        if "team_members" in data:
            recipients.extend(data["team_members"])
        
        return list(set(recipients))  # 去重
    
    def _get_escalation_recipients(self, rule: ReminderRule) -> List[int]:
        """获取升级接收者"""
        escalate_roles = rule.escalation_rules.get("escalate_to_roles", [])
        
        recipients = []
        for role in escalate_roles:
            # 根据角色查找用户
            role_users = self.db.query(User).filter(User.role == role).all()
            recipients.extend([user.id for user in role_users])
        
        return list(set(recipients))
    
    def _find_matching_rule(self, reminder_type: ReminderType, data: Dict[str, Any]) -> Optional[ReminderRule]:
        """查找匹配的催办规则"""
        rules = self.db.query(ReminderRule).filter(
            ReminderRule.reminder_type == reminder_type,
            ReminderRule.is_active == True
        ).all()
        
        for rule in rules:
            # 检查触发条件
            if self._check_trigger_conditions(rule.trigger_conditions, data):
                return rule
        return None
    
    def _generate_reminder_content(self, rule: ReminderRule, data: Dict[str, Any]) -> tuple[str, str]:
        """生成催办内容"""
        # 简单的模板替换
        title = rule.title_template
        content = rule.content_template
        
        # 替换模板变量
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))
            
        return title, content
    
    def _get_notification_priority(self, level: ReminderLevel) -> str:
        """获取通知优先级"""
        priority_map = {
            ReminderLevel.LOW: "low",
            ReminderLevel.NORMAL: "normal",
            ReminderLevel.HIGH: "high",
            ReminderLevel.URGENT: "urgent"
        }
        
        return priority_map.get(level, "normal")