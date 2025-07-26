from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class PlanStatus(str, enum.Enum):
    """计划状态枚举"""
    DRAFT = "草稿"
    CONFIRMED = "已确认"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    PAUSED = "暂停"

class PlanPriority(str, enum.Enum):
    """计划优先级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"

class StageStatus(str, enum.Enum):
    """阶段状态枚举"""
    PENDING = "待开始"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    PAUSED = "暂停"
    CANCELLED = "已取消"

class ProductionPlan(Base):
    """生产计划模型"""
    __tablename__ = "production_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_no = Column(String(50), unique=True, index=True, nullable=False, comment="计划编号")
    plan_name = Column(String(100), nullable=False, comment="计划名称")
    
    # 关联订单
    order_id = Column(Integer, ForeignKey("orders.id"), comment="关联订单ID")
    order_no = Column(String(50), comment="订单编号")
    
    # 产品信息
    product_name = Column(String(100), nullable=False, comment="产品名称")
    product_model = Column(String(50), comment="产品型号")
    quantity = Column(Integer, nullable=False, comment="计划数量")
    unit = Column(String(20), nullable=False, comment="单位")
    
    # 时间计划
    plan_start_date = Column(DateTime, nullable=False, comment="计划开始日期")
    plan_end_date = Column(DateTime, nullable=False, comment="计划完成日期")
    actual_start_date = Column(DateTime, comment="实际开始日期")
    actual_end_date = Column(DateTime, comment="实际完成日期")
    
    # 状态和优先级
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, comment="计划状态")
    priority = Column(Enum(PlanPriority), default=PlanPriority.MEDIUM, comment="优先级")
    progress = Column(Integer, default=0, comment="完成进度(%)")
    
    # 资源分配
    workshop = Column(String(50), comment="生产车间")
    production_line = Column(String(50), comment="生产线")
    responsible_person = Column(String(50), comment="负责人")
    team_members = Column(Text, comment="团队成员")
    
    # 工艺信息
    process_flow = Column(Text, comment="工艺流程")
    technical_requirements = Column(Text, comment="技术要求")
    quality_standards = Column(Text, comment="质量标准")
    
    # 成本预算
    material_cost = Column(Float, comment="材料成本")
    labor_cost = Column(Float, comment="人工成本")
    equipment_cost = Column(Float, comment="设备成本")
    other_cost = Column(Float, comment="其他成本")
    total_cost = Column(Float, comment="总成本")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    # 关联关系
    order = relationship("Order", backref="production_plans")
    
    def __repr__(self):
        return f"<ProductionPlan(plan_no='{self.plan_no}', product='{self.product_name}', status='{self.status}')>"

class ProductionStage(Base):
    """生产阶段模型"""
    __tablename__ = "production_stages"
    
    id = Column(Integer, primary_key=True, index=True)
    stage_no = Column(String(50), nullable=False, comment="阶段编号")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    
    # 关联生产计划
    plan_id = Column(Integer, ForeignKey("production_plans.id"), nullable=False, comment="生产计划ID")
    
    # 阶段信息
    sequence = Column(Integer, nullable=False, comment="阶段顺序")
    description = Column(Text, comment="阶段描述")
    
    # 时间计划
    plan_start_date = Column(DateTime, nullable=False, comment="计划开始日期")
    plan_end_date = Column(DateTime, nullable=False, comment="计划完成日期")
    actual_start_date = Column(DateTime, comment="实际开始日期")
    actual_end_date = Column(DateTime, comment="实际完成日期")
    
    # 状态和进度
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, comment="阶段状态")
    progress = Column(Integer, default=0, comment="完成进度(%)")
    
    # 资源分配
    workshop = Column(String(50), comment="执行车间")
    responsible_person = Column(String(50), comment="负责人")
    required_skills = Column(Text, comment="所需技能")
    
    # 质量要求
    quality_checkpoints = Column(Text, comment="质量检查点")
    acceptance_criteria = Column(Text, comment="验收标准")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    production_plan = relationship("ProductionPlan", backref="stages")
    
    def __repr__(self):
        return f"<ProductionStage(stage_name='{self.stage_name}', sequence={self.sequence}, status='{self.status}')>"