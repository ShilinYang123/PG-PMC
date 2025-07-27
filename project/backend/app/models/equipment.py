"""设备管理模型

定义设备管理相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.db.base_class import Base


class EquipmentStatus(PyEnum):
    """设备状态枚举"""
    RUNNING = "running"  # 运行中
    IDLE = "idle"  # 空闲
    MAINTENANCE = "maintenance"  # 维护中
    BREAKDOWN = "breakdown"  # 故障
    OFFLINE = "offline"  # 离线
    RETIRED = "retired"  # 报废


class EquipmentType(PyEnum):
    """设备类型枚举"""
    PRODUCTION = "production"  # 生产设备
    TESTING = "testing"  # 检测设备
    TRANSPORT = "transport"  # 运输设备
    AUXILIARY = "auxiliary"  # 辅助设备
    SAFETY = "safety"  # 安全设备


class MaintenanceType(PyEnum):
    """维护类型枚举"""
    PREVENTIVE = "preventive"  # 预防性维护
    CORRECTIVE = "corrective"  # 纠正性维护
    EMERGENCY = "emergency"  # 紧急维护
    ROUTINE = "routine"  # 例行维护
    OVERHAUL = "overhaul"  # 大修


class MaintenanceStatus(PyEnum):
    """维护状态枚举"""
    PLANNED = "planned"  # 计划中
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    POSTPONED = "postponed"  # 已延期


class Equipment(Base):
    """设备表"""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_code = Column(String(50), unique=True, index=True, comment="设备编码")
    equipment_name = Column(String(200), nullable=False, comment="设备名称")
    equipment_type = Column(Enum(EquipmentType), nullable=False, comment="设备类型")
    
    # 基本信息
    model = Column(String(100), comment="设备型号")
    manufacturer = Column(String(200), comment="制造商")
    serial_number = Column(String(100), comment="序列号")
    purchase_date = Column(DateTime, comment="采购日期")
    installation_date = Column(DateTime, comment="安装日期")
    warranty_expiry = Column(DateTime, comment="保修到期日")
    
    # 技术参数
    specifications = Column(Text, comment="技术规格（JSON格式）")
    capacity = Column(Float, comment="产能")
    power_consumption = Column(Float, comment="功耗（kW）")
    operating_temperature = Column(String(50), comment="工作温度范围")
    operating_pressure = Column(String(50), comment="工作压力范围")
    
    # 位置信息
    location = Column(String(200), comment="设备位置")
    workshop = Column(String(100), comment="车间")
    production_line = Column(String(100), comment="生产线")
    
    # 状态信息
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.IDLE, comment="设备状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 运行统计
    total_runtime = Column(Float, default=0, comment="总运行时间（小时）")
    total_downtime = Column(Float, default=0, comment="总停机时间（小时）")
    total_maintenance_time = Column(Float, default=0, comment="总维护时间（小时）")
    availability_rate = Column(Float, comment="可用率")
    
    # 成本信息
    purchase_cost = Column(Float, comment="采购成本")
    installation_cost = Column(Float, comment="安装成本")
    annual_maintenance_cost = Column(Float, comment="年维护成本")
    depreciation_rate = Column(Float, comment="折旧率")
    
    # 责任人
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作员ID")
    maintainer_id = Column(Integer, ForeignKey("users.id"), comment="维护员ID")
    manager_id = Column(Integer, ForeignKey("users.id"), comment="设备管理员ID")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注
    description = Column(Text, comment="设备描述")
    remarks = Column(Text, comment="备注")
    
    # 关联关系
    operator = relationship("User", foreign_keys=[operator_id])
    maintainer = relationship("User", foreign_keys=[maintainer_id])
    manager = relationship("User", foreign_keys=[manager_id])
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment")
    operation_logs = relationship("EquipmentOperationLog", back_populates="equipment")


class MaintenanceRecord(Base):
    """维护记录表"""
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    maintenance_number = Column(String(50), unique=True, index=True, comment="维护单号")
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, comment="设备ID")
    
    # 维护信息
    maintenance_type = Column(Enum(MaintenanceType), nullable=False, comment="维护类型")
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.PLANNED, comment="维护状态")
    priority = Column(String(20), comment="优先级")
    
    # 计划信息
    planned_start_time = Column(DateTime, nullable=False, comment="计划开始时间")
    planned_end_time = Column(DateTime, comment="计划结束时间")
    planned_duration = Column(Float, comment="计划持续时间（小时）")
    
    # 实际信息
    actual_start_time = Column(DateTime, comment="实际开始时间")
    actual_end_time = Column(DateTime, comment="实际结束时间")
    actual_duration = Column(Float, comment="实际持续时间（小时）")
    
    # 维护内容
    maintenance_items = Column(Text, comment="维护项目（JSON格式）")
    maintenance_description = Column(Text, comment="维护描述")
    parts_replaced = Column(Text, comment="更换部件（JSON格式）")
    materials_used = Column(Text, comment="使用材料（JSON格式）")
    
    # 结果信息
    maintenance_result = Column(Text, comment="维护结果")
    issues_found = Column(Text, comment="发现问题")
    recommendations = Column(Text, comment="建议")
    next_maintenance_date = Column(DateTime, comment="下次维护日期")
    
    # 成本信息
    labor_cost = Column(Float, comment="人工成本")
    parts_cost = Column(Float, comment="配件成本")
    material_cost = Column(Float, comment="材料成本")
    total_cost = Column(Float, comment="总成本")
    
    # 人员信息
    assigned_to = Column(Integer, ForeignKey("users.id"), comment="分配给")
    performed_by = Column(Integer, ForeignKey("users.id"), comment="执行人")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="批准人")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注
    remarks = Column(Text, comment="备注")
    
    # 关联关系
    equipment = relationship("Equipment", back_populates="maintenance_records")
    assignee = relationship("User", foreign_keys=[assigned_to])
    performer = relationship("User", foreign_keys=[performed_by])
    approver = relationship("User", foreign_keys=[approved_by])


class EquipmentOperationLog(Base):
    """设备操作日志表"""
    __tablename__ = "equipment_operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, comment="设备ID")
    
    # 操作信息
    operation_type = Column(String(50), nullable=False, comment="操作类型")
    operation_description = Column(Text, comment="操作描述")
    
    # 状态变化
    previous_status = Column(String(50), comment="之前状态")
    new_status = Column(String(50), comment="新状态")
    
    # 运行参数
    operating_parameters = Column(Text, comment="运行参数（JSON格式）")
    performance_metrics = Column(Text, comment="性能指标（JSON格式）")
    
    # 操作人员
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作员ID")
    
    # 时间信息
    operation_time = Column(DateTime, default=func.now(), comment="操作时间")
    duration = Column(Float, comment="持续时间（小时）")
    
    # 备注
    remarks = Column(Text, comment="备注")
    
    # 关联关系
    equipment = relationship("Equipment", back_populates="operation_logs")
    operator = relationship("User")


class EquipmentAlert(Base):
    """设备预警表"""
    __tablename__ = "equipment_alerts"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, comment="设备ID")
    
    # 预警信息
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    alert_level = Column(String(20), nullable=False, comment="预警级别")
    title = Column(String(200), nullable=False, comment="预警标题")
    description = Column(Text, comment="预警描述")
    
    # 触发条件
    trigger_condition = Column(Text, comment="触发条件")
    threshold_value = Column(Float, comment="阈值")
    actual_value = Column(Float, comment="实际值")
    
    # 处理信息
    status = Column(String(20), default="active", comment="状态")
    handled_by = Column(Integer, ForeignKey("users.id"), comment="处理人ID")
    handled_at = Column(DateTime, comment="处理时间")
    handling_notes = Column(Text, comment="处理说明")
    
    # 时间信息
    triggered_at = Column(DateTime, default=func.now(), comment="触发时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    equipment = relationship("Equipment")
    handler = relationship("User")


class EquipmentSpare(Base):
    """设备备件表"""
    __tablename__ = "equipment_spares"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, comment="设备ID")
    
    # 备件信息
    spare_code = Column(String(50), index=True, comment="备件编码")
    spare_name = Column(String(200), nullable=False, comment="备件名称")
    specification = Column(String(500), comment="规格型号")
    manufacturer = Column(String(200), comment="制造商")
    
    # 库存信息
    current_stock = Column(Integer, default=0, comment="当前库存")
    min_stock = Column(Integer, comment="最小库存")
    max_stock = Column(Integer, comment="最大库存")
    unit = Column(String(20), comment="单位")
    
    # 成本信息
    unit_price = Column(Float, comment="单价")
    total_value = Column(Float, comment="总价值")
    
    # 供应商信息
    supplier = Column(String(200), comment="供应商")
    lead_time = Column(Integer, comment="采购周期（天）")
    
    # 使用信息
    usage_frequency = Column(String(50), comment="使用频率")
    last_used_date = Column(DateTime, comment="最后使用日期")
    replacement_cycle = Column(Integer, comment="更换周期（天）")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 备注
    remarks = Column(Text, comment="备注")
    
    # 关联关系
    equipment = relationship("Equipment")