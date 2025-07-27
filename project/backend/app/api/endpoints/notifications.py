from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User
from ...models.notification import (
    Notification, NotificationTemplate, NotificationRule,
    NotificationType, NotificationStatus, NotificationPriority
)
from ...schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse,
    NotificationRuleCreate, NotificationRuleUpdate, NotificationRuleResponse,
    BatchNotificationCreate, NotificationQuery, NotificationStats
)
from ...services.notification_service import NotificationService

router = APIRouter()

# 通知相关端点
@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知"""
    service = NotificationService(db)
    return service.create_notification(notification, current_user.id)

@router.post("/batch", response_model=List[NotificationResponse])
def create_batch_notifications(
    batch_data: BatchNotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量创建通知"""
    service = NotificationService(db)
    return service.create_batch_notifications(batch_data, current_user.id)

@router.get("/", response_model=dict)
def get_notifications(
    notification_type: Optional[NotificationType] = Query(None),
    status: Optional[NotificationStatus] = Query(None),
    priority: Optional[NotificationPriority] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知列表"""
    service = NotificationService(db)
    query = NotificationQuery(
        notification_type=notification_type,
        status=status,
        priority=priority,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size
    )
    return service.get_user_notifications(current_user.id, query)

@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知统计"""
    service = NotificationService(db)
    return service.get_notification_stats(current_user.id)

@router.get("/admin/stats", response_model=NotificationStats)
def get_admin_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取系统通知统计（管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    return service.get_notification_stats()

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定通知详情"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification

@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    for field, value in notification_update.dict(exclude_unset=True).items():
        setattr(notification, field, value)
    
    db.commit()
    db.refresh(notification)
    return notification

@router.post("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记通知为已读"""
    service = NotificationService(db)
    success = service.mark_as_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found or already read")
    
    return {"message": "Notification marked as read"}

@router.post("/{notification_id}/send")
def send_notification(
    notification_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送指定通知"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    background_tasks.add_task(service.send_notification, notification_id)
    
    return {"message": "Notification sending initiated"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}

# 通知模板相关端点
@router.post("/templates/", response_model=NotificationTemplateResponse)
def create_notification_template(
    template: NotificationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知模板"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # 检查模板名称是否已存在
    existing_template = db.query(NotificationTemplate).filter(
        NotificationTemplate.name == template.name
    ).first()
    
    if existing_template:
        raise HTTPException(status_code=400, detail="Template name already exists")
    
    db_template = NotificationTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template

@router.get("/templates/", response_model=List[NotificationTemplateResponse])
def get_notification_templates(
    notification_type: Optional[NotificationType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知模板列表"""
    query = db.query(NotificationTemplate)
    
    if notification_type:
        query = query.filter(NotificationTemplate.notification_type == notification_type)
    
    if is_active is not None:
        query = query.filter(NotificationTemplate.is_active == is_active)
    
    return query.all()

@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
def get_notification_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定通知模板"""
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template

@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
def update_notification_template(
    template_id: int,
    template_update: NotificationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知模板"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    return template

@router.delete("/templates/{template_id}")
def delete_notification_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知模板"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    
    return {"message": "Template deleted"}

# 通知规则相关端点
@router.post("/rules/", response_model=NotificationRuleResponse)
def create_notification_rule(
    rule: NotificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建通知规则"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_rule = NotificationRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return db_rule

@router.get("/rules/", response_model=List[NotificationRuleResponse])
def get_notification_rules(
    trigger_event: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取通知规则列表"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(NotificationRule)
    
    if trigger_event:
        query = query.filter(NotificationRule.trigger_event == trigger_event)
    
    if is_active is not None:
        query = query.filter(NotificationRule.is_active == is_active)
    
    return query.all()

@router.put("/rules/{rule_id}", response_model=NotificationRuleResponse)
def update_notification_rule(
    rule_id: int,
    rule_update: NotificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知规则"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rule = db.query(NotificationRule).filter(
        NotificationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    for field, value in rule_update.dict(exclude_unset=True).items():
        setattr(rule, field, value)
    
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)
    
    return rule

@router.delete("/rules/{rule_id}")
def delete_notification_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知规则"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rule = db.query(NotificationRule).filter(
        NotificationRule.id == rule_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    
    return {"message": "Rule deleted"}

# 系统管理端点
@router.post("/admin/retry-failed")
def retry_failed_notifications(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重试失败的通知"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    background_tasks.add_task(service.retry_failed_notifications)
    
    return {"message": "Failed notifications retry initiated"}

@router.post("/admin/process-scheduled")
def process_scheduled_notifications(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """处理计划发送的通知"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    background_tasks.add_task(service.process_scheduled_notifications)
    
    return {"message": "Scheduled notifications processing initiated"}

@router.post("/admin/trigger-event")
def trigger_notification_event(
    event: str,
    event_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动触发通知事件"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    background_tasks.add_task(service.trigger_notification_by_event, event, event_data)
    
    return {"message": f"Event '{event}' triggered"}