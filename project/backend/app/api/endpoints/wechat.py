from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from app.services.wechat_service import WeChatService, MessageType, Priority, NotificationRule

router = APIRouter()
wechat_service = WeChatService()

# 请求模型
class SendMessageRequest(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    priority: Priority = Priority.NORMAL
    recipients: Optional[List[str]] = None

class NotificationRuleRequest(BaseModel):
    rule_type: str
    conditions: dict
    message_template: str
    recipients: List[str]
    enabled: bool = True
    schedule: Optional[str] = None

class WeChatConfigRequest(BaseModel):
    corp_id: str
    corp_secret: str
    agent_id: str
    webhook_url: Optional[str] = None

# 响应模型
class MessageResponse(BaseModel):
    message_id: str
    status: str
    sent_at: datetime
    recipients_count: int

class NotificationRuleResponse(BaseModel):
    rule_id: str
    rule_type: str
    enabled: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None

class MessageStatsResponse(BaseModel):
    total_sent: int
    success_count: int
    failed_count: int
    pending_count: int
    today_sent: int
    this_week_sent: int

@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks
):
    """
    发送微信消息
    """
    try:
        message = await wechat_service.create_message(
            content=request.content,
            message_type=request.message_type,
            priority=request.priority,
            recipients=request.recipients
        )
        
        # 异步发送消息
        background_tasks.add_task(
            wechat_service.send_message,
            message.message_id
        )
        
        return MessageResponse(
            message_id=message.message_id,
            status="queued",
            sent_at=message.created_at,
            recipients_count=len(message.recipients)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

@router.post("/send-delivery-alert")
async def send_delivery_alert(
    order_id: str,
    days_remaining: int,
    background_tasks: BackgroundTasks
):
    """
    发送交期预警通知
    """
    try:
        background_tasks.add_task(
            wechat_service.send_delivery_alert,
            order_id,
            days_remaining
        )
        return {"status": "success", "message": "交期预警通知已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送交期预警失败: {str(e)}")

@router.post("/send-scheduling-notification")
async def send_scheduling_notification(
    order_id: str,
    equipment_id: str,
    start_time: datetime,
    background_tasks: BackgroundTasks
):
    """
    发送排产通知
    """
    try:
        background_tasks.add_task(
            wechat_service.send_scheduling_notification,
            order_id,
            equipment_id,
            start_time
        )
        return {"status": "success", "message": "排产通知已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送排产通知失败: {str(e)}")

@router.post("/send-daily-report")
async def send_daily_report(
    date: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    发送日报
    """
    try:
        target_date = datetime.fromisoformat(date) if date else datetime.now()
        background_tasks.add_task(
            wechat_service.send_daily_report,
            target_date
        )
        return {"status": "success", "message": "日报已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送日报失败: {str(e)}")

@router.post("/send-exception-alert")
async def send_exception_alert(
    exception_type: str,
    description: str,
    severity: str = "medium",
    background_tasks: BackgroundTasks = None
):
    """
    发送异常告警
    """
    try:
        background_tasks.add_task(
            wechat_service.send_exception_alert,
            exception_type,
            description,
            severity
        )
        return {"status": "success", "message": "异常告警已发送"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送异常告警失败: {str(e)}")

@router.get("/messages", response_model=List[dict])
async def get_messages(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    message_type: Optional[MessageType] = None
):
    """
    获取消息列表
    """
    try:
        messages = await wechat_service.get_messages(
            limit=limit,
            offset=offset,
            status=status,
            message_type=message_type
        )
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息列表失败: {str(e)}")

@router.get("/messages/{message_id}")
async def get_message(message_id: str):
    """
    获取消息详情
    """
    try:
        message = await wechat_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息详情失败: {str(e)}")

@router.get("/stats", response_model=MessageStatsResponse)
async def get_message_stats():
    """
    获取消息统计信息
    """
    try:
        stats = await wechat_service.get_message_stats()
        return MessageStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息统计失败: {str(e)}")

@router.post("/rules", response_model=NotificationRuleResponse)
async def create_notification_rule(request: NotificationRuleRequest):
    """
    创建通知规则
    """
    try:
        rule = await wechat_service.add_notification_rule(
            rule_type=request.rule_type,
            conditions=request.conditions,
            message_template=request.message_template,
            recipients=request.recipients,
            enabled=request.enabled,
            schedule=request.schedule
        )
        
        return NotificationRuleResponse(
            rule_id=rule.rule_id,
            rule_type=rule.rule_type,
            enabled=rule.enabled,
            created_at=rule.created_at,
            last_triggered=rule.last_triggered
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建通知规则失败: {str(e)}")

@router.get("/rules", response_model=List[NotificationRuleResponse])
async def get_notification_rules():
    """
    获取通知规则列表
    """
    try:
        rules = await wechat_service.get_notification_rules()
        return [
            NotificationRuleResponse(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                enabled=rule.enabled,
                created_at=rule.created_at,
                last_triggered=rule.last_triggered
            )
            for rule in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取通知规则失败: {str(e)}")

@router.put("/rules/{rule_id}")
async def update_notification_rule(
    rule_id: str,
    request: NotificationRuleRequest
):
    """
    更新通知规则
    """
    try:
        await wechat_service.update_notification_rule(
            rule_id=rule_id,
            rule_type=request.rule_type,
            conditions=request.conditions,
            message_template=request.message_template,
            recipients=request.recipients,
            enabled=request.enabled,
            schedule=request.schedule
        )
        return {"status": "success", "message": "通知规则更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新通知规则失败: {str(e)}")

@router.delete("/rules/{rule_id}")
async def delete_notification_rule(rule_id: str):
    """
    删除通知规则
    """
    try:
        await wechat_service.delete_notification_rule(rule_id)
        return {"status": "success", "message": "通知规则删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除通知规则失败: {str(e)}")

@router.post("/config")
async def update_wechat_config(request: WeChatConfigRequest):
    """
    更新微信配置
    """
    try:
        await wechat_service.update_config(
            corp_id=request.corp_id,
            corp_secret=request.corp_secret,
            agent_id=request.agent_id,
            webhook_url=request.webhook_url
        )
        return {"status": "success", "message": "微信配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新微信配置失败: {str(e)}")

@router.get("/config")
async def get_wechat_config():
    """
    获取微信配置（隐藏敏感信息）
    """
    try:
        config = await wechat_service.get_config()
        # 隐藏敏感信息
        safe_config = {
            "corp_id": config.get("corp_id", "")[:8] + "****" if config.get("corp_id") else "",
            "agent_id": config.get("agent_id", ""),
            "webhook_configured": bool(config.get("webhook_url")),
            "is_configured": bool(config.get("corp_id") and config.get("corp_secret"))
        }
        return safe_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取微信配置失败: {str(e)}")

@router.post("/test")
async def test_wechat_connection():
    """
    测试微信连接
    """
    try:
        result = await wechat_service.test_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试微信连接失败: {str(e)}")

@router.post("/process-queue")
async def process_message_queue(background_tasks: BackgroundTasks):
    """
    手动处理消息队列
    """
    try:
        background_tasks.add_task(wechat_service.process_message_queue)
        return {"status": "success", "message": "消息队列处理已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息队列失败: {str(e)}")