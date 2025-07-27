from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class ProgressStatus(str, enum.Enum):
    """进度状态枚举"""
    NOT_STARTED = "未开始"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    DELAYED = "延期"
    PAUSED = "暂停"
    CANCELLED = "已取消"

class QualityResult(str, enum.Enum):
    """质量检查结果枚举"""
    PASS = "合格"
    FAIL = "不合格"
    REWORK = "返工"
    PENDING = "待检"

class ProgressRecord(Base):
    """进度跟踪记录模型"""
    __tablename__ = "progress_records"
    
    id = Column(Integer, primary_key=True, index=True)
    record_no = Column(String(50), unique=True, index=True, nullable=False, comment="跟踪编号")
    
    # 关联订单和生产计划
    order_id = Column(Integer, ForeignKey("orders.id"), comment="订单ID")
    order_no = Column(String(50), nullable=False, comment="订单编号")
    plan_id = Column(Integer, ForeignKey("production_plans.id"), comment="生产计划ID")
    
    # 产品信息
    product_name = Column(String(100), nullable=False, comment="产品名称")
    product_model = Column(String(50), comment="产品型号")
    quantity = Column(Integer, nullable=False, comment="数量")
    
    # 时间信息
    plan_start_date = Column(DateTime, nullable=False, comment="计划开始日期")
    plan_end_date = Column(DateTime, nullable=False, comment="计划完成日期")
    actual_start_date = Column(DateTime, comment="实际开始日期")
    actual_end_date = Column(DateTime, comment="实际完成日期")
    
    # 进度信息
    current_stage = Column(String(50), comment="当前阶段")
    progress = Column(Integer, default=0, comment="完成进度(%)")
    status = Column(Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED, comment="状态")
    
    # 责任人信息
    responsible_person = Column(String(50), comment="负责人")
    workshop = Column(String(50), comment="车间")
    team_members = Column(Text, comment="团队成员")
    
    # 优先级
    priority = Column(String(20), default="中", comment="优先级")
    
    # 问题和风险
    issues = Column(Text, comment="存在问题")
    risks = Column(Text, comment="风险点")
    solutions = Column(Text, comment="解决方案")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    # 关联关系
    order = relationship("Order", backref="progress_records")
    production_plan = relationship("ProductionPlan", backref="progress_records")
    
    def __repr__(self):
        return f"<ProgressRecord(order_no='{self.order_no}', product='{self.product_name}', progress={self.progress}%)>"

class StageRecord(Base):
    """阶段记录模型"""
    __tablename__ = "stage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    stage_no = Column(String(50), nullable=False, comment="阶段编号")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    
    # 关联进度记录
    progress_id = Column(Integer, ForeignKey("progress_records.id"), nullable=False, comment="进度记录ID")
    
    # 阶段信息
    sequence = Column(Integer, nullable=False, comment="阶段顺序")
    description = Column(Text, comment="阶段描述")
    
    # 时间信息
    plan_start_date = Column(DateTime, nullable=False, comment="计划开始日期")
    plan_end_date = Column(DateTime, nullable=False, comment="计划完成日期")
    actual_start_date = Column(DateTime, comment="实际开始日期")
    actual_end_date = Column(DateTime, comment="实际完成日期")
    duration = Column(Integer, comment="持续时间(天)")
    
    # 进度信息
    progress = Column(Integer, default=0, comment="完成进度(%)")
    status = Column(Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED, comment="状态")
    
    # 责任人信息
    responsible_person = Column(String(50), comment="负责人")
    workshop = Column(String(50), comment="执行车间")
    equipment = Column(String(100), comment="使用设备")
    
    # 工艺信息
    process_requirements = Column(Text, comment="工艺要求")
    quality_checkpoints = Column(Text, comment="质量检查点")
    
    # 资源消耗
    material_consumption = Column(Text, comment="物料消耗")
    labor_hours = Column(Float, comment="工时")
    equipment_hours = Column(Float, comment="设备工时")
    
    # 质量信息
    quality_score = Column(Float, comment="质量评分")
    defect_count = Column(Integer, default=0, comment="缺陷数量")
    rework_count = Column(Integer, default=0, comment="返工次数")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    progress_record = relationship("ProgressRecord", backref="stage_records")
    
    def __repr__(self):
        return f"<StageRecord(stage_name='{self.stage_name}', sequence={self.sequence}, progress={self.progress}%)>"

class QualityRecord(Base):
    """质量检查记录模型"""
    __tablename__ = "quality_records"
    
    id = Column(Integer, primary_key=True, index=True)
    check_no = Column(String(50), unique=True, index=True, nullable=False, comment="检查编号")
    
    # 关联信息
    order_id = Column(Integer, ForeignKey("orders.id"), comment="订单ID")
    order_no = Column(String(50), nullable=False, comment="订单编号")
    stage_id = Column(Integer, ForeignKey("stage_records.id"), comment="阶段ID")
    stage_name = Column(String(100), nullable=False, comment="检查阶段")
    
    # 检查信息
    check_date = Column(DateTime, nullable=False, comment="检查日期")
    check_type = Column(String(50), comment="检查类型")
    check_items = Column(Text, comment="检查项目")
    check_standards = Column(Text, comment="检查标准")
    
    # 检查结果
    check_result = Column(Enum(QualityResult), nullable=False, comment="检查结果")
    quality_score = Column(Float, comment="质量评分")
    pass_rate = Column(Float, comment="合格率(%)")
    
    # 缺陷信息
    defect_count = Column(Integer, default=0, comment="缺陷数量")
    defect_types = Column(Text, comment="缺陷类型")
    defect_description = Column(Text, comment="缺陷描述")
    defect_images = Column(Text, comment="缺陷图片")
    
    # 处理信息
    corrective_actions = Column(Text, comment="纠正措施")
    preventive_actions = Column(Text, comment="预防措施")
    follow_up_required = Column(Boolean, default=False, comment="是否需要跟进")
    follow_up_date = Column(DateTime, comment="跟进日期")
    
    # 检验人员
    inspector = Column(String(50), nullable=False, comment="检验员")
    reviewer = Column(String(50), comment="复核人")
    approver = Column(String(50), comment="批准人")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    # 关联关系
    order = relationship("Order", backref="quality_records")
    stage_record = relationship("StageRecord", backref="quality_records")
    
    def __repr__(self):
        return f"<QualityRecord(check_no='{self.check_no}', stage='{self.stage_name}', result='{self.check_result}')>"

class ProgressUpdate(Base):
    """进度更新记录模型"""
    __tablename__ = "progress_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联进度记录
    progress_id = Column(Integer, ForeignKey("progress_records.id"), nullable=False, comment="进度记录ID")
    stage_id = Column(Integer, ForeignKey("stage_records.id"), comment="阶段记录ID")
    
    # 更新信息
    update_date = Column(DateTime, nullable=False, comment="更新日期")
    update_type = Column(String(50), comment="更新类型")
    previous_progress = Column(Integer, comment="之前进度(%)")
    current_progress = Column(Integer, comment="当前进度(%)")
    progress_change = Column(Integer, comment="进度变化(%)")
    
    # 状态变化
    previous_status = Column(String(50), comment="之前状态")
    current_status = Column(String(50), comment="当前状态")
    
    # 更新内容
    update_content = Column(Text, comment="更新内容")
    achievements = Column(Text, comment="完成工作")
    next_plans = Column(Text, comment="下步计划")
    
    # 问题和风险
    issues_found = Column(Text, comment="发现问题")
    risks_identified = Column(Text, comment="识别风险")
    mitigation_actions = Column(Text, comment="缓解措施")
    
    # 资源使用
    resources_used = Column(Text, comment="资源使用")
    time_spent = Column(Float, comment="耗时(小时)")
    cost_incurred = Column(Float, comment="发生成本")
    
    # 更新人员
    updated_by = Column(String(50), nullable=False, comment="更新人")
    reviewer = Column(String(50), comment="审核人")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    progress_record = relationship("ProgressRecord", backref="updates")
    stage_record = relationship("StageRecord", backref="updates")
    
    def __repr__(self):
        return f"<ProgressUpdate(date='{self.update_date}', progress={self.current_progress}%, updated_by='{self.updated_by}')>"