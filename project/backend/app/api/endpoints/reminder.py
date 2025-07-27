from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date

from app.db.database import get_db
from app.models.reminder import ReminderRecord, ReminderRule, ReminderResponse, ReminderType, ReminderLevel, ReminderStatus
from app.schemas.reminder import (
    ReminderRecordCreate, ReminderRecordUpdate, ReminderRecordResponse,
    ReminderRuleCreate, ReminderRuleUpdate, ReminderRuleResponse,
    ReminderResponseCreate, ReminderResponseUpdate, ReminderResponseResponse,
    ReminderQueryParams, ReminderStatistics
)
from app.services.reminder_service import ReminderService
from app.core.exceptions import ValidationException

router = APIRouter()


@router.post("/records", response_model=ReminderRecordResponse)
def create_reminder_record(
    reminder_data: ReminderRecordCreate,
    db: Session = Depends(get_db)
):
    """
    创建催办记录
    """
    try:
        reminder_service = ReminderService(db)
        reminder = reminder_service.create_reminder(
            reminder_type=reminder_data.reminder_type,
            target_id=reminder_data.target_id,
            target_type=reminder_data.target_type,
            title=reminder_data.title,
            content=reminder_data.content,
            recipient_user_ids=reminder_data.recipient_user_ids,
            sender_user_id=reminder_data.sender_user_id,
            due_date=reminder_data.due_date,
            priority_level=reminder_data.priority_level
        )
        return reminder
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records", response_model=List[ReminderRecordResponse])
def get_reminder_records(
    query: ReminderQueryParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    获取催办记录列表
    """
    # 构建查询条件
    filters = []
    
    if query.reminder_type:
        filters.append(ReminderRecord.reminder_type == query.reminder_type)
    
    if query.status:
        filters.append(ReminderRecord.status == query.status)
    
    if query.level:
        filters.append(ReminderRecord.level == query.level)
    
    if query.target_type:
        filters.append(ReminderRecord.target_type == query.target_type)
    
    if query.target_id:
        filters.append(ReminderRecord.target_id == query.target_id)
    
    if query.recipient_user_id:
        filters.append(ReminderRecord.recipient_user_ids.contains(str(query.recipient_user_id)))
    
    if query.sender_user_id:
        filters.append(ReminderRecord.sender_user_id == query.sender_user_id)
    
    if query.due_date_start:
        filters.append(ReminderRecord.due_date >= query.due_date_start)
    
    if query.due_date_end:
        filters.append(ReminderRecord.due_date <= query.due_date_end)
    
    if query.created_start:
        filters.append(ReminderRecord.created_at >= query.created_start)
    
    if query.created_end:
        filters.append(ReminderRecord.created_at <= query.created_end)
    
    # 构建基础查询
    base_query = db.query(ReminderRecord)
    if filters:
        base_query = base_query.filter(and_(*filters))
    
    # 排序
    if query.sort_field:
        sort_column = getattr(ReminderRecord, query.sort_field, None)
        if sort_column:
            if query.sort_order == "desc":
                base_query = base_query.order_by(sort_column.desc())
            else:
                base_query = base_query.order_by(sort_column.asc())
    else:
        base_query = base_query.order_by(ReminderRecord.created_at.desc())
    
    # 分页
    offset = (query.page - 1) * query.page_size
    records = base_query.offset(offset).limit(query.page_size).all()
    
    return records


@router.get("/records/{record_id}", response_model=ReminderRecordResponse)
def get_reminder_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个催办记录详情
    """
    record = db.query(ReminderRecord).filter(ReminderRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="催办记录不存在")
    return record


@router.put("/records/{record_id}", response_model=ReminderRecordResponse)
def update_reminder_record(
    record_id: int,
    update_data: ReminderRecordUpdate,
    db: Session = Depends(get_db)
):
    """
    更新催办记录
    """
    record = db.query(ReminderRecord).filter(ReminderRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="催办记录不存在")
    
    # 更新字段
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(record, field, value)
    
    record.updated_at = datetime.now()
    
    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/records/{record_id}/respond", response_model=ReminderResponseResponse)
def respond_to_reminder(
    record_id: int,
    response_data: ReminderResponseCreate,
    db: Session = Depends(get_db)
):
    """
    响应催办记录
    """
    record = db.query(ReminderRecord).filter(ReminderRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="催办记录不存在")
    
    try:
        reminder_service = ReminderService(db)
        response = reminder_service.mark_reminder_responded(
            reminder_id=record_id,
            response_content=response_data.response_content,
            response_user_id=response_data.response_user_id,
            action_taken=response_data.action_taken,
            completion_status=response_data.completion_status
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records/{record_id}/responses", response_model=List[ReminderResponseResponse])
def get_reminder_responses(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    获取催办记录的所有响应
    """
    record = db.query(ReminderRecord).filter(ReminderRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="催办记录不存在")
    
    responses = db.query(ReminderResponse).filter(
        ReminderResponse.reminder_id == record_id
    ).order_by(ReminderResponse.created_at.desc()).all()
    
    return responses


@router.get("/statistics", response_model=ReminderStatistics)
def get_reminder_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    reminder_type: Optional[ReminderType] = Query(None, description="催办类型"),
    db: Session = Depends(get_db)
):
    """
    获取催办统计信息
    """
    try:
        reminder_service = ReminderService(db)
        stats = reminder_service.get_reminder_statistics(
            start_date=start_date,
            end_date=end_date,
            reminder_type=reminder_type
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process-pending")
def process_pending_reminders(
    db: Session = Depends(get_db)
):
    """
    处理待催办记录（手动触发）
    """
    try:
        reminder_service = ReminderService(db)
        processed_count = reminder_service.process_pending_reminders()
        return {"message": f"已处理 {processed_count} 条待催办记录"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 催办规则管理
@router.post("/rules", response_model=ReminderRuleResponse)
def create_reminder_rule(
    rule_data: ReminderRuleCreate,
    db: Session = Depends(get_db)
):
    """
    创建催办规则
    """
    rule = ReminderRule(**rule_data.dict())
    rule.created_at = datetime.now()
    rule.updated_at = datetime.now()
    
    try:
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules", response_model=List[ReminderRuleResponse])
def get_reminder_rules(
    reminder_type: Optional[ReminderType] = Query(None, description="催办类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db)
):
    """
    获取催办规则列表
    """
    query = db.query(ReminderRule)
    
    if reminder_type:
        query = query.filter(ReminderRule.reminder_type == reminder_type)
    
    if is_active is not None:
        query = query.filter(ReminderRule.is_active == is_active)
    
    rules = query.order_by(ReminderRule.created_at.desc()).all()
    return rules


@router.get("/rules/{rule_id}", response_model=ReminderRuleResponse)
def get_reminder_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个催办规则详情
    """
    rule = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="催办规则不存在")
    return rule


@router.put("/rules/{rule_id}", response_model=ReminderRuleResponse)
def update_reminder_rule(
    rule_id: int,
    update_data: ReminderRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    更新催办规则
    """
    rule = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="催办规则不存在")
    
    # 更新字段
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(rule, field, value)
    
    rule.updated_at = datetime.now()
    
    try:
        db.commit()
        db.refresh(rule)
        return rule
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rules/{rule_id}")
def delete_reminder_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    删除催办规则
    """
    rule = db.query(ReminderRule).filter(ReminderRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="催办规则不存在")
    
    try:
        db.delete(rule)
        db.commit()
        return {"message": "催办规则删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))