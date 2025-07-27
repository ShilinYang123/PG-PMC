from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.reminder import ReminderType, ReminderLevel, ReminderStatus, CompletionStatus


# 基础模式
class ReminderRecordBase(BaseModel):
    reminder_type: ReminderType = Field(..., description="催办类型")
    target_id: int = Field(..., description="目标对象ID")
    target_type: str = Field(..., description="目标对象类型")
    title: str = Field(..., max_length=200, description="催办标题")
    content: Optional[str] = Field(None, description="催办内容")
    recipient_user_ids: List[int] = Field(..., description="接收人用户ID列表")
    sender_user_id: Optional[int] = Field(None, description="发送人用户ID")
    due_date: Optional[datetime] = Field(None, description="截止时间")
    priority_level: ReminderLevel = Field(ReminderLevel.NORMAL, description="优先级")
    
    @validator('recipient_user_ids')
    def validate_recipient_user_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('至少需要指定一个接收人')
        return v


class ReminderRecordCreate(ReminderRecordBase):
    pass


class ReminderRecordUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="催办标题")
    content: Optional[str] = Field(None, description="催办内容")
    recipient_user_ids: Optional[List[int]] = Field(None, description="接收人用户ID列表")
    due_date: Optional[datetime] = Field(None, description="截止时间")
    priority_level: Optional[ReminderLevel] = Field(None, description="优先级")
    status: Optional[ReminderStatus] = Field(None, description="状态")
    
    @validator('recipient_user_ids')
    def validate_recipient_user_ids(cls, v):
        if v is not None and (not v or len(v) == 0):
            raise ValueError('至少需要指定一个接收人')
        return v


class ReminderRecordResponse(ReminderRecordBase):
    id: int
    status: ReminderStatus
    sent_count: int = Field(0, description="发送次数")
    last_sent_at: Optional[datetime] = Field(None, description="最后发送时间")
    responded_at: Optional[datetime] = Field(None, description="响应时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 催办响应模式
class ReminderResponseBase(BaseModel):
    response_content: str = Field(..., description="响应内容")
    response_user_id: int = Field(..., description="响应用户ID")
    action_taken: Optional[str] = Field(None, description="采取的行动")
    completion_status: Optional[CompletionStatus] = Field(None, description="完成状态")


class ReminderResponseCreate(ReminderResponseBase):
    pass


class ReminderResponseUpdate(BaseModel):
    response_content: Optional[str] = Field(None, description="响应内容")
    action_taken: Optional[str] = Field(None, description="采取的行动")
    completion_status: Optional[CompletionStatus] = Field(None, description="完成状态")


class ReminderResponseResponse(ReminderResponseBase):
    id: int
    reminder_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 催办规则模式
class ReminderRuleBase(BaseModel):
    rule_name: str = Field(..., max_length=100, description="规则名称")
    reminder_type: ReminderType = Field(..., description="催办类型")
    target_type: str = Field(..., description="目标对象类型")
    trigger_conditions: Dict[str, Any] = Field(..., description="触发条件")
    reminder_intervals: List[int] = Field(..., description="催办间隔（小时）")
    max_reminders: int = Field(3, description="最大催办次数")
    escalation_rules: Optional[Dict[str, Any]] = Field(None, description="升级规则")
    is_active: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="规则描述")
    
    @validator('reminder_intervals')
    def validate_reminder_intervals(cls, v):
        if not v or len(v) == 0:
            raise ValueError('至少需要设置一个催办间隔')
        if any(interval <= 0 for interval in v):
            raise ValueError('催办间隔必须大于0')
        return v
    
    @validator('max_reminders')
    def validate_max_reminders(cls, v):
        if v <= 0:
            raise ValueError('最大催办次数必须大于0')
        return v


class ReminderRuleCreate(ReminderRuleBase):
    pass


class ReminderRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=100, description="规则名称")
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    reminder_intervals: Optional[List[int]] = Field(None, description="催办间隔（小时）")
    max_reminders: Optional[int] = Field(None, description="最大催办次数")
    escalation_rules: Optional[Dict[str, Any]] = Field(None, description="升级规则")
    is_active: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="规则描述")
    
    @validator('reminder_intervals')
    def validate_reminder_intervals(cls, v):
        if v is not None and (not v or len(v) == 0):
            raise ValueError('至少需要设置一个催办间隔')
        if v is not None and any(interval <= 0 for interval in v):
            raise ValueError('催办间隔必须大于0')
        return v
    
    @validator('max_reminders')
    def validate_max_reminders(cls, v):
        if v is not None and v <= 0:
            raise ValueError('最大催办次数必须大于0')
        return v


class ReminderRuleResponse(ReminderRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 查询参数模式
class ReminderQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    reminder_type: Optional[ReminderType] = Field(None, description="催办类型")
    status: Optional[ReminderStatus] = Field(None, description="状态")
    level: Optional[ReminderLevel] = Field(None, description="优先级")
    target_type: Optional[str] = Field(None, description="目标对象类型")
    target_id: Optional[int] = Field(None, description="目标对象ID")
    recipient_user_id: Optional[int] = Field(None, description="接收人用户ID")
    sender_user_id: Optional[int] = Field(None, description="发送人用户ID")
    due_date_start: Optional[datetime] = Field(None, description="截止时间开始")
    due_date_end: Optional[datetime] = Field(None, description="截止时间结束")
    created_start: Optional[datetime] = Field(None, description="创建时间开始")
    created_end: Optional[datetime] = Field(None, description="创建时间结束")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    
    class Config:
        # 允许从查询参数构造
        extra = "forbid"


# 统计信息模式
class ReminderStatistics(BaseModel):
    total_reminders: int = Field(0, description="总催办数")
    pending_reminders: int = Field(0, description="待处理催办数")
    sent_reminders: int = Field(0, description="已发送催办数")
    responded_reminders: int = Field(0, description="已响应催办数")
    completed_reminders: int = Field(0, description="已完成催办数")
    overdue_reminders: int = Field(0, description="逾期催办数")
    
    # 按类型统计
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")
    
    # 按优先级统计
    by_level: Dict[str, int] = Field(default_factory=dict, description="按优先级统计")
    
    # 按状态统计
    by_status: Dict[str, int] = Field(default_factory=dict, description="按状态统计")
    
    # 响应率统计
    response_rate: float = Field(0.0, description="响应率")
    completion_rate: float = Field(0.0, description="完成率")
    
    # 平均响应时间（小时）
    avg_response_time: Optional[float] = Field(None, description="平均响应时间（小时）")
    
    # 平均完成时间（小时）
    avg_completion_time: Optional[float] = Field(None, description="平均完成时间（小时）")
    
    class Config:
        from_attributes = True


# 批量操作模式
class BatchReminderOperation(BaseModel):
    reminder_ids: List[int] = Field(..., description="催办记录ID列表")
    operation: str = Field(..., pattern="^(mark_sent|mark_responded|mark_completed|cancel)$", description="操作类型")
    operation_data: Optional[Dict[str, Any]] = Field(None, description="操作数据")
    
    @validator('reminder_ids')
    def validate_reminder_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('至少需要指定一个催办记录ID')
        return v


class BatchOperationResult(BaseModel):
    success_count: int = Field(0, description="成功数量")
    failed_count: int = Field(0, description="失败数量")
    failed_items: List[Dict[str, Any]] = Field(default_factory=list, description="失败项目详情")
    message: str = Field("", description="操作结果消息")


# 催办模板模式
class ReminderTemplate(BaseModel):
    template_name: str = Field(..., max_length=100, description="模板名称")
    reminder_type: ReminderType = Field(..., description="催办类型")
    title_template: str = Field(..., description="标题模板")
    content_template: str = Field(..., description="内容模板")
    default_level: ReminderLevel = Field(ReminderLevel.NORMAL, description="默认优先级")
    template_variables: List[str] = Field(default_factory=list, description="模板变量")
    is_active: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="模板描述")
    
    class Config:
        from_attributes = True