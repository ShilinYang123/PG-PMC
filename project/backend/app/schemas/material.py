from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal
from app.models.material import MaterialCategory, MaterialStatus
from app.schemas.common import QueryParams

# 物料基础模型
class MaterialBase(BaseModel):
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    category: MaterialCategory = Field(..., description="物料分类")
    specification: Optional[str] = Field(None, description="规格型号")
    unit: str = Field(..., description="计量单位")
    unit_price: Decimal = Field(..., ge=0, description="单价")
    supplier: Optional[str] = Field(None, description="供应商")
    supplier_contact: Optional[str] = Field(None, description="供应商联系方式")
    lead_time: Optional[int] = Field(None, ge=0, description="采购周期(天)")
    warehouse: Optional[str] = Field(None, description="仓库")
    location: Optional[str] = Field(None, description="存放位置")
    remark: Optional[str] = Field(None, description="备注")

class MaterialCreate(MaterialBase):
    """创建物料"""
    current_stock: Optional[Decimal] = Field(default=0, ge=0, description="当前库存")
    min_stock: Optional[Decimal] = Field(default=0, ge=0, description="最小库存")
    max_stock: Optional[Decimal] = Field(None, ge=0, description="最大库存")
    safety_stock: Optional[Decimal] = Field(default=0, ge=0, description="安全库存")
    status: Optional[MaterialStatus] = Field(default=MaterialStatus.ACTIVE, description="状态")
    
    @validator('material_code')
    def validate_material_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('物料编码不能为空')
        if len(v) > 50:
            raise ValueError('物料编码长度不能超过50个字符')
        return v.strip().upper()
    
    @validator('material_name')
    def validate_material_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('物料名称不能为空')
        if len(v) > 200:
            raise ValueError('物料名称长度不能超过200个字符')
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('计量单位不能为空')
        if len(v) > 20:
            raise ValueError('计量单位长度不能超过20个字符')
        return v.strip()
    
    @validator('max_stock')
    def validate_max_stock(cls, v, values):
        if v is not None and 'min_stock' in values and values['min_stock'] is not None:
            if v <= values['min_stock']:
                raise ValueError('最大库存必须大于最小库存')
        return v

class MaterialUpdate(BaseModel):
    """更新物料"""
    material_name: Optional[str] = Field(None, description="物料名称")
    category: Optional[MaterialCategory] = Field(None, description="物料分类")
    specification: Optional[str] = Field(None, description="规格型号")
    unit: Optional[str] = Field(None, description="计量单位")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="单价")
    current_stock: Optional[Decimal] = Field(None, ge=0, description="当前库存")
    min_stock: Optional[Decimal] = Field(None, ge=0, description="最小库存")
    max_stock: Optional[Decimal] = Field(None, ge=0, description="最大库存")
    safety_stock: Optional[Decimal] = Field(None, ge=0, description="安全库存")
    supplier: Optional[str] = Field(None, description="供应商")
    supplier_contact: Optional[str] = Field(None, description="供应商联系方式")
    lead_time: Optional[int] = Field(None, ge=0, description="采购周期(天)")
    warehouse: Optional[str] = Field(None, description="仓库")
    location: Optional[str] = Field(None, description="存放位置")
    status: Optional[MaterialStatus] = Field(None, description="状态")
    last_purchase_date: Optional[date] = Field(None, description="最后采购日期")
    last_purchase_price: Optional[Decimal] = Field(None, ge=0, description="最后采购价格")
    last_usage_date: Optional[date] = Field(None, description="最后使用日期")
    remark: Optional[str] = Field(None, description="备注")

class MaterialDetail(MaterialBase):
    """物料详情"""
    id: int = Field(..., description="物料ID")
    current_stock: Decimal = Field(..., description="当前库存")
    min_stock: Decimal = Field(..., description="最小库存")
    max_stock: Optional[Decimal] = Field(None, description="最大库存")
    safety_stock: Decimal = Field(..., description="安全库存")
    stock_status: str = Field(..., description="库存状态")
    status: MaterialStatus = Field(..., description="状态")
    last_purchase_date: Optional[date] = Field(None, description="最后采购日期")
    last_purchase_price: Optional[Decimal] = Field(None, description="最后采购价格")
    last_usage_date: Optional[date] = Field(None, description="最后使用日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

class MaterialQuery(QueryParams):
    """物料查询参数"""
    category: Optional[MaterialCategory] = Field(None, description="物料分类")
    status: Optional[MaterialStatus] = Field(None, description="状态")
    supplier: Optional[str] = Field(None, description="供应商")
    warehouse: Optional[str] = Field(None, description="仓库")
    low_stock_only: Optional[bool] = Field(False, description="仅显示库存不足")
    out_of_stock_only: Optional[bool] = Field(False, description="仅显示缺货")
    price_min: Optional[Decimal] = Field(None, ge=0, description="最低价格")
    price_max: Optional[Decimal] = Field(None, ge=0, description="最高价格")

class MaterialSummary(BaseModel):
    """物料摘要"""
    id: int = Field(..., description="物料ID")
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    category: MaterialCategory = Field(..., description="物料分类")
    unit: str = Field(..., description="计量单位")
    unit_price: Decimal = Field(..., description="单价")
    current_stock: Decimal = Field(..., description="当前库存")
    min_stock: Decimal = Field(..., description="最小库存")
    stock_status: str = Field(..., description="库存状态")
    supplier: Optional[str] = Field(None, description="供应商")
    status: MaterialStatus = Field(..., description="状态")
    
    class Config:
        from_attributes = True

class MaterialStats(BaseModel):
    """物料统计"""
    total_materials: int = Field(..., description="总物料数")
    active_materials: int = Field(..., description="活跃物料数")
    inactive_materials: int = Field(..., description="非活跃物料数")
    discontinued_materials: int = Field(..., description="停用物料数")
    raw_materials: int = Field(..., description="原材料数")
    semi_finished: int = Field(..., description="半成品数")
    finished_products: int = Field(..., description="成品数")
    consumables: int = Field(..., description="耗材数")
    tools: int = Field(..., description="工具数")
    low_stock_materials: int = Field(..., description="库存不足物料数")
    out_of_stock_materials: int = Field(..., description="缺货物料数")
    overstock_materials: int = Field(..., description="库存过多物料数")
    total_stock_value: float = Field(..., description="总库存价值")
    monthly_new_materials: int = Field(..., description="本月新增物料数")

class MaterialStockAlert(BaseModel):
    """物料库存预警"""
    material_id: int = Field(..., description="物料ID")
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    current_stock: Decimal = Field(..., description="当前库存")
    min_stock: Decimal = Field(..., description="最小库存")
    max_stock: Optional[Decimal] = Field(None, description="最大库存")
    alert_type: str = Field(..., description="预警类型")
    alert_level: str = Field(..., description="预警级别")
    supplier: Optional[str] = Field(None, description="供应商")
    lead_time: Optional[int] = Field(None, description="采购周期")

class MaterialStatusUpdate(BaseModel):
    """物料状态更新"""
    status: MaterialStatus = Field(..., description="新状态")
    remark: Optional[str] = Field(None, description="备注")

class MaterialStockUpdate(BaseModel):
    """物料库存更新"""
    stock_change: Decimal = Field(..., description="库存变化量")
    change_type: str = Field(..., description="变化类型")
    reference_number: Optional[str] = Field(None, description="参考单号")
    remark: Optional[str] = Field(None, description="备注")
    
    @validator('change_type')
    def validate_change_type(cls, v):
        allowed_types = ['入库', '出库', '调拨', '盘点', '报废', '退货']
        if v not in allowed_types:
            raise ValueError(f'变化类型必须是以下之一: {", ".join(allowed_types)}')
        return v

class MaterialBatchOperation(BaseModel):
    """物料批量操作"""
    material_ids: List[int] = Field(..., description="物料ID列表")
    operation: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")

class MaterialImport(BaseModel):
    """物料导入"""
    file_url: str = Field(..., description="文件URL")
    file_type: str = Field(..., description="文件类型")
    mapping: Dict[str, str] = Field(..., description="字段映射")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")

class MaterialExport(BaseModel):
    """物料导出"""
    material_ids: Optional[List[int]] = Field(None, description="物料ID列表")
    query: Optional[MaterialQuery] = Field(None, description="查询条件")
    fields: List[str] = Field(..., description="导出字段")
    file_type: str = Field(..., description="文件类型")
    options: Optional[Dict[str, Any]] = Field(None, description="导出选项")

# 库存操作模型
class MaterialStockIn(BaseModel):
    """物料入库"""
    quantity: Decimal = Field(..., gt=0, description="入库数量")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="入库单价")
    supplier: Optional[str] = Field(None, description="供应商")
    warehouse: Optional[str] = Field(None, description="仓库")
    location: Optional[str] = Field(None, description="存放位置")
    reference_number: Optional[str] = Field(None, description="参考单号")
    remark: Optional[str] = Field(None, description="备注")

class MaterialStockOut(BaseModel):
    """物料出库"""
    quantity: Decimal = Field(..., gt=0, description="出库数量")
    purpose: Optional[str] = Field(None, description="出库用途")
    department: Optional[str] = Field(None, description="领用部门")
    recipient: Optional[str] = Field(None, description="领用人")
    reference_number: Optional[str] = Field(None, description="参考单号")
    remark: Optional[str] = Field(None, description="备注")

class MaterialStockTransfer(BaseModel):
    """物料调拨"""
    from_material_id: int = Field(..., description="源物料ID")
    to_material_id: int = Field(..., description="目标物料ID")
    quantity: Decimal = Field(..., gt=0, description="调拨数量")
    from_warehouse: Optional[str] = Field(None, description="源仓库")
    to_warehouse: Optional[str] = Field(None, description="目标仓库")
    reference_number: Optional[str] = Field(None, description="参考单号")
    remark: Optional[str] = Field(None, description="备注")

class MaterialStockCheck(BaseModel):
    """物料盘点"""
    actual_quantity: Decimal = Field(..., ge=0, description="实际盘点数量")
    check_date: Optional[date] = Field(None, description="盘点日期")
    checker: Optional[str] = Field(None, description="盘点人")
    warehouse: Optional[str] = Field(None, description="盘点仓库")
    location: Optional[str] = Field(None, description="盘点位置")
    remark: Optional[str] = Field(None, description="备注")

# 供应商信息
class SupplierInfo(BaseModel):
    """供应商信息"""
    name: str = Field(..., description="供应商名称")
    code: str = Field(..., description="供应商编码")
    contact_person: Optional[str] = Field(None, description="联系人")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")
    credit_rating: Optional[str] = Field(None, description="信用等级")
    payment_terms: Optional[str] = Field(None, description="付款条件")
    delivery_terms: Optional[str] = Field(None, description="交货条件")
    status: str = Field(..., description="状态")

# 仓库信息
class WarehouseInfo(BaseModel):
    """仓库信息"""
    name: str = Field(..., description="仓库名称")
    code: str = Field(..., description="仓库编码")
    type: str = Field(..., description="仓库类型")
    manager: Optional[str] = Field(None, description="仓库管理员")
    location: Optional[str] = Field(None, description="位置")
    capacity: Optional[Decimal] = Field(None, description="容量")
    current_usage: Optional[Decimal] = Field(None, description="当前使用量")
    status: str = Field(..., description="状态")

# 库存变动记录
class StockMovement(BaseModel):
    """库存变动记录"""
    id: int = Field(..., description="记录ID")
    material_id: int = Field(..., description="物料ID")
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    movement_type: str = Field(..., description="变动类型")
    quantity: Decimal = Field(..., description="变动数量")
    unit_price: Optional[Decimal] = Field(None, description="单价")
    total_amount: Optional[Decimal] = Field(None, description="总金额")
    before_stock: Decimal = Field(..., description="变动前库存")
    after_stock: Decimal = Field(..., description="变动后库存")
    reference_number: Optional[str] = Field(None, description="参考单号")
    warehouse: Optional[str] = Field(None, description="仓库")
    location: Optional[str] = Field(None, description="位置")
    operator: Optional[str] = Field(None, description="操作员")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True

# 物料价格历史
class MaterialPriceHistory(BaseModel):
    """物料价格历史"""
    id: int = Field(..., description="记录ID")
    material_id: int = Field(..., description="物料ID")
    price: Decimal = Field(..., description="价格")
    supplier: Optional[str] = Field(None, description="供应商")
    effective_date: date = Field(..., description="生效日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    purchase_quantity: Optional[Decimal] = Field(None, description="采购数量")
    currency: str = Field(default="CNY", description="货币")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[str] = Field(None, description="创建人")
    
    class Config:
        from_attributes = True

# 物料需求计划
class MaterialRequirement(BaseModel):
    """物料需求计划"""
    material_id: int = Field(..., description="物料ID")
    material_code: str = Field(..., description="物料编码")
    material_name: str = Field(..., description="物料名称")
    required_quantity: Decimal = Field(..., description="需求数量")
    current_stock: Decimal = Field(..., description="当前库存")
    shortage_quantity: Decimal = Field(..., description="缺口数量")
    required_date: date = Field(..., description="需求日期")
    priority: str = Field(..., description="优先级")
    source: str = Field(..., description="需求来源")
    source_id: Optional[int] = Field(None, description="来源ID")
    status: str = Field(..., description="状态")

# 物料仪表板
class MaterialDashboard(BaseModel):
    """物料仪表板"""
    stats: MaterialStats = Field(..., description="统计信息")
    alerts: List[MaterialStockAlert] = Field(..., description="库存预警")
    recent_movements: List[StockMovement] = Field(..., description="最近库存变动")
    price_trends: List[MaterialPriceHistory] = Field(..., description="价格趋势")
    requirements: List[MaterialRequirement] = Field(..., description="物料需求")
    suppliers: List[SupplierInfo] = Field(..., description="供应商信息")
    warehouses: List[WarehouseInfo] = Field(..., description="仓库信息")