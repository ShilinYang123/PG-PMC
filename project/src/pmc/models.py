"""PMC系统数据模型

定义PMC系统中的核心业务对象和数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "待开始"
    IN_PROGRESS = "进行中"
    PAUSED = "暂停"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    DELAYED = "延期"


class AlertSeverity(Enum):
    """预警严重程度枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "紧急"


class AlertType(Enum):
    """预警类型枚举"""
    QUALITY_ISSUE = "质量问题"
    EQUIPMENT_FAILURE = "设备故障"
    MATERIAL_SHORTAGE = "物料短缺"
    SCHEDULE_DELAY = "进度延误"
    SAFETY_INCIDENT = "安全事故"
    RESOURCE_CONFLICT = "资源冲突"
    DELIVERY_RISK = "交期风险"


@dataclass
class ProductionTask:
    """生产任务模型"""
    task_id: str
    product_name: str
    product_code: str
    quantity: int
    unit: str
    status: TaskStatus
    priority: int
    planned_start: datetime
    planned_completion: datetime
    actual_start: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    progress: float = 0.0  # 进度百分比 0-100
    responsible_person: str = ""
    department: str = ""
    workshop: str = ""
    equipment_required: List[str] = field(default_factory=list)
    materials_required: List[Dict[str, Any]] = field(default_factory=list)
    quality_requirements: str = ""
    notes: str = ""
    additional_info: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """后处理初始化"""
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
    
    @property
    def is_overdue(self) -> bool:
        """是否超期"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False
        return datetime.now() > self.planned_completion
    
    @property
    def days_remaining(self) -> int:
        """剩余天数"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return 0
        delta = self.planned_completion - datetime.now()
        return max(0, delta.days)
    
    def update_progress(self, progress: float, notes: str = ""):
        """更新进度"""
        self.progress = max(0, min(100, progress))
        if notes:
            self.notes = notes
        self.updated_at = datetime.now()
        
        # 自动更新状态
        if self.progress >= 100 and self.status != TaskStatus.COMPLETED:
            self.status = TaskStatus.COMPLETED
            self.actual_completion = datetime.now()
        elif self.progress > 0 and self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS
            self.actual_start = datetime.now()


@dataclass
class ExceptionAlert:
    """异常预警模型"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    affected_scope: str  # 影响范围
    occurrence_time: datetime
    detected_by: str  # 检测人/系统
    responsible_person: str = ""
    department: str = ""
    recommended_action: str = ""
    current_status: str = "待处理"
    resolution_notes: str = ""
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """后处理初始化"""
        if isinstance(self.alert_type, str):
            self.alert_type = AlertType(self.alert_type)
        if isinstance(self.severity, str):
            self.severity = AlertSeverity(self.severity)
    
    @property
    def is_resolved(self) -> bool:
        """是否已解决"""
        return self.resolved_at is not None
    
    @property
    def duration_hours(self) -> float:
        """持续时间（小时）"""
        end_time = self.resolved_at or datetime.now()
        delta = end_time - self.occurrence_time
        return delta.total_seconds() / 3600
    
    def resolve(self, resolution_notes: str, resolved_by: str = ""):
        """标记为已解决"""
        self.current_status = "已解决"
        self.resolution_notes = resolution_notes
        self.resolved_at = datetime.now()
        if resolved_by:
            self.responsible_person = resolved_by


@dataclass
class MeetingMinutes:
    """会议纪要模型"""
    meeting_id: str
    meeting_number: str  # 会议编号，如 "105"
    title: str
    meeting_time: datetime
    location: str
    organizer: str
    attendees: List[str]
    main_topics: List[str]  # 主要议题
    decisions: List[str]  # 决策事项
    action_items: List[str]  # 行动项
    next_meeting: Optional[datetime] = None
    meeting_type: str = "PMC生产协调会议"
    notes: str = ""
    attachments: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def attendee_count(self) -> int:
        """参会人数"""
        return len(self.attendees)
    
    @property
    def action_item_count(self) -> int:
        """行动项数量"""
        return len(self.action_items)


@dataclass
class DeliveryReminder:
    """供货提醒模型"""
    reminder_id: str
    order_id: str
    customer_name: str
    product_info: str
    original_delivery: datetime  # 原定交期
    adjusted_delivery: datetime  # 调整后交期
    advance_days: float  # 提前天数
    reason: str = ""  # 调整原因
    affected_departments: List[str] = field(default_factory=list)
    preparation_requirements: List[str] = field(default_factory=list)
    contact_person: str = ""
    urgency_level: str = "正常"
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_urgent(self) -> bool:
        """是否紧急"""
        return self.advance_days >= 1.0 or self.urgency_level == "紧急"
    
    @property
    def time_saved_hours(self) -> float:
        """节省的时间（小时）"""
        return self.advance_days * 24


@dataclass
class ProductionMetrics:
    """生产指标模型"""
    date: datetime
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    average_completion_rate: float  # 平均完成率
    quality_pass_rate: float  # 质量合格率
    equipment_utilization: float  # 设备利用率
    material_waste_rate: float  # 物料浪费率
    on_time_delivery_rate: float  # 准时交付率
    total_alerts: int
    resolved_alerts: int
    average_resolution_time: float  # 平均解决时间（小时）
    
    @property
    def completion_rate(self) -> float:
        """任务完成率"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def alert_resolution_rate(self) -> float:
        """预警解决率"""
        if self.total_alerts == 0:
            return 100.0
        return (self.resolved_alerts / self.total_alerts) * 100


@dataclass
class NotificationLog:
    """通知日志模型"""
    log_id: str
    notification_type: str
    title: str
    content: str
    recipients: List[str]
    channels: List[str]
    status: str  # 发送状态：success, failed, pending
    sent_at: datetime
    delivery_status: Dict[str, str] = field(default_factory=dict)  # 各渠道的投递状态
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_successful(self) -> bool:
        """是否发送成功"""
        return self.status == "success"
    
    @property
    def has_failures(self) -> bool:
        """是否有失败的渠道"""
        return any(status == "failed" for status in self.delivery_status.values())


@dataclass
class SystemStatus:
    """系统状态模型"""
    timestamp: datetime
    service_name: str
    version: str
    status: str  # running, stopped, error
    uptime_seconds: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    processed_messages: int
    failed_messages: int
    queue_size: int
    last_error: Optional[str] = None
    
    @property
    def uptime_hours(self) -> float:
        """运行时间（小时）"""
        return self.uptime_seconds / 3600
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.processed_messages + self.failed_messages
        if total == 0:
            return 100.0
        return (self.processed_messages / total) * 100