from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class MaterialCategory(str, enum.Enum):
    """物料类别枚举"""
    RAW_MATERIAL = "原材料"
    SEMI_FINISHED = "半成品"
    FINISHED_PRODUCT = "成品"
    STANDARD_PART = "标准件"
    CONSUMABLE = "消耗品"
    TOOL = "工具"

class MaterialStatus(str, enum.Enum):
    """物料状态枚举"""
    ACTIVE = "启用"
    NORMAL = "正常"
    WARNING = "预警"
    OUT_OF_STOCK = "缺货"
    OVERSTOCKED = "超储"
    DISCONTINUED = "停用"

class PurchaseStatus(str, enum.Enum):
    """采购状态枚举"""
    DRAFT = "草稿"
    SUBMITTED = "已提交"
    APPROVED = "已审批"
    ORDERED = "已下单"
    RECEIVED = "已收货"
    COMPLETED = "已完成"
    CANCELLED = "已取消"

class Material(Base):
    """物料模型"""
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), unique=True, index=True, nullable=False, comment="物料编码")
    material_name = Column(String(100), nullable=False, comment="物料名称")
    specification = Column(String(200), comment="规格型号")
    unit = Column(String(20), nullable=False, comment="计量单位")
    category = Column(Enum(MaterialCategory), nullable=False, comment="物料类别")
    
    # 库存信息
    current_stock = Column(Float, default=0, comment="当前库存")
    safety_stock = Column(Float, default=0, comment="安全库存")
    max_stock = Column(Float, comment="最大库存")
    location = Column(String(50), comment="存储位置")
    
    # 价格信息
    unit_price = Column(Float, comment="单价")
    last_purchase_price = Column(Float, comment="最近采购价")
    average_price = Column(Float, comment="平均价格")
    
    # 供应商信息
    primary_supplier = Column(String(100), comment="主要供应商")
    backup_suppliers = Column(Text, comment="备用供应商")
    
    # 技术信息
    technical_specs = Column(Text, comment="技术规格")
    quality_standards = Column(Text, comment="质量标准")
    storage_conditions = Column(Text, comment="存储条件")
    
    # 状态信息
    status = Column(Enum(MaterialStatus), default=MaterialStatus.NORMAL, comment="物料状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 统计信息
    total_in = Column(Float, default=0, comment="累计入库")
    total_out = Column(Float, default=0, comment="累计出库")
    turnover_rate = Column(Float, comment="周转率")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    def __repr__(self):
        return f"<Material(code='{self.material_code}', name='{self.material_name}', stock={self.current_stock})>"

class BOM(Base):
    """物料清单(BOM)模型"""
    __tablename__ = "bom"
    
    id = Column(Integer, primary_key=True, index=True)
    bom_code = Column(String(50), unique=True, index=True, nullable=False, comment="BOM编码")
    product_name = Column(String(100), nullable=False, comment="产品名称")
    product_model = Column(String(50), comment="产品型号")
    version = Column(String(20), nullable=False, comment="版本号")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否启用")
    effective_date = Column(DateTime, comment="生效日期")
    expiry_date = Column(DateTime, comment="失效日期")
    
    # 备注
    description = Column(Text, comment="描述")
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    def __repr__(self):
        return f"<BOM(code='{self.bom_code}', product='{self.product_name}', version='{self.version}')>"

class BOMItem(Base):
    """BOM明细模型"""
    __tablename__ = "bom_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联BOM
    bom_id = Column(Integer, ForeignKey("bom.id"), nullable=False, comment="BOM ID")
    
    # 关联物料
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, comment="物料ID")
    material_code = Column(String(50), nullable=False, comment="物料编码")
    material_name = Column(String(100), nullable=False, comment="物料名称")
    
    # 用量信息
    quantity = Column(Float, nullable=False, comment="用量")
    unit = Column(String(20), nullable=False, comment="单位")
    loss_rate = Column(Float, default=0, comment="损耗率(%)")
    
    # 层级信息
    level = Column(Integer, default=1, comment="层级")
    parent_item_id = Column(Integer, ForeignKey("bom_items.id"), comment="父级明细ID")
    
    # 替代信息
    is_substitute = Column(Boolean, default=False, comment="是否替代料")
    substitute_group = Column(String(50), comment="替代组")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    bom = relationship("BOM", backref="items")
    material = relationship("Material", backref="bom_items")
    parent_item = relationship("BOMItem", remote_side=[id], backref="sub_items")
    
    def __repr__(self):
        return f"<BOMItem(material='{self.material_name}', quantity={self.quantity}, level={self.level})>"

class PurchaseOrder(Base):
    """采购订单模型"""
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    po_no = Column(String(50), unique=True, index=True, nullable=False, comment="采购单号")
    
    # 供应商信息
    supplier_name = Column(String(100), nullable=False, comment="供应商名称")
    supplier_contact = Column(String(50), comment="联系人")
    supplier_phone = Column(String(20), comment="联系电话")
    supplier_address = Column(Text, comment="供应商地址")
    
    # 订单信息
    order_date = Column(DateTime, nullable=False, comment="下单日期")
    expected_date = Column(DateTime, nullable=False, comment="期望到货日期")
    actual_date = Column(DateTime, comment="实际到货日期")
    
    # 金额信息
    total_amount = Column(Float, comment="订单总金额")
    paid_amount = Column(Float, default=0, comment="已付金额")
    
    # 状态信息
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.DRAFT, comment="采购状态")
    
    # 审批信息
    applicant = Column(String(50), comment="申请人")
    approver = Column(String(50), comment="审批人")
    approval_date = Column(DateTime, comment="审批日期")
    approval_remark = Column(Text, comment="审批意见")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    def __repr__(self):
        return f"<PurchaseOrder(po_no='{self.po_no}', supplier='{self.supplier_name}', status='{self.status}')>"

class PurchaseOrderItem(Base):
    """采购订单明细模型"""
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联采购订单
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False, comment="采购订单ID")
    
    # 关联物料
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, comment="物料ID")
    material_code = Column(String(50), nullable=False, comment="物料编码")
    material_name = Column(String(100), nullable=False, comment="物料名称")
    specification = Column(String(200), comment="规格")
    
    # 数量和价格
    quantity = Column(Float, nullable=False, comment="采购数量")
    unit = Column(String(20), nullable=False, comment="单位")
    unit_price = Column(Float, nullable=False, comment="单价")
    total_price = Column(Float, nullable=False, comment="总价")
    
    # 收货信息
    received_quantity = Column(Float, default=0, comment="已收货数量")
    remaining_quantity = Column(Float, comment="剩余数量")
    
    # 质量信息
    quality_requirement = Column(Text, comment="质量要求")
    inspection_result = Column(String(50), comment="检验结果")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    purchase_order = relationship("PurchaseOrder", backref="items")
    material = relationship("Material", backref="purchase_items")
    
    def __repr__(self):
        return f"<PurchaseOrderItem(material='{self.material_name}', quantity={self.quantity}, price={self.unit_price})>"