from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum
from app.models.equipment import EquipmentStatus, MaintenanceType

# 设备基础模型
class EquipmentBase(BaseModel):
    equipment_code: str = Field(..., description="设备编号")
    equipment_name: str = Field(..., description="设备名称")
    category: Optional[str] = Field(None, description="设备类别")
    model: Optional[str] = Field(None, description="设备型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    purchase_date: Optional[date] = Field(None, description="采购日期")
    purchase_price: Optional[float] = Field(None, ge=0, description="采购价格")
    warranty_expiry: Optional[date] = Field(None, description="保修到期日期")
    status: Optional[EquipmentStatus] = Field(EquipmentStatus.NORMAL, description="设备状态")
    workshop: Optional[str] = Field(None, description="所属车间")
    location: Optional[str] = Field(None, description="设备位置")
    responsible_person: Optional[str] = Field(None, description="负责人")
    specifications: Optional[str] = Field(None, description="技术规格")
    operating_parameters: Optional[str] = Field(None, description="操作参数")
    maintenance_cycle: Optional[int] = Field(None, ge=1, description="维护周期（天）")
    description: Optional[str] = Field(None, description="设备描述")
    remark: Optional[str] = Field(None, description="备注")

    @validator('warranty_expiry')
    def validate_warranty_expiry(cls, v, values):
        if v and 'purchase_date' in values and values['purchase_date']:
            if v < values['purchase_date']:
                raise ValueError('保修到期日期不能早于采购日期')
        return v

    @validator('equipment_code')
    def validate_equipment_code(cls, v):
        if not v or not v.strip():
            raise ValueError('设备编号不能为空')
        if len(v.strip()) > 50:
            raise ValueError('设备编号长度不能超过50个字符')
        return v.strip()

    @validator('equipment_name')
    def validate_equipment_name(cls, v):
        if not v or not v.strip():
            raise ValueError('设备名称不能为空')
        if len(v.strip()) > 100:
            raise ValueError('设备名称长度不能超过100个字符')
        return v.strip()

# 创建设备模型
class EquipmentCreate(EquipmentBase):
    pass

# 更新设备模型
class EquipmentUpdate(BaseModel):
    equipment_code: Optional[str] = Field(None, description="设备编号")
    equipment_name: Optional[str] = Field(None, description="设备名称")
    category: Optional[str] = Field(None, description="设备类别")
    model: Optional[str] = Field(None, description="设备型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    purchase_date: Optional[date] = Field(None, description="采购日期")
    purchase_price: Optional[float] = Field(None, ge=0, description="采购价格")
    warranty_expiry: Optional[date] = Field(None, description="保修到期日期")
    status: Optional[EquipmentStatus] = Field(None, description="设备状态")
    workshop: Optional[str] = Field(None, description="所属车间")
    location: Optional[str] = Field(None, description="设备位置")
    responsible_person: Optional[str] = Field(None, description="负责人")
    specifications: Optional[str] = Field(None, description="技术规格")
    operating_parameters: Optional[str] = Field(None, description="操作参数")
    maintenance_cycle: Optional[int] = Field(None, ge=1, description="维护周期（天）")
    total_runtime: Optional[float] = Field(None, ge=0, description="总运行时间（小时）")
    description: Optional[str] = Field(None, description="设备描述")
    remark: Optional[str] = Field(None, description="备注")

    @validator('equipment_code')
    def validate_equipment_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('设备编号不能为空')
            if len(v.strip()) > 50:
                raise ValueError('设备编号长度不能超过50个字符')
            return v.strip()
        return v

    @validator('equipment_name')
    def validate_equipment_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('设备名称不能为空')
            if len(v.strip()) > 100:
                raise ValueError('设备名称长度不能超过100个字符')
            return v.strip()
        return v

# 维护记录基础模型
class MaintenanceRecordBase(BaseModel):
    maintenance_type: MaintenanceType = Field(..., description="维护类型")
    maintenance_date: date = Field(..., description="维护日期")
    maintenance_person: str = Field(..., description="维护人员")
    maintenance_content: str = Field(..., description="维护内容")
    parts_replaced: Optional[str] = Field(None, description="更换部件")
    cost: Optional[float] = Field(None, ge=0, description="维护费用")
    duration_hours: Optional[float] = Field(None, ge=0, description="维护时长（小时）")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    status: Optional[str] = Field("completed", description="维护状态")
    remark: Optional[str] = Field(None, description="备注")

    @validator('maintenance_date')
    def validate_maintenance_date(cls, v):
        if v > date.today():
            raise ValueError('维护日期不能是未来日期')
        return v

    @validator('next_maintenance_date')
    def validate_next_maintenance_date(cls, v, values):
        if v and 'maintenance_date' in values:
            if v <= values['maintenance_date']:
                raise ValueError('下次维护日期必须晚于当前维护日期')
        return v

    @validator('maintenance_person')
    def validate_maintenance_person(cls, v):
        if not v or not v.strip():
            raise ValueError('维护人员不能为空')
        return v.strip()

    @validator('maintenance_content')
    def validate_maintenance_content(cls, v):
        if not v or not v.strip():
            raise ValueError('维护内容不能为空')
        return v.strip()

# 创建维护记录模型
class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass

# 更新维护记录模型
class MaintenanceRecordUpdate(BaseModel):
    maintenance_type: Optional[MaintenanceType] = Field(None, description="维护类型")
    maintenance_date: Optional[date] = Field(None, description="维护日期")
    maintenance_person: Optional[str] = Field(None, description="维护人员")
    maintenance_content: Optional[str] = Field(None, description="维护内容")
    parts_replaced: Optional[str] = Field(None, description="更换部件")
    cost: Optional[float] = Field(None, ge=0, description="维护费用")
    duration_hours: Optional[float] = Field(None, ge=0, description="维护时长（小时）")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    status: Optional[str] = Field(None, description="维护状态")
    remark: Optional[str] = Field(None, description="备注")

# 维护记录详情模型
class MaintenanceRecordDetail(MaintenanceRecordBase):
    id: int = Field(..., description="维护记录ID")
    equipment_id: int = Field(..., description="设备ID")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[str] = Field(None, description="创建人")

    class Config:
        from_attributes = True

# 设备查询模型
class EquipmentQuery(BaseModel):
    keyword: Optional[str] = Field(None, description="关键词搜索")
    status: Optional[EquipmentStatus] = Field(None, description="设备状态")
    category: Optional[str] = Field(None, description="设备类别")
    workshop: Optional[str] = Field(None, description="所属车间")
    responsible_person: Optional[str] = Field(None, description="负责人")
    manufacturer: Optional[str] = Field(None, description="制造商")
    purchase_date_start: Optional[date] = Field(None, description="采购开始日期")
    purchase_date_end: Optional[date] = Field(None, description="采购结束日期")
    warranty_expiry_start: Optional[date] = Field(None, description="保修到期开始日期")
    warranty_expiry_end: Optional[date] = Field(None, description="保修到期结束日期")
    price_min: Optional[float] = Field(None, ge=0, description="最低价格")
    price_max: Optional[float] = Field(None, ge=0, description="最高价格")
    maintenance_due: Optional[int] = Field(None, ge=0, description="维护到期天数")
    warranty_expiring: Optional[int] = Field(None, ge=0, description="保修到期天数")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")

# 设备详情模型
class EquipmentDetail(EquipmentBase):
    id: int = Field(..., description="设备ID")
    last_maintenance_date: Optional[date] = Field(None, description="上次维护日期")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    total_runtime: Optional[float] = Field(None, description="总运行时间（小时）")
    usage_years: Optional[float] = Field(None, description="使用年限")
    maintenance_status: Optional[str] = Field(None, description="维护状态")
    warranty_status: Optional[str] = Field(None, description="保修状态")
    total_maintenance_count: Optional[int] = Field(None, description="总维护次数")
    recent_maintenance_count: Optional[int] = Field(None, description="近期维护次数")
    maintenance_records: Optional[List[MaintenanceRecordDetail]] = Field(None, description="维护记录")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")

    class Config:
        from_attributes = True

# 设备摘要模型
class EquipmentSummary(BaseModel):
    id: int = Field(..., description="设备ID")
    equipment_code: str = Field(..., description="设备编号")
    equipment_name: str = Field(..., description="设备名称")
    category: Optional[str] = Field(None, description="设备类别")
    status: EquipmentStatus = Field(..., description="设备状态")
    workshop: Optional[str] = Field(None, description="所属车间")
    responsible_person: Optional[str] = Field(None, description="负责人")
    next_maintenance_date: Optional[date] = Field(None, description="下次维护日期")
    days_to_maintenance: Optional[int] = Field(None, description="距离维护天数")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

# 设备统计模型
class EquipmentStats(BaseModel):
    total_equipment: int = Field(..., description="总设备数")
    normal_equipment: int = Field(..., description="正常设备数")
    running_equipment: int = Field(..., description="运行设备数")
    maintenance_equipment: int = Field(..., description="维护设备数")
    fault_equipment: int = Field(..., description="故障设备数")
    retired_equipment: int = Field(..., description="报废设备数")
    maintenance_due_equipment: int = Field(..., description="需要维护设备数")
    warranty_expiring_equipment: int = Field(..., description="保修即将到期设备数")
    total_equipment_value: float = Field(..., description="设备总价值")
    utilization_rate: float = Field(..., description="设备利用率")
    monthly_new_equipment: int = Field(..., description="本月新增设备")
    monthly_maintenance_records: int = Field(..., description="本月维护记录")
    monthly_maintenance_cost: float = Field(..., description="本月维护费用")

# 设备状态更新模型
class EquipmentStatusUpdate(BaseModel):
    status: EquipmentStatus = Field(..., description="设备状态")
    remark: Optional[str] = Field(None, description="备注")

# 批量操作模型
class EquipmentBatchOperation(BaseModel):
    equipment_ids: List[int] = Field(..., description="设备ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")

# 设备导入模型
class EquipmentImport(BaseModel):
    file_url: str = Field(..., description="文件URL")
    file_type: str = Field(..., description="文件类型")
    mapping: Dict[str, str] = Field(..., description="字段映射")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")

# 设备导出模型
class EquipmentExport(BaseModel):
    equipment_ids: Optional[List[int]] = Field(None, description="设备ID列表")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    format: str = Field("excel", description="导出格式")

# 车间信息模型
class WorkshopInfo(BaseModel):
    workshop_name: str = Field(..., description="车间名称")
    equipment_count: int = Field(..., description="设备数量")
    running_count: int = Field(..., description="运行设备数")
    fault_count: int = Field(..., description="故障设备数")
    utilization_rate: float = Field(..., description="利用率")

# 设备类别信息模型
class CategoryInfo(BaseModel):
    category_name: str = Field(..., description="类别名称")
    equipment_count: int = Field(..., description="设备数量")
    total_value: float = Field(..., description="总价值")
    average_age: float = Field(..., description="平均使用年限")

# 维护趋势模型
class MaintenanceTrend(BaseModel):
    date: date = Field(..., description="日期")
    maintenance_count: int = Field(..., description="维护次数")
    maintenance_cost: float = Field(..., description="维护费用")
    preventive_count: int = Field(..., description="预防性维护次数")
    corrective_count: int = Field(..., description="纠正性维护次数")

# 设备效率分析模型
class EquipmentEfficiencyAnalysis(BaseModel):
    equipment_id: int = Field(..., description="设备ID")
    equipment_name: str = Field(..., description="设备名称")
    total_runtime: float = Field(..., description="总运行时间")
    planned_runtime: float = Field(..., description="计划运行时间")
    efficiency_rate: float = Field(..., description="效率率")
    downtime_hours: float = Field(..., description="停机时间")
    maintenance_hours: float = Field(..., description="维护时间")
    fault_hours: float = Field(..., description="故障时间")

# 设备仪表板模型
class EquipmentDashboard(BaseModel):
    overview_stats: EquipmentStats = Field(..., description="概览统计")
    workshop_distribution: List[WorkshopInfo] = Field(..., description="车间分布")
    category_distribution: List[CategoryInfo] = Field(..., description="类别分布")
    maintenance_trends: List[MaintenanceTrend] = Field(..., description="维护趋势")
    efficiency_analysis: List[EquipmentEfficiencyAnalysis] = Field(..., description="效率分析")
    maintenance_alerts: List[EquipmentSummary] = Field(..., description="维护提醒")
    warranty_alerts: List[EquipmentSummary] = Field(..., description="保修提醒")

# 设备报告模型
class EquipmentReport(BaseModel):
    report_id: str = Field(..., description="报告ID")
    report_name: str = Field(..., description="报告名称")
    report_type: str = Field(..., description="报告类型")
    date_range: Dict[str, date] = Field(..., description="日期范围")
    equipment_filters: Optional[Dict[str, Any]] = Field(None, description="设备过滤条件")
    data: Dict[str, Any] = Field(..., description="报告数据")
    generated_at: datetime = Field(..., description="生成时间")
    generated_by: str = Field(..., description="生成人")

# 设备配置模型
class EquipmentConfig(BaseModel):
    config_id: str = Field(..., description="配置ID")
    config_name: str = Field(..., description="配置名称")
    config_type: str = Field(..., description="配置类型")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    is_active: bool = Field(True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

# 设备模板模型
class EquipmentTemplate(BaseModel):
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    category: str = Field(..., description="设备类别")
    default_values: Dict[str, Any] = Field(..., description="默认值")
    required_fields: List[str] = Field(..., description="必填字段")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    description: Optional[str] = Field(None, description="模板描述")
    is_active: bool = Field(True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    created_by: str = Field(..., description="创建人")

# 设备预警模型
class EquipmentAlert(BaseModel):
    alert_id: str = Field(..., description="预警ID")
    equipment_id: int = Field(..., description="设备ID")
    alert_type: str = Field(..., description="预警类型")
    alert_level: str = Field(..., description="预警级别")
    alert_message: str = Field(..., description="预警消息")
    alert_data: Optional[Dict[str, Any]] = Field(None, description="预警数据")
    is_resolved: bool = Field(False, description="是否已解决")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    resolved_by: Optional[str] = Field(None, description="解决人")
    created_at: datetime = Field(..., description="创建时间")

# 设备性能指标模型
class EquipmentPerformanceMetrics(BaseModel):
    equipment_id: int = Field(..., description="设备ID")
    metric_date: date = Field(..., description="指标日期")
    runtime_hours: float = Field(..., description="运行时间")
    output_quantity: Optional[float] = Field(None, description="产出数量")
    energy_consumption: Optional[float] = Field(None, description="能耗")
    efficiency_rate: Optional[float] = Field(None, description="效率率")
    quality_rate: Optional[float] = Field(None, description="质量率")
    availability_rate: Optional[float] = Field(None, description="可用率")
    oee_score: Optional[float] = Field(None, description="OEE得分")
    recorded_at: datetime = Field(..., description="记录时间")
    recorded_by: str = Field(..., description="记录人")