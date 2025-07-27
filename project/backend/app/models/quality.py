"""质量检查模型

定义质量检查相关的数据库模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from app.db.base_class import Base


class QualityResult(PyEnum):
    """质量检查结果枚举"""
    PASS = "pass"  # 通过
    FAIL = "fail"  # 不通过
    PENDING = "pending"  # 待检查
    REWORK = "rework"  # 返工
    SCRAP = "scrap"  # 报废


class QualityCheckType(PyEnum):
    """质量检查类型枚举"""
    INCOMING = "incoming"  # 来料检验
    IN_PROCESS = "in_process"  # 过程检验
    FINAL = "final"  # 最终检验
    OUTGOING = "outgoing"  # 出货检验
    SPECIAL = "special"  # 特殊检验


class QualityCheck(Base):
    """质量检查记录表"""
    __tablename__ = "quality_checks"

    id = Column(Integer, primary_key=True, index=True)
    check_number = Column(String(50), unique=True, index=True, comment="检查单号")
    check_type = Column(Enum(QualityCheckType), nullable=False, comment="检查类型")
    
    # 关联信息
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, comment="订单ID")
    production_plan_id = Column(Integer, ForeignKey("production_plans.id"), nullable=True, comment="生产计划ID")
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True, comment="物料ID")
    
    # 检查信息
    product_name = Column(String(200), nullable=False, comment="产品名称")
    product_spec = Column(String(500), comment="产品规格")
    batch_number = Column(String(100), comment="批次号")
    check_quantity = Column(Integer, nullable=False, comment="检查数量")
    sample_quantity = Column(Integer, comment="抽样数量")
    
    # 检查结果
    result = Column(Enum(QualityResult), default=QualityResult.PENDING, comment="检查结果")
    pass_quantity = Column(Integer, default=0, comment="合格数量")
    fail_quantity = Column(Integer, default=0, comment="不合格数量")
    pass_rate = Column(Float, comment="合格率")
    
    # 检查详情
    check_items = Column(Text, comment="检查项目（JSON格式）")
    check_standards = Column(Text, comment="检查标准（JSON格式）")
    check_results = Column(Text, comment="检查结果详情（JSON格式）")
    defect_description = Column(Text, comment="缺陷描述")
    defect_images = Column(Text, comment="缺陷图片（JSON格式）")
    
    # 处理信息
    corrective_action = Column(Text, comment="纠正措施")
    preventive_action = Column(Text, comment="预防措施")
    rework_instructions = Column(Text, comment="返工指导")
    
    # 人员信息
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="检验员ID")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核员ID")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="批准人ID")
    
    # 时间信息
    check_date = Column(DateTime, nullable=False, comment="检查日期")
    review_date = Column(DateTime, comment="审核日期")
    approval_date = Column(DateTime, comment="批准日期")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否有效")
    remarks = Column(Text, comment="备注")
    
    # 关联关系
    order = relationship("Order", back_populates="quality_checks")
    production_plan = relationship("ProductionPlan", back_populates="quality_checks")
    material = relationship("Material", back_populates="quality_checks")
    inspector = relationship("User", foreign_keys=[inspector_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    approver = relationship("User", foreign_keys=[approver_id])


class QualityStandard(Base):
    """质量标准表"""
    __tablename__ = "quality_standards"

    id = Column(Integer, primary_key=True, index=True)
    standard_code = Column(String(50), unique=True, index=True, comment="标准编码")
    standard_name = Column(String(200), nullable=False, comment="标准名称")
    standard_type = Column(String(50), comment="标准类型")
    
    # 适用范围
    product_category = Column(String(100), comment="产品类别")
    material_type = Column(String(100), comment="物料类型")
    process_stage = Column(String(100), comment="工艺阶段")
    
    # 标准内容
    check_items = Column(Text, nullable=False, comment="检查项目（JSON格式）")
    acceptance_criteria = Column(Text, nullable=False, comment="验收标准（JSON格式）")
    sampling_plan = Column(Text, comment="抽样方案（JSON格式）")
    test_methods = Column(Text, comment="检测方法（JSON格式）")
    
    # 版本信息
    version = Column(String(20), default="1.0", comment="版本号")
    effective_date = Column(DateTime, nullable=False, comment="生效日期")
    expiry_date = Column(DateTime, comment="失效日期")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="批准人ID")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class QualityDefect(Base):
    """质量缺陷表"""
    __tablename__ = "quality_defects"

    id = Column(Integer, primary_key=True, index=True)
    defect_code = Column(String(50), unique=True, index=True, comment="缺陷编码")
    defect_name = Column(String(200), nullable=False, comment="缺陷名称")
    defect_category = Column(String(100), comment="缺陷类别")
    severity_level = Column(String(20), comment="严重程度")
    
    # 缺陷描述
    description = Column(Text, comment="缺陷描述")
    causes = Column(Text, comment="可能原因（JSON格式）")
    detection_methods = Column(Text, comment="检测方法")
    
    # 处理方式
    corrective_actions = Column(Text, comment="纠正措施（JSON格式）")
    preventive_actions = Column(Text, comment="预防措施（JSON格式）")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否有效")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class QualityMetrics(Base):
    """质量指标表"""
    __tablename__ = "quality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_date = Column(DateTime, nullable=False, comment="统计日期")
    
    # 检查统计
    total_checks = Column(Integer, default=0, comment="总检查次数")
    pass_checks = Column(Integer, default=0, comment="通过检查次数")
    fail_checks = Column(Integer, default=0, comment="不通过检查次数")
    pass_rate = Column(Float, comment="通过率")
    
    # 产品统计
    total_products = Column(Integer, default=0, comment="总产品数量")
    qualified_products = Column(Integer, default=0, comment="合格产品数量")
    defective_products = Column(Integer, default=0, comment="不合格产品数量")
    qualification_rate = Column(Float, comment="合格率")
    
    # 缺陷统计
    total_defects = Column(Integer, default=0, comment="总缺陷数")
    critical_defects = Column(Integer, default=0, comment="严重缺陷数")
    major_defects = Column(Integer, default=0, comment="主要缺陷数")
    minor_defects = Column(Integer, default=0, comment="次要缺陷数")
    
    # 成本统计
    inspection_cost = Column(Float, comment="检验成本")
    rework_cost = Column(Float, comment="返工成本")
    scrap_cost = Column(Float, comment="报废成本")
    total_quality_cost = Column(Float, comment="总质量成本")
    
    # 时间统计
    avg_inspection_time = Column(Float, comment="平均检验时间（分钟）")
    avg_rework_time = Column(Float, comment="平均返工时间（分钟）")
    
    # 分类统计
    by_product_type = Column(Text, comment="按产品类型统计（JSON格式）")
    by_inspector = Column(Text, comment="按检验员统计（JSON格式）")
    by_defect_type = Column(Text, comment="按缺陷类型统计（JSON格式）")
    
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class QualityAlert(Base):
    """质量预警表"""
    __tablename__ = "quality_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    alert_level = Column(String(20), nullable=False, comment="预警级别")
    
    # 预警内容
    title = Column(String(200), nullable=False, comment="预警标题")
    description = Column(Text, comment="预警描述")
    trigger_condition = Column(Text, comment="触发条件")
    
    # 关联信息
    related_check_id = Column(Integer, ForeignKey("quality_checks.id"), comment="关联检查ID")
    related_product = Column(String(200), comment="关联产品")
    related_process = Column(String(100), comment="关联工序")
    
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
    related_check = relationship("QualityCheck")
    handler = relationship("User")