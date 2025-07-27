"""催办记录数据模型

定义催办系统相关的数据库模型：
- ReminderRecord: 催办记录
- ReminderRule: 催办规则
- ReminderResponse: 催办响应
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from ..db.database import Base


class ReminderType(str, Enum):
    """催办类型"""
    ORDER_DUE = "order_due"  # 订单交期
    TASK_OVERDUE = "task_overdue"  # 任务逾期
    QUALITY_ISSUE = "quality_issue"  # 质量问题
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"  # 设备维护
    MATERIAL_SHORTAGE = "material_shortage"  # 物料短缺
    CUSTOM = "custom"  # 自定义催办


class ReminderLevel(str, Enum):
    """催办级别"""
    LOW = "low"  # 低级
    NORMAL = "normal"  # 普通
    HIGH = "high"  # 高级
    URGENT = "urgent"  # 紧急
    CRITICAL = "critical"  # 严重


class ReminderStatus(str, Enum):
    """催办状态"""
    PENDING = "pending"  # 待发送
    SENT = "sent"  # 已发送
    RESPONDED = "responded"  # 已响应
    ESCALATED = "escalated"  # 已升级
    CANCELLED = "cancelled"  # 已取消


class CompletionStatus(str, Enum):
    """完成状态"""
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ReminderRecord(Base):
    """催办记录模型"""
    __tablename__ = "reminder_records"
    
    id = Column(Integer, primary_key=True, index=True, comment="催办记录ID")
    
    # 基本信息
    reminder_type = Column(SQLEnum(ReminderType), nullable=False, comment="催办类型")
    level = Column(SQLEnum(ReminderLevel), default=ReminderLevel.NORMAL, comment="催办级别")
    status = Column(SQLEnum(ReminderStatus), default=ReminderStatus.PENDING, comment="催办状态")
    
    # 关联信息
    related_type = Column(String(50), nullable=False, comment="关联对象类型")
    related_id = Column(Integer, nullable=False, comment="关联对象ID")
    
    # 接收者信息
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="接收者用户ID")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    
    # 发送者信息
    sender_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="发送者用户ID")
    sender_user = relationship("User", foreign_keys=[sender_user_id])
    
    # 内容信息
    title = Column(String(200), nullable=False, comment="催办标题")
    content = Column(Text, nullable=False, comment="催办内容")
    data = Column(JSON, nullable=True, comment="催办相关数据")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    response_time = Column(DateTime, nullable=True, comment="响应时间")
    escalation_time = Column(DateTime, nullable=True, comment="升级时间")
    
    # 状态标记
    is_responded = Column(Boolean, default=False, comment="是否已响应")
    is_escalated = Column(Boolean, default=False, comment="是否已升级")
    escalation_count = Column(Integer, default=0, comment="升级次数")
    
    # 规则关联
    rule_id = Column(Integer, ForeignKey("reminder_rules.id"), nullable=True, comment="关联规则ID")
    rule = relationship("ReminderRule", back_populates="records")
    
    # 响应记录
    responses = relationship("ReminderResponse", back_populates="reminder", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ReminderRecord(id={self.id}, type={self.reminder_type}, level={self.level})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "reminder_type": self.reminder_type.value,
            "level": self.level.value,
            "status": self.status.value,
            "related_type": self.related_type,
            "related_id": self.related_id,
            "recipient_user_id": self.recipient_user_id,
            "sender_user_id": self.sender_user_id,
            "title": self.title,
            "content": self.content,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "response_time": self.response_time.isoformat() if self.response_time else None,
            "escalation_time": self.escalation_time.isoformat() if self.escalation_time else None,
            "is_responded": self.is_responded,
            "is_escalated": self.is_escalated,
            "escalation_count": self.escalation_count,
            "rule_id": self.rule_id
        }


class ReminderRule(Base):
    """催办规则模型"""
    __tablename__ = "reminder_rules"
    
    id = Column(Integer, primary_key=True, index=True, comment="规则ID")
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    reminder_type = Column(SQLEnum(ReminderType), nullable=False, comment="催办类型")
    
    # 触发条件
    trigger_conditions = Column(JSON, nullable=False, comment="触发条件")
    
    # 催办配置
    initial_level = Column(SQLEnum(ReminderLevel), default=ReminderLevel.NORMAL, comment="初始级别")
    escalation_intervals = Column(JSON, nullable=True, comment="升级间隔配置")
    max_escalations = Column(Integer, default=3, comment="最大升级次数")
    
    # 接收者配置
    recipient_config = Column(JSON, nullable=False, comment="接收者配置")
    
    # 模板配置
    title_template = Column(String(200), nullable=False, comment="标题模板")
    content_template = Column(Text, nullable=False, comment="内容模板")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    creator = relationship("User")
    
    # 关联记录
    records = relationship("ReminderRecord", back_populates="rule")
    
    def __repr__(self):
        return f"<ReminderRule(id={self.id}, name={self.name}, type={self.reminder_type})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "reminder_type": self.reminder_type.value,
            "trigger_conditions": self.trigger_conditions,
            "initial_level": self.initial_level.value,
            "escalation_intervals": self.escalation_intervals,
            "max_escalations": self.max_escalations,
            "recipient_config": self.recipient_config,
            "title_template": self.title_template,
            "content_template": self.content_template,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }


class ReminderResponse(Base):
    """催办响应模型"""
    __tablename__ = "reminder_responses"
    
    id = Column(Integer, primary_key=True, index=True, comment="响应ID")
    
    # 关联催办
    reminder_id = Column(Integer, ForeignKey("reminder_records.id"), nullable=False, comment="催办记录ID")
    reminder = relationship("ReminderRecord", back_populates="responses")
    
    # 响应者信息
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="响应者ID")
    responder = relationship("User")
    
    # 响应内容
    response_type = Column(String(50), nullable=False, comment="响应类型")
    response_content = Column(Text, nullable=True, comment="响应内容")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    
    # 时间信息
    response_time = Column(DateTime, default=datetime.utcnow, comment="响应时间")
    
    # 处理结果
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    resolution_note = Column(Text, nullable=True, comment="解决说明")
    
    def __repr__(self):
        return f"<ReminderResponse(id={self.id}, reminder_id={self.reminder_id}, type={self.response_type})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "reminder_id": self.reminder_id,
            "responder_id": self.responder_id,
            "response_type": self.response_type,
            "response_content": self.response_content,
            "response_data": self.response_data,
            "response_time": self.response_time.isoformat() if self.response_time else None,
            "is_resolved": self.is_resolved,
            "resolution_note": self.resolution_note
        }


# 为了向后兼容，添加Reminder别名
Reminder = ReminderRecord