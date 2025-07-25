from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import datetime, date
from decimal import Decimal
from app.models.order import OrderStatus, OrderPriority
from app.schemas.common import QueryParams

class OrderBase(BaseModel):
    """订单基础模型"""
    order_number: str
    customer_name: str
    customer_code: Optional[str] = None
    product_name: str
    product_model: Optional[str] = None
    product_spec: Optional[str] = None
    quantity: int
    unit: str = "件"
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: str = "CNY"
    order_date: date
    delivery_date: date
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    delivery_address: Optional[str] = None
    technical_requirements: Optional[str] = None
    quality_standards: Optional[str] = None
    remark: Optional[str] = None

class OrderCreate(OrderBase):
    """创建订单模型"""
    status: Optional[OrderStatus] = OrderStatus.PENDING
    priority: Optional[OrderPriority] = OrderPriority.MEDIUM
    
    @validator('order_number')
    def validate_order_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('订单号不能为空')
        return v.strip()
    
    @validator('customer_name')
    def validate_customer_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('客户名称不能为空')
        return v.strip()
    
    @validator('product_name')
    def validate_product_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('产品名称不能为空')
        return v.strip()
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('数量必须大于0')
        return v
    
    @validator('delivery_date')
    def validate_delivery_date(cls, v, values):
        if 'order_date' in values and v < values['order_date']:
            raise ValueError('交货日期不能早于订单日期')
        return v
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('单价不能为负数')
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('总金额不能为负数')
        return v

class OrderUpdate(BaseModel):
    """更新订单模型"""
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    product_name: Optional[str] = None
    product_model: Optional[str] = None
    product_spec: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    delivery_address: Optional[str] = None
    technical_requirements: Optional[str] = None
    quality_standards: Optional[str] = None
    remark: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('数量必须大于0')
        return v
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('单价不能为负数')
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('总金额不能为负数')
        return v

class OrderDetail(OrderBase):
    """订单详情模型"""
    id: int
    status: OrderStatus
    priority: OrderPriority
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderQuery(QueryParams):
    """订单查询参数"""
    keyword: Optional[str] = None  # 关键词搜索（订单号、客户名称、产品名称、产品型号）
    status: Optional[OrderStatus] = None
    priority: Optional[OrderPriority] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    order_date_start: Optional[date] = None
    order_date_end: Optional[date] = None
    delivery_date_start: Optional[date] = None
    delivery_date_end: Optional[date] = None
    urgent_only: Optional[bool] = False  # 只显示紧急订单
    overdue_only: Optional[bool] = False  # 只显示逾期订单

class OrderSummary(BaseModel):
    """订单摘要信息"""
    id: int
    order_number: str
    customer_name: str
    product_name: str
    quantity: int
    unit: str
    delivery_date: date
    status: OrderStatus
    priority: OrderPriority
    total_amount: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class OrderStats(BaseModel):
    """订单统计信息"""
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    in_production_orders: int
    completed_orders: int
    cancelled_orders: int
    urgent_orders: int
    overdue_orders: int
    monthly_new_orders: int
    monthly_completed_orders: int
    total_amount: float
    monthly_amount: float

class OrderStatusUpdate(BaseModel):
    """订单状态更新"""
    status: OrderStatus
    remark: Optional[str] = None

class OrderPriorityUpdate(BaseModel):
    """订单优先级更新"""
    priority: OrderPriority
    remark: Optional[str] = None

class OrderBatchOperation(BaseModel):
    """订单批量操作"""
    order_ids: List[int]
    operation: str  # 'confirm', 'start_production', 'complete', 'cancel'
    remark: Optional[str] = None

class OrderImport(BaseModel):
    """订单导入"""
    order_number: str
    customer_name: str
    customer_code: Optional[str] = None
    product_name: str
    product_model: Optional[str] = None
    product_spec: Optional[str] = None
    quantity: int
    unit: str = "件"
    unit_price: Optional[str] = None  # 字符串格式，便于Excel导入
    total_amount: Optional[str] = None  # 字符串格式，便于Excel导入
    currency: str = "CNY"
    order_date: str  # 字符串格式，便于Excel导入
    delivery_date: str  # 字符串格式，便于Excel导入
    priority: str = "MEDIUM"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    delivery_address: Optional[str] = None
    technical_requirements: Optional[str] = None
    quality_standards: Optional[str] = None
    remark: Optional[str] = None
    
    @validator('priority')
    def validate_priority(cls, v):
        try:
            OrderPriority(v)
        except ValueError:
            raise ValueError(f'无效的优先级: {v}')
        return v

class OrderExport(BaseModel):
    """订单导出"""
    id: int
    order_number: str
    customer_name: str
    customer_code: Optional[str] = None
    product_name: str
    product_model: Optional[str] = None
    product_spec: Optional[str] = None
    quantity: int
    unit: str
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: str
    order_date: date
    delivery_date: date
    status: str
    priority: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    delivery_address: Optional[str] = None
    technical_requirements: Optional[str] = None
    quality_standards: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class CustomerInfo(BaseModel):
    """客户信息"""
    name: str
    code: Optional[str] = None
    order_count: int
    total_amount: float
    last_order_date: Optional[date] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

class ProductInfo(BaseModel):
    """产品信息"""
    name: str
    model: Optional[str] = None
    spec: Optional[str] = None
    order_count: int
    total_quantity: int
    unit: str
    last_order_date: Optional[date] = None
    avg_unit_price: Optional[float] = None

class OrderTrend(BaseModel):
    """订单趋势数据"""
    date: date
    new_orders: int
    completed_orders: int
    total_amount: float
    avg_amount: float

class DeliveryAnalysis(BaseModel):
    """交期分析"""
    on_time_count: int  # 按时交货数量
    delayed_count: int  # 延期交货数量
    avg_delay_days: float  # 平均延期天数
    on_time_rate: float  # 按时交货率
    
class OrderDashboard(BaseModel):
    """订单仪表板数据"""
    stats: OrderStats
    recent_orders: List[OrderSummary]
    urgent_orders: List[OrderSummary]
    overdue_orders: List[OrderSummary]
    top_customers: List[CustomerInfo]
    top_products: List[ProductInfo]
    monthly_trend: List[OrderTrend]
    delivery_analysis: DeliveryAnalysis