from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base

class Priority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EquipmentStatus(enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class ProductionOrder(Base):
    """
    生产订单模型
    """
    __tablename__ = "production_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    priority = Column(Enum(Priority), default=Priority.NORMAL)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # 时间信息
    due_date = Column(DateTime, nullable=False)
    estimated_duration = Column(Float, nullable=False)  # 预计工时（小时）
    actual_duration = Column(Float, nullable=True)  # 实际工时（小时）
    
    # 排产信息
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # 设备和物料
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    required_materials = Column(Text, nullable=True)  # JSON格式存储所需物料
    
    # 其他信息
    customer = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)  # 进度百分比
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    equipment = relationship("Equipment", back_populates="orders")
    schedule_logs = relationship("ScheduleLog", back_populates="order")

class Equipment(Base):
    """
    设备模型
    """
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.AVAILABLE)
    
    # 能力信息
    capacity = Column(Float, nullable=False)  # 产能（件/小时）
    efficiency = Column(Float, default=1.0)  # 效率系数
    
    # 维护信息
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    maintenance_interval = Column(Integer, default=720)  # 维护间隔（小时）
    
    # 位置和描述
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    utilization_rate = Column(Float, default=0.0)  # 利用率
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    orders = relationship("ProductionOrder", back_populates="equipment")
    schedule_logs = relationship("ScheduleLog", back_populates="equipment")

class Material(Base):
    """
    物料模型
    """
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)
    unit = Column(String(20), nullable=False)  # 单位
    
    # 库存信息
    current_stock = Column(Float, default=0.0)
    min_stock = Column(Float, default=0.0)  # 最小库存
    max_stock = Column(Float, default=0.0)  # 最大库存
    
    # 成本信息
    unit_cost = Column(Float, default=0.0)
    supplier = Column(String(200), nullable=True)
    lead_time = Column(Integer, default=0)  # 采购周期（天）
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScheduleLog(Base):
    """
    排产日志模型
    """
    __tablename__ = "schedule_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 关联信息
    order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    
    # 排产信息
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # 状态和结果
    status = Column(String(50), default="scheduled")
    result = Column(String(50), nullable=True)  # success, failed, cancelled
    notes = Column(Text, nullable=True)
    
    # 操作信息
    created_by = Column(String(100), nullable=True)
    operation_type = Column(String(50), default="auto_schedule")  # auto_schedule, manual_schedule, reschedule
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    order = relationship("ProductionOrder", back_populates="schedule_logs")
    equipment = relationship("Equipment", back_populates="schedule_logs")

class ScheduleRule(Base):
    """
    排产规则模型
    """
    __tablename__ = "schedule_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)  # priority, capacity, time, resource
    
    # 规则配置
    conditions = Column(Text, nullable=False)  # JSON格式存储条件
    actions = Column(Text, nullable=False)  # JSON格式存储动作
    weight = Column(Float, default=1.0)  # 权重
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScheduleOptimization(Base):
    """
    排产优化记录模型
    """
    __tablename__ = "schedule_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 优化信息
    algorithm = Column(String(100), nullable=False)  # 使用的算法
    parameters = Column(Text, nullable=True)  # JSON格式存储参数
    
    # 结果信息
    before_metrics = Column(Text, nullable=True)  # 优化前指标
    after_metrics = Column(Text, nullable=True)  # 优化后指标
    improvement = Column(Float, default=0.0)  # 改进百分比
    
    # 执行信息
    execution_time = Column(Float, default=0.0)  # 执行时间（秒）
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)