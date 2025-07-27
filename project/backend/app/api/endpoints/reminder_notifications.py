"""催办通知API接口

提供催办通知系统的完整API接口：
- 创建催办并发送通知
- 响应催办
- 升级催办
- 查询催办状态
- 管理通知渠道
- 调度器管理
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...db.database import get_db
from ...models.user import User
from ...models.reminder import ReminderType, ReminderLevel, ReminderStatus
from ...services.reminder_notification_service import ReminderNotificationService
from ...services.multi_channel_notification_service import (
    MultiChannelNotificationService, 
    ChannelType, 
    NotificationLevel
)
from ...services.reminder_scheduler import reminder_scheduler
from ...core.auth import get_current_user, require_permissions
from ...core.permissions import Permission

router = APIRouter(prefix="/reminder-notifications", tags=["催办通知"])


# Pydantic 模型
class CreateReminderRequest(BaseModel):
    """创建催办请求"""
    reminder_type: ReminderType = Field(..., description="催办类型")
    target_id: int = Field(..., description="目标对象ID")
    title: str = Field(..., min_length=1, max_length=200, description="催办标题")
    content: str = Field(..., min_length=1, max_length=2000, description="催办内容")
    level: ReminderLevel = Field(default=ReminderLevel.NORMAL, description="催办级别")
    assignee_id: Optional[int] = Field(None, description="指定处理人ID")
    due_date: Optional[datetime] = Field(None, description="截止时间")
    notify_channels: Optional[List[ChannelType]] = Field(None, description="指定通知渠道")


class RespondReminderRequest(BaseModel):
    """响应催办请求"""
    response_content: str = Field(..., min_length=1, max_length=2000, description="响应内容")


class EscalateReminderRequest(BaseModel):
    """升级催办请求"""
    new_level: ReminderLevel = Field(..., description="新的催办级别")
    escalation_reason: str = Field("", max_length=500, description="升级原因")


class SendNotificationRequest(BaseModel):
    """发送通知请求"""
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    content: str = Field(..., min_length=1, max_length=2000, description="通知内容")
    level: NotificationLevel = Field(default=NotificationLevel.INFO, description="通知级别")
    recipients: List[str] = Field(..., description="接收者列表")
    channels: Optional[List[ChannelType]] = Field(None, description="指定通知渠道")
    scheduled_at: Optional[datetime] = Field(None, description="计划发送时间")


class ReminderResponse(BaseModel):
    """催办响应"""
    id: int
    reminder_type: str
    target_id: int
    title: str
    content: str
    level: str
    status: str
    assignee_id: Optional[int]
    created_by: Optional[int]
    due_date: Optional[datetime]
    created_at: datetime
    responded_at: Optional[datetime]
    response_content: Optional[str]
    responder_id: Optional[int]


@router.post("/reminders", summary="创建催办并发送通知")
async def create_reminder_with_notification(
    request: CreateReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """创建催办并发送通知"""
    try:
        service = ReminderNotificationService(db)
        
        result = await service.create_reminder_with_notification(
            reminder_type=request.reminder_type,
            target_id=request.target_id,
            title=request.title,
            content=request.content,
            level=request.level,
            assignee_id=request.assignee_id,
            due_date=request.due_date,
            notify_channels=request.notify_channels
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "催办创建成功并已发送通知"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建催办失败: {str(e)}")


@router.post("/reminders/{reminder_id}/respond", summary="响应催办")
async def respond_reminder(
    reminder_id: int,
    request: RespondReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """响应催办"""
    try:
        service = ReminderNotificationService(db)
        
        result = await service.respond_reminder_with_notification(
            reminder_id=reminder_id,
            response_content=request.response_content,
            responder_id=current_user.id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "催办响应成功并已发送通知"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"响应催办失败: {str(e)}")


@router.post("/reminders/{reminder_id}/escalate", summary="升级催办")
async def escalate_reminder(
    reminder_id: int,
    request: EscalateReminderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions([Permission.REMINDER_MANAGE]))
) -> Dict[str, Any]:
    """升级催办（需要管理权限）"""
    try:
        service = ReminderNotificationService(db)
        
        result = await service.escalate_reminder_with_notification(
            reminder_id=reminder_id,
            new_level=request.new_level,
            escalation_reason=request.escalation_reason
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "催办升级成功并已发送通知"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"升级催办失败: {str(e)}")


@router.get("/reminders", summary="查询催办列表")
async def get_reminders(
    status: Optional[ReminderStatus] = Query(None, description="催办状态"),
    reminder_type: Optional[ReminderType] = Query(None, description="催办类型"),
    level: Optional[ReminderLevel] = Query(None, description="催办级别"),
    assignee_id: Optional[int] = Query(None, description="处理人ID"),
    created_by: Optional[int] = Query(None, description="创建人ID"),
    overdue_only: bool = Query(False, description="仅显示逾期催办"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """查询催办列表"""
    try:
        from ...models.reminder import Reminder
        
        query = db.query(Reminder)
        
        # 应用过滤条件
        if status:
            query = query.filter(Reminder.status == status)
        if reminder_type:
            query = query.filter(Reminder.reminder_type == reminder_type)
        if level:
            query = query.filter(Reminder.level == level)
        if assignee_id:
            query = query.filter(Reminder.assignee_id == assignee_id)
        if created_by:
            query = query.filter(Reminder.created_by == created_by)
        if overdue_only:
            query = query.filter(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.due_date.isnot(None),
                Reminder.due_date < datetime.now()
            )
        
        # 分页
        total = query.count()
        reminders = query.offset((page - 1) * size).limit(size).all()
        
        # 转换为响应格式
        reminder_list = []
        for reminder in reminders:
            reminder_list.append({
                "id": reminder.id,
                "reminder_type": reminder.reminder_type.value,
                "target_id": reminder.target_id,
                "title": reminder.title,
                "content": reminder.content,
                "level": reminder.level.value,
                "status": reminder.status.value,
                "assignee_id": reminder.assignee_id,
                "created_by": reminder.created_by,
                "due_date": reminder.due_date,
                "created_at": reminder.created_at,
                "responded_at": reminder.responded_at,
                "response_content": reminder.response_content,
                "responder_id": reminder.responder_id
            })
        
        return {
            "success": True,
            "data": {
                "items": reminder_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询催办列表失败: {str(e)}")


@router.get("/reminders/{reminder_id}", summary="获取催办详情")
async def get_reminder_detail(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取催办详情"""
    try:
        from ...models.reminder import Reminder
        
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if not reminder:
            raise HTTPException(status_code=404, detail="催办不存在")
        
        return {
            "success": True,
            "data": {
                "id": reminder.id,
                "reminder_type": reminder.reminder_type.value,
                "target_id": reminder.target_id,
                "title": reminder.title,
                "content": reminder.content,
                "level": reminder.level.value,
                "status": reminder.status.value,
                "assignee_id": reminder.assignee_id,
                "created_by": reminder.created_by,
                "due_date": reminder.due_date,
                "created_at": reminder.created_at,
                "responded_at": reminder.responded_at,
                "response_content": reminder.response_content,
                "responder_id": reminder.responder_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取催办详情失败: {str(e)}")


@router.post("/notifications/send", summary="发送通知")
async def send_notification(
    request: SendNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions([Permission.NOTIFICATION_SEND]))
) -> Dict[str, Any]:
    """发送通知（需要发送权限）"""
    try:
        service = MultiChannelNotificationService(db)
        
        result = await service.send_notification(
            title=request.title,
            content=request.content,
            level=request.level,
            recipients=request.recipients,
            channels=request.channels,
            scheduled_at=request.scheduled_at
        )
        
        return {
            "success": True,
            "data": result,
            "message": "通知发送成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送通知失败: {str(e)}")


@router.get("/channels/status", summary="获取通知渠道状态")
async def get_channel_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取通知渠道状态"""
    try:
        service = MultiChannelNotificationService(db)
        status = service.get_channel_status()
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取渠道状态失败: {str(e)}")


@router.get("/statistics", summary="获取催办通知统计")
async def get_statistics(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取催办通知统计"""
    try:
        from ...models.reminder import Reminder
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 统计催办数据
        total_reminders = db.query(Reminder).filter(
            Reminder.created_at >= start_date
        ).count()
        
        responded_reminders = db.query(Reminder).filter(
            Reminder.created_at >= start_date,
            Reminder.status == ReminderStatus.RESPONDED
        ).count()
        
        pending_reminders = db.query(Reminder).filter(
            Reminder.status == ReminderStatus.PENDING
        ).count()
        
        overdue_reminders = db.query(Reminder).filter(
            Reminder.status == ReminderStatus.PENDING,
            Reminder.due_date.isnot(None),
            Reminder.due_date < datetime.now()
        ).count()
        
        # 按级别统计
        level_stats = {}
        for level in ReminderLevel:
            count = db.query(Reminder).filter(
                Reminder.created_at >= start_date,
                Reminder.level == level
            ).count()
            level_stats[level.value] = count
        
        # 按类型统计
        type_stats = {}
        for reminder_type in ReminderType:
            count = db.query(Reminder).filter(
                Reminder.created_at >= start_date,
                Reminder.reminder_type == reminder_type
            ).count()
            type_stats[reminder_type.value] = count
        
        # 获取通知服务统计
        notification_service = MultiChannelNotificationService(db)
        notification_stats = notification_service.get_statistics()
        
        return {
            "success": True,
            "data": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "reminder_stats": {
                    "total": total_reminders,
                    "responded": responded_reminders,
                    "pending": pending_reminders,
                    "overdue": overdue_reminders,
                    "response_rate": responded_reminders / total_reminders * 100 if total_reminders > 0 else 0
                },
                "level_stats": level_stats,
                "type_stats": type_stats,
                "notification_stats": notification_stats
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.post("/scheduler/check-overdue", summary="立即检查逾期催办")
async def trigger_overdue_check(
    current_user: User = Depends(require_permissions([Permission.REMINDER_MANAGE]))
) -> Dict[str, Any]:
    """立即触发逾期催办检查（需要管理权限）"""
    try:
        result = await reminder_scheduler.trigger_immediate_check()
        return {
            "success": result["success"],
            "message": result.get("message", result.get("error", "Unknown result"))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发逾期检查失败: {str(e)}")


@router.post("/scheduler/send-summary", summary="立即发送催办汇总")
async def trigger_summary_send(
    current_user: User = Depends(require_permissions([Permission.REMINDER_MANAGE]))
) -> Dict[str, Any]:
    """立即触发催办汇总发送（需要管理权限）"""
    try:
        result = await reminder_scheduler.trigger_immediate_summary()
        return {
            "success": result["success"],
            "message": result.get("message", result.get("error", "Unknown result"))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发汇总发送失败: {str(e)}")


@router.get("/scheduler/status", summary="获取调度器状态")
async def get_scheduler_status(
    current_user: User = Depends(require_permissions([Permission.SYSTEM_MONITOR]))
) -> Dict[str, Any]:
    """获取调度器状态（需要监控权限）"""
    try:
        from ...services.reminder_scheduler import get_scheduler_status
        status = get_scheduler_status()
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")


@router.post("/daily-summary", summary="发送每日催办汇总")
async def send_daily_summary(
    target_date: Optional[datetime] = Query(None, description="目标日期，默认为今天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions([Permission.REMINDER_MANAGE]))
) -> Dict[str, Any]:
    """发送每日催办汇总（需要管理权限）"""
    try:
        service = ReminderNotificationService(db)
        result = await service.send_daily_reminder_summary(target_date)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "data": result,
            "message": "每日催办汇总发送成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送每日汇总失败: {str(e)}")