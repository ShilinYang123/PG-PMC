from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    PENDING = "待处理"
    CONFIRMED = "已确认"
    IN_PRODUCTION = "生产中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"

class OrderPriority(str, enum.Enum):
    """订单优先级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"

class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False, comment="订单编号")
    customer_name = Column(String(100), nullable=False, comment="客户名称")
    product_name = Column(String(100), nullable=False, comment="产品名称")
    product_model = Column(String(50), comment="产品型号")
    quantity = Column(Integer, nullable=False, comment="数量")
    unit = Column(String(20), nullable=False, comment="单位")
    unit_price = Column(Float, comment="单价")
    total_amount = Column(Float, comment="总金额")
    
    # 日期字段
    order_date = Column(DateTime, nullable=False, comment="下单日期")
    delivery_date = Column(DateTime, nullable=False, comment="交货日期")
    
    # 状态和优先级
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, comment="订单状态")
    priority = Column(Enum(OrderPriority), default=OrderPriority.MEDIUM, comment="优先级")
    
    # 联系信息
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    
    # 地址信息
    delivery_address = Column(Text, comment="交货地址")
    
    # 技术要求
    technical_requirements = Column(Text, comment="技术要求")
    quality_standards = Column(Text, comment="质量标准")
    
    # 备注
    remark = Column(Text, comment="备注")
    
    # 系统字段
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_by = Column(String(50), comment="创建人")
    updated_by = Column(String(50), comment="更新人")
    
    def __repr__(self):
        return f"<Order(order_no='{self.order_no}', customer='{self.customer_name}', product='{self.product_name}')>"