"""催办管理API端点

提供催办系统的REST API接口：
- 创建催办
- 查询催办记录
- 响应催办
- 催办统计
- 催办规则管理
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from ...database import get_db
from ...services.reminder_service import ReminderService, ReminderType, ReminderLevel
from ...schemas.base import BaseResponse, PaginatedResponse
from ...core.auth import get_current_user
from ...models.user import User

router = APIRouter(prefix="/reminders", tags=["催办管理"])


# 催办记录相关的Pydantic模型
from pydantic import BaseModel, Field

class ReminderCreateRequest(BaseModel):
    """创建催办请求"""
    reminder_type: str = Field(..., description="催办类型")
    related_type: str = Field(..., description="关联对象类型")
    related_id: int = Field(..., description="关联对象ID")
    data: Dict[str, Any] = Field(..., description="催办数据")

class ReminderResponse(BaseModel):
    """催办记录响应"""
    record_id: str
    reminder_type: str
    related_type: str
    related_id: int
    reminder_level: int
    recipients: List[int]
    sent_at: datetime
    response_deadline: datetime
    is_responded: bool
    response_time: Optional[datetime]
    escalated: bool

class ReminderStatisticsResponse(BaseModel):
    """催办统计响应"""
    total_reminders: int
    responded_reminders: int
    escalated_reminders: int
    pending_reminders: int
    response_rate: float
    escalation_rate: float
    avg_response_time_hours: float
    type_statistics: Dict[str, Dict[str, int]]

class ReminderRuleResponse(BaseModel):
    """催办规则响应"""
    rule_id: str
    name: str
    reminder_type: str
    trigger_conditions: Dict[str, Any]
    reminder_intervals: List[int]
    escalation_rules: Dict[str, Any]
    notification_types: List[str]
    is_active: bool

class ReminderResponseRequest(BaseModel):
    """催办响应请求"""
    record_id: str = Field(..., description="催办记录ID")
    response_time: Optional[datetime] = Field(None, description="响应时间")


@router.post("/create", response_model=BaseResponse[List[ReminderResponse]])
async def create_reminder(
    request: ReminderCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建催办"""
    try:
        reminder_service = ReminderService(db)
        
        # 验证催办类型
        try:
            reminder_type = ReminderType(request.reminder_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的催办类型: {request.reminder_type}")
        
        # 创建催办记录
        records = reminder_service.create_reminder(
            reminder_type=reminder_type,
            related_type=request.related_type,
            related_id=request.related_id,
            data=request.data
        )
        
        # 转换为响应格式
        response_records = [
            ReminderResponse(
                record_id=record.record_id,
                reminder_type=record.reminder_type.value,
                related_type=record.related_type,
                related_id=record.related_id,
                reminder_level=record.reminder_level.value,
                recipients=record.recipients,
                sent_at=record.sent_at,
                response_deadline=record.response_deadline,
                is_responded=record.is_responded,
                response_time=record.response_time,
                escalated=record.escalated
            )
            for record in records
        ]
        
        logger.info(f"用户 {current_user.username} 创建了 {len(records)} 个催办记录")
        
        return BaseResponse(
            success=True,
            data=response_records,
            message=f"成功创建 {len(records)} 个催办记录"
        )
        
    except Exception as e:
        logger.error(f"创建催办失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建催办失败: {str(e)}")


@router.get("/list", response_model=PaginatedResponse[ReminderResponse])
async def get_reminders(
    reminder_type: Optional[str] = Query(None, description="催办类型筛选"),
    is_responded: Optional[bool] = Query(None, description="是否已响应筛选"),
    escalated: Optional[bool] = Query(None, description="是否已升级筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取催办记录列表"""
    try:
        reminder_service = ReminderService(db)
        
        # 获取所有催办记录
        all_records = reminder_service.reminder_records
        
        # 应用筛选条件
        filtered_records = all_records
        
        if reminder_type:
            try:
                filter_type = ReminderType(reminder_type)
                filtered_records = [r for r in filtered_records if r.reminder_type == filter_type]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的催办类型: {reminder_type}")
        
        if is_responded is not None:
            filtered_records = [r for r in filtered_records if r.is_responded == is_responded]
        
        if escalated is not None:
            filtered_records = [r for r in filtered_records if r.escalated == escalated]
        
        # 分页
        total = len(filtered_records)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_records = filtered_records[start_idx:end_idx]
        
        # 转换为响应格式
        response_records = [
            ReminderResponse(
                record_id=record.record_id,
                reminder_type=record.reminder_type.value,
                related_type=record.related_type,
                related_id=record.related_id,
                reminder_level=record.reminder_level.value,
                recipients=record.recipients,
                sent_at=record.sent_at,
                response_deadline=record.response_deadline,
                is_responded=record.is_responded,
                response_time=record.response_time,
                escalated=record.escalated
            )
            for record in page_records
        ]
        
        return PaginatedResponse(
            success=True,
            data=response_records,
            total=total,
            page=page,
            page_size=page_size,
            message="获取催办记录成功"
        )
        
    except Exception as e:
        logger.error(f"获取催办记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取催办记录失败: {str(e)}")


@router.post("/respond", response_model=BaseResponse[bool])
async def respond_to_reminder(
    request: ReminderResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """响应催办"""
    try:
        reminder_service = ReminderService(db)
        
        # 标记催办已响应
        success = reminder_service.mark_reminder_responded(
            record_id=request.record_id,
            response_time=request.response_time
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="催办记录不存在")
        
        logger.info(f"用户 {current_user.username} 响应了催办: {request.record_id}")
        
        return BaseResponse(
            success=True,
            data=True,
            message="催办响应成功"
        )
        
    except Exception as e:
        logger.error(f"响应催办失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"响应催办失败: {str(e)}")


@router.get("/statistics", response_model=BaseResponse[ReminderStatisticsResponse])
async def get_reminder_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取催办统计"""
    try:
        reminder_service = ReminderService(db)
        
        # 获取统计数据
        stats = reminder_service.get_reminder_statistics()
        
        response = ReminderStatisticsResponse(**stats)
        
        return BaseResponse(
            success=True,
            data=response,
            message="获取催办统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取催办统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取催办统计失败: {str(e)}")


@router.get("/rules", response_model=BaseResponse[List[ReminderRuleResponse]])
async def get_reminder_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取催办规则列表"""
    try:
        reminder_service = ReminderService(db)
        
        # 转换规则为响应格式
        response_rules = [
            ReminderRuleResponse(
                rule_id=rule.rule_id,
                name=rule.name,
                reminder_type=rule.reminder_type.value,
                trigger_conditions=rule.trigger_conditions,
                reminder_intervals=rule.reminder_intervals,
                escalation_rules=rule.escalation_rules,
                notification_types=[nt.value for nt in rule.notification_types],
                is_active=rule.is_active
            )
            for rule in reminder_service.reminder_rules
        ]
        
        return BaseResponse(
            success=True,
            data=response_rules,
            message="获取催办规则成功"
        )
        
    except Exception as e:
        logger.error(f"获取催办规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取催办规则失败: {str(e)}")


@router.post("/process-pending", response_model=BaseResponse[int])
async def process_pending_reminders(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """处理待催办记录（手动触发）"""
    try:
        reminder_service = ReminderService(db)
        
        # 处理待催办记录
        processed_count = reminder_service.process_pending_reminders()
        
        logger.info(f"用户 {current_user.username} 手动触发催办处理，处理了 {processed_count} 个记录")
        
        return BaseResponse(
            success=True,
            data=processed_count,
            message=f"成功处理 {processed_count} 个待催办记录"
        )
        
    except Exception as e:
        logger.error(f"处理待催办记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理待催办记录失败: {str(e)}")


@router.get("/types", response_model=BaseResponse[List[Dict[str, str]]])
async def get_reminder_types():
    """获取催办类型列表"""
    try:
        types = [
            {"value": rt.value, "label": rt.value.replace("_", " ").title()}
            for rt in ReminderType
        ]
        
        return BaseResponse(
            success=True,
            data=types,
            message="获取催办类型成功"
        )
        
    except Exception as e:
        logger.error(f"获取催办类型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取催办类型失败: {str(e)}")


@router.get("/record/{record_id}", response_model=BaseResponse[ReminderResponse])
async def get_reminder_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定催办记录详情"""
    try:
        reminder_service = ReminderService(db)
        
        # 查找催办记录
        record = next(
            (r for r in reminder_service.reminder_records if r.record_id == record_id),
            None
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="催办记录不存在")
        
        response_record = ReminderResponse(
            record_id=record.record_id,
            reminder_type=record.reminder_type.value,
            related_type=record.related_type,
            related_id=record.related_id,
            reminder_level=record.reminder_level.value,
            recipients=record.recipients,
            sent_at=record.sent_at,
            response_deadline=record.response_deadline,
            is_responded=record.is_responded,
            response_time=record.response_time,
            escalated=record.escalated
        )
        
        return BaseResponse(
            success=True,
            data=response_record,
            message="获取催办记录详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取催办记录详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取催办记录详情失败: {str(e)}")


# 业务场景快捷催办接口

@router.post("/order-due", response_model=BaseResponse[List[ReminderResponse]])
async def create_order_due_reminder(
    order_id: int,
    days_before_due: int = 3,
    responsible_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单交期催办"""
    try:
        reminder_service = ReminderService(db)
        
        data = {
            "order_id": order_id,
            "days_before_due": days_before_due
        }
        
        if responsible_user_id:
            data["responsible_user_id"] = responsible_user_id
        
        records = reminder_service.create_reminder(
            reminder_type=ReminderType.ORDER_DUE,
            related_type="order",
            related_id=order_id,
            data=data
        )
        
        response_records = [
            ReminderResponse(
                record_id=record.record_id,
                reminder_type=record.reminder_type.value,
                related_type=record.related_type,
                related_id=record.related_id,
                reminder_level=record.reminder_level.value,
                recipients=record.recipients,
                sent_at=record.sent_at,
                response_deadline=record.response_deadline,
                is_responded=record.is_responded,
                response_time=record.response_time,
                escalated=record.escalated
            )
            for record in records
        ]
        
        return BaseResponse(
            success=True,
            data=response_records,
            message="订单交期催办创建成功"
        )
        
    except Exception as e:
        logger.error(f"创建订单交期催办失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建订单交期催办失败: {str(e)}")


@router.post("/task-overdue", response_model=BaseResponse[List[ReminderResponse]])
async def create_task_overdue_reminder(
    task_id: int,
    task_name: str,
    overdue_hours: int = 2,
    responsible_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务逾期催办"""
    try:
        reminder_service = ReminderService(db)
        
        data = {
            "task_name": task_name,
            "overdue_hours": overdue_hours
        }
        
        if responsible_user_id:
            data["responsible_user_id"] = responsible_user_id
        
        records = reminder_service.create_reminder(
            reminder_type=ReminderType.TASK_OVERDUE,
            related_type="task",
            related_id=task_id,
            data=data
        )
        
        response_records = [
            ReminderResponse(
                record_id=record.record_id,
                reminder_type=record.reminder_type.value,
                related_type=record.related_type,
                related_id=record.related_id,
                reminder_level=record.reminder_level.value,
                recipients=record.recipients,
                sent_at=record.sent_at,
                response_deadline=record.response_deadline,
                is_responded=record.is_responded,
                response_time=record.response_time,
                escalated=record.escalated
            )
            for record in records
        ]
        
        return BaseResponse(
            success=True,
            data=response_records,
            message="任务逾期催办创建成功"
        )
        
    except Exception as e:
        logger.error(f"创建任务逾期催办失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务逾期催办失败: {str(e)}")