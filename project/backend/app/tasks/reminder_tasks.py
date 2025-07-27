"""催办定时任务

实现催办系统的定时任务：
- 自动检查催办条件
- 处理待催办记录
- 升级逾期催办
- 清理过期记录
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from ..database import SessionLocal
from ..services.reminder_service import ReminderService, ReminderType
from ..models.order import Order
from ..models.task import Task
from ..models.equipment import Equipment
from ..models.quality_record import QualityRecord
from ..core.celery_app import celery_app


@celery_app.task(name="process_pending_reminders")
def process_pending_reminders_task():
    """处理待催办记录的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        processed_count = reminder_service.process_pending_reminders()
        
        logger.info(f"定时任务处理了 {processed_count} 个待催办记录")
        return {"processed_count": processed_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"处理待催办记录任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="check_order_due_reminders")
def check_order_due_reminders_task():
    """检查订单交期催办的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        created_count = 0
        
        # 查询即将到期的订单（3天内）
        three_days_later = datetime.now() + timedelta(days=3)
        upcoming_orders = db.query(Order).filter(
            Order.delivery_date <= three_days_later,
            Order.delivery_date > datetime.now(),
            Order.status.in_(["in_progress", "pending"])
        ).all()
        
        for order in upcoming_orders:
            days_before_due = (order.delivery_date - datetime.now()).days
            
            # 检查是否已经创建过催办
            existing_reminders = [
                r for r in reminder_service.reminder_records
                if (r.reminder_type == ReminderType.ORDER_DUE and 
                    r.related_type == "order" and 
                    r.related_id == order.id)
            ]
            
            if not existing_reminders:
                data = {
                    "order_id": order.id,
                    "days_before_due": days_before_due,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "delivery_date": order.delivery_date.isoformat(),
                    "responsible_user_id": order.responsible_user_id
                }
                
                records = reminder_service.create_reminder(
                    reminder_type=ReminderType.ORDER_DUE,
                    related_type="order",
                    related_id=order.id,
                    data=data
                )
                
                created_count += len(records)
        
        # 检查1天内到期的订单（紧急催办）
        one_day_later = datetime.now() + timedelta(days=1)
        urgent_orders = db.query(Order).filter(
            Order.delivery_date <= one_day_later,
            Order.delivery_date > datetime.now(),
            Order.status.in_(["in_progress", "pending"])
        ).all()
        
        for order in urgent_orders:
            # 检查是否已经创建过1天催办
            existing_urgent_reminders = [
                r for r in reminder_service.reminder_records
                if (r.reminder_type == ReminderType.ORDER_DUE and 
                    r.related_type == "order" and 
                    r.related_id == order.id and
                    "days_before_due" in str(r.record_id) and "1" in str(r.record_id))
            ]
            
            if not existing_urgent_reminders:
                data = {
                    "order_id": order.id,
                    "days_before_due": 1,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "delivery_date": order.delivery_date.isoformat(),
                    "responsible_user_id": order.responsible_user_id,
                    "urgent": True
                }
                
                records = reminder_service.create_reminder(
                    reminder_type=ReminderType.ORDER_DUE,
                    related_type="order",
                    related_id=order.id,
                    data=data
                )
                
                created_count += len(records)
        
        logger.info(f"订单交期检查任务创建了 {created_count} 个催办记录")
        return {"created_count": created_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"检查订单交期催办任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="check_task_overdue_reminders")
def check_task_overdue_reminders_task():
    """检查任务逾期催办的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        created_count = 0
        
        # 查询逾期的任务
        overdue_tasks = db.query(Task).filter(
            Task.due_date < datetime.now(),
            Task.status.in_(["pending", "in_progress"])
        ).all()
        
        for task in overdue_tasks:
            overdue_hours = (datetime.now() - task.due_date).total_seconds() / 3600
            
            # 只处理逾期超过2小时的任务
            if overdue_hours >= 2:
                # 检查是否已经创建过催办
                existing_reminders = [
                    r for r in reminder_service.reminder_records
                    if (r.reminder_type == ReminderType.TASK_OVERDUE and 
                        r.related_type == "task" and 
                        r.related_id == task.id)
                ]
                
                if not existing_reminders:
                    data = {
                        "task_name": task.name,
                        "overdue_hours": int(overdue_hours),
                        "due_date": task.due_date.isoformat(),
                        "responsible_user_id": task.assigned_to,
                        "project_id": task.project_id
                    }
                    
                    records = reminder_service.create_reminder(
                        reminder_type=ReminderType.TASK_OVERDUE,
                        related_type="task",
                        related_id=task.id,
                        data=data
                    )
                    
                    created_count += len(records)
        
        logger.info(f"任务逾期检查任务创建了 {created_count} 个催办记录")
        return {"created_count": created_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"检查任务逾期催办任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="check_quality_issue_reminders")
def check_quality_issue_reminders_task():
    """检查质量问题催办的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        created_count = 0
        
        # 查询高严重性的质量问题
        high_severity_issues = db.query(QualityRecord).filter(
            QualityRecord.severity == "high",
            QualityRecord.status.in_(["open", "investigating"])
        ).all()
        
        for issue in high_severity_issues:
            # 检查问题创建时间，超过1小时未处理的进行催办
            hours_since_created = (datetime.now() - issue.created_at).total_seconds() / 3600
            
            if hours_since_created >= 1:
                # 检查是否已经创建过催办
                existing_reminders = [
                    r for r in reminder_service.reminder_records
                    if (r.reminder_type == ReminderType.QUALITY_ISSUE and 
                        r.related_type == "quality_record" and 
                        r.related_id == issue.id)
                ]
                
                if not existing_reminders:
                    data = {
                        "severity": "high",
                        "issue_description": issue.description,
                        "created_at": issue.created_at.isoformat(),
                        "responsible_user_id": issue.inspector_id,
                        "order_id": issue.order_id
                    }
                    
                    records = reminder_service.create_reminder(
                        reminder_type=ReminderType.QUALITY_ISSUE,
                        related_type="quality_record",
                        related_id=issue.id,
                        data=data
                    )
                    
                    created_count += len(records)
        
        logger.info(f"质量问题检查任务创建了 {created_count} 个催办记录")
        return {"created_count": created_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"检查质量问题催办任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="check_equipment_maintenance_reminders")
def check_equipment_maintenance_reminders_task():
    """检查设备维护催办的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        created_count = 0
        
        # 查询维护逾期的设备
        overdue_equipment = db.query(Equipment).filter(
            Equipment.next_maintenance_date < datetime.now(),
            Equipment.status == "active"
        ).all()
        
        for equipment in overdue_equipment:
            days_overdue = (datetime.now() - equipment.next_maintenance_date).days
            
            # 只处理逾期超过1天的设备
            if days_overdue >= 1:
                # 检查是否已经创建过催办
                existing_reminders = [
                    r for r in reminder_service.reminder_records
                    if (r.reminder_type == ReminderType.EQUIPMENT_MAINTENANCE and 
                        r.related_type == "equipment" and 
                        r.related_id == equipment.id)
                ]
                
                if not existing_reminders:
                    data = {
                        "equipment_name": equipment.name,
                        "days_overdue": days_overdue,
                        "next_maintenance_date": equipment.next_maintenance_date.isoformat(),
                        "responsible_user_id": equipment.responsible_user_id,
                        "location": equipment.location
                    }
                    
                    records = reminder_service.create_reminder(
                        reminder_type=ReminderType.EQUIPMENT_MAINTENANCE,
                        related_type="equipment",
                        related_id=equipment.id,
                        data=data
                    )
                    
                    created_count += len(records)
        
        logger.info(f"设备维护检查任务创建了 {created_count} 个催办记录")
        return {"created_count": created_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"检查设备维护催办任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="cleanup_old_reminder_records")
def cleanup_old_reminder_records_task():
    """清理过期催办记录的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        
        # 清理30天前的已响应记录
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        old_records = [
            r for r in reminder_service.reminder_records
            if (r.is_responded and r.response_time and r.response_time < thirty_days_ago)
        ]
        
        # 从内存中移除旧记录
        for record in old_records:
            reminder_service.reminder_records.remove(record)
        
        cleaned_count = len(old_records)
        
        logger.info(f"清理了 {cleaned_count} 个过期催办记录")
        return {"cleaned_count": cleaned_count, "status": "success"}
        
    except Exception as e:
        logger.error(f"清理过期催办记录任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@celery_app.task(name="generate_reminder_daily_report")
def generate_reminder_daily_report_task():
    """生成催办日报的定时任务"""
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        
        # 获取今日统计
        today = datetime.now().date()
        today_records = [
            r for r in reminder_service.reminder_records
            if r.sent_at.date() == today
        ]
        
        # 统计数据
        stats = {
            "date": today.isoformat(),
            "total_reminders_today": len(today_records),
            "responded_today": len([r for r in today_records if r.is_responded]),
            "escalated_today": len([r for r in today_records if r.escalated]),
            "pending_reminders": len([
                r for r in reminder_service.reminder_records 
                if not r.is_responded and not r.escalated
            ]),
            "type_breakdown": {}
        }
        
        # 按类型统计
        for reminder_type in ReminderType:
            type_records = [r for r in today_records if r.reminder_type == reminder_type]
            stats["type_breakdown"][reminder_type.value] = len(type_records)
        
        # 这里可以发送日报邮件或保存到数据库
        logger.info(f"生成催办日报: {stats}")
        
        return {"stats": stats, "status": "success"}
        
    except Exception as e:
        logger.error(f"生成催办日报任务失败: {str(e)}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


# 定时任务调度配置
REMINDER_TASK_SCHEDULE = {
    # 每5分钟处理一次待催办记录
    "process-pending-reminders": {
        "task": "process_pending_reminders",
        "schedule": 300.0,  # 5分钟
    },
    
    # 每小时检查一次订单交期
    "check-order-due": {
        "task": "check_order_due_reminders",
        "schedule": 3600.0,  # 1小时
    },
    
    # 每30分钟检查一次任务逾期
    "check-task-overdue": {
        "task": "check_task_overdue_reminders",
        "schedule": 1800.0,  # 30分钟
    },
    
    # 每小时检查一次质量问题
    "check-quality-issues": {
        "task": "check_quality_issue_reminders",
        "schedule": 3600.0,  # 1小时
    },
    
    # 每天检查一次设备维护
    "check-equipment-maintenance": {
        "task": "check_equipment_maintenance_reminders",
        "schedule": 86400.0,  # 24小时
    },
    
    # 每天凌晨2点清理过期记录
    "cleanup-old-records": {
        "task": "cleanup_old_reminder_records",
        "schedule": 86400.0,  # 24小时
    },
    
    # 每天早上8点生成日报
    "daily-report": {
        "task": "generate_reminder_daily_report",
        "schedule": 86400.0,  # 24小时
    }
}


def setup_reminder_tasks():
    """设置催办定时任务"""
    logger.info("设置催办系统定时任务")
    
    # 这里可以添加任务调度的初始化逻辑
    # 例如使用 Celery Beat 或其他调度器
    
    return REMINDER_TASK_SCHEDULE