from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal
from app.models.production_plan import PlanStatus, PlanPriority, StageStatus
from app.schemas.common import QueryParams

# 生产阶段基础模型
class ProductionStageBase(BaseModel):
    stage_number: str = Field(..., description="阶段编号")
    stage_name: str = Field(..., description="阶段名称")
    stage_sequence: int = Field(..., description="阶段顺序")
    description: Optional[str] = Field(None, description="阶段描述")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    workshop: Optional[str] = Field(None, description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    responsible_person: Optional[str] = Field(None, description="负责人")
    team_members: Optional[str] = Field(None, description="团队成员")
    quality_checkpoints: Optional[str] = Field(None, description="质量检查点")
    remark: Optional[str] = Field(None, description="备注")

class ProductionStageCreate(ProductionStageBase):
    """创建生产阶段"""
    pass

class ProductionStageUpdate(BaseModel):
    """更新生产阶段"""
    stage_name: Optional[str] = Field(None, description="阶段名称")
    description: Optional[str] = Field(None, description="阶段描述")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    stage_status: Optional[StageStatus] = Field(None, description="阶段状态")
    progress: Optional[Decimal] = Field(None, ge=0, le=100, description="进度百分比")
    workshop: Optional[str] = Field(None, description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    responsible_person: Optional[str] = Field(None, description="负责人")
    team_members: Optional[str] = Field(None, description="团队成员")
    quality_checkpoints: Optional[str] = Field(None, description="质量检查点")
    remark: Optional[str] = Field(None, description="备注")

class ProductionStageDetail(ProductionStageBase):
    """生产阶段详情"""
    id: int = Field(..., description="阶段ID")
    plan_id: int = Field(..., description="计划ID")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    stage_status: StageStatus = Field(default=StageStatus.PENDING, description="阶段状态")
    progress: Decimal = Field(default=0, description="进度百分比")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

# 生产计划基础模型
class ProductionPlanBase(BaseModel):
    plan_number: str = Field(..., description="计划编号")
    plan_name: str = Field(..., description="计划名称")
    order_id: Optional[int] = Field(None, description="关联订单ID")
    product_name: str = Field(..., description="产品名称")
    product_model: Optional[str] = Field(None, description="产品型号")
    product_spec: Optional[str] = Field(None, description="产品规格")
    planned_quantity: Decimal = Field(..., gt=0, description="计划数量")
    unit: str = Field(..., description="单位")
    planned_start_date: date = Field(..., description="计划开始日期")
    planned_end_date: date = Field(..., description="计划结束日期")
    workshop: Optional[str] = Field(None, description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    responsible_person: Optional[str] = Field(None, description="负责人")
    team_members: Optional[str] = Field(None, description="团队成员")
    process_flow: Optional[str] = Field(None, description="工艺流程")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="预估成本")
    remark: Optional[str] = Field(None, description="备注")
    
    @validator('planned_end_date')
    def validate_end_date(cls, v, values):
        if 'planned_start_date' in values and v <= values['planned_start_date']:
            raise ValueError('计划结束日期必须晚于开始日期')
        return v

class ProductionPlanCreate(ProductionPlanBase):
    """创建生产计划"""
    status: Optional[PlanStatus] = Field(default=PlanStatus.DRAFT, description="计划状态")
    priority: Optional[PlanPriority] = Field(default=PlanPriority.MEDIUM, description="优先级")
    stages: Optional[List[ProductionStageCreate]] = Field(default=[], description="生产阶段")
    
    @validator('plan_number')
    def validate_plan_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('计划编号不能为空')
        if len(v) > 50:
            raise ValueError('计划编号长度不能超过50个字符')
        return v.strip()
    
    @validator('plan_name')
    def validate_plan_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('计划名称不能为空')
        if len(v) > 200:
            raise ValueError('计划名称长度不能超过200个字符')
        return v.strip()
    
    @validator('product_name')
    def validate_product_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('产品名称不能为空')
        if len(v) > 200:
            raise ValueError('产品名称长度不能超过200个字符')
        return v.strip()

class ProductionPlanUpdate(BaseModel):
    """更新生产计划"""
    plan_name: Optional[str] = Field(None, description="计划名称")
    product_name: Optional[str] = Field(None, description="产品名称")
    product_model: Optional[str] = Field(None, description="产品型号")
    product_spec: Optional[str] = Field(None, description="产品规格")
    planned_quantity: Optional[Decimal] = Field(None, gt=0, description="计划数量")
    actual_quantity: Optional[Decimal] = Field(None, ge=0, description="实际数量")
    unit: Optional[str] = Field(None, description="单位")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    status: Optional[PlanStatus] = Field(None, description="计划状态")
    priority: Optional[PlanPriority] = Field(None, description="优先级")
    progress: Optional[Decimal] = Field(None, ge=0, le=100, description="进度百分比")
    workshop: Optional[str] = Field(None, description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    responsible_person: Optional[str] = Field(None, description="负责人")
    team_members: Optional[str] = Field(None, description="团队成员")
    process_flow: Optional[str] = Field(None, description="工艺流程")
    estimated_cost: Optional[Decimal] = Field(None, ge=0, description="预估成本")
    actual_cost: Optional[Decimal] = Field(None, ge=0, description="实际成本")
    remark: Optional[str] = Field(None, description="备注")

class ProductionPlanDetail(ProductionPlanBase):
    """生产计划详情"""
    id: int = Field(..., description="计划ID")
    order_number: Optional[str] = Field(None, description="订单编号")
    actual_quantity: Optional[Decimal] = Field(None, description="实际数量")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    status: PlanStatus = Field(..., description="计划状态")
    priority: PlanPriority = Field(..., description="优先级")
    progress: Decimal = Field(default=0, description="进度百分比")
    actual_cost: Optional[Decimal] = Field(None, description="实际成本")
    stages: Optional[List[ProductionStageDetail]] = Field(default=[], description="生产阶段")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

class ProductionPlanQuery(QueryParams):
    """生产计划查询参数"""
    status: Optional[PlanStatus] = Field(None, description="计划状态")
    priority: Optional[PlanPriority] = Field(None, description="优先级")
    workshop: Optional[str] = Field(None, description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    responsible_person: Optional[str] = Field(None, description="负责人")
    planned_start_date_start: Optional[date] = Field(None, description="计划开始日期-开始")
    planned_start_date_end: Optional[date] = Field(None, description="计划开始日期-结束")
    planned_end_date_start: Optional[date] = Field(None, description="计划结束日期-开始")
    planned_end_date_end: Optional[date] = Field(None, description="计划结束日期-结束")
    order_id: Optional[int] = Field(None, description="关联订单ID")

class ProductionPlanSummary(BaseModel):
    """生产计划摘要"""
    id: int = Field(..., description="计划ID")
    plan_number: str = Field(..., description="计划编号")
    plan_name: str = Field(..., description="计划名称")
    product_name: str = Field(..., description="产品名称")
    planned_quantity: Decimal = Field(..., description="计划数量")
    unit: str = Field(..., description="单位")
    planned_start_date: date = Field(..., description="计划开始日期")
    planned_end_date: date = Field(..., description="计划结束日期")
    status: PlanStatus = Field(..., description="计划状态")
    priority: PlanPriority = Field(..., description="优先级")
    progress: Decimal = Field(..., description="进度百分比")
    responsible_person: Optional[str] = Field(None, description="负责人")
    
    class Config:
        from_attributes = True

class ProductionPlanStats(BaseModel):
    """生产计划统计"""
    total_plans: int = Field(..., description="总计划数")
    draft_plans: int = Field(..., description="草稿计划数")
    confirmed_plans: int = Field(..., description="已确认计划数")
    in_progress_plans: int = Field(..., description="进行中计划数")
    completed_plans: int = Field(..., description="已完成计划数")
    cancelled_plans: int = Field(..., description="已取消计划数")
    paused_plans: int = Field(..., description="已暂停计划数")
    overdue_plans: int = Field(..., description="逾期计划数")
    monthly_new_plans: int = Field(..., description="本月新增计划数")
    monthly_completed_plans: int = Field(..., description="本月完成计划数")
    avg_progress: float = Field(..., description="平均进度")

class ProductionPlanStatusUpdate(BaseModel):
    """生产计划状态更新"""
    status: PlanStatus = Field(..., description="新状态")
    remark: Optional[str] = Field(None, description="备注")

class ProductionPlanPriorityUpdate(BaseModel):
    """生产计划优先级更新"""
    priority: PlanPriority = Field(..., description="新优先级")
    remark: Optional[str] = Field(None, description="备注")

class ProductionPlanBatchOperation(BaseModel):
    """生产计划批量操作"""
    plan_ids: List[int] = Field(..., description="计划ID列表")
    operation: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")

class ProductionPlanImport(BaseModel):
    """生产计划导入"""
    file_url: str = Field(..., description="文件URL")
    file_type: str = Field(..., description="文件类型")
    mapping: Dict[str, str] = Field(..., description="字段映射")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")

class ProductionPlanExport(BaseModel):
    """生产计划导出"""
    plan_ids: Optional[List[int]] = Field(None, description="计划ID列表")
    query: Optional[ProductionPlanQuery] = Field(None, description="查询条件")
    fields: List[str] = Field(..., description="导出字段")
    file_type: str = Field(..., description="文件类型")
    options: Optional[Dict[str, Any]] = Field(None, description="导出选项")

# 工作车间信息
class WorkshopInfo(BaseModel):
    """车间信息"""
    name: str = Field(..., description="车间名称")
    code: str = Field(..., description="车间编码")
    manager: Optional[str] = Field(None, description="车间主管")
    production_lines: List[str] = Field(default=[], description="生产线列表")
    capacity: Optional[int] = Field(None, description="产能")
    status: str = Field(..., description="状态")

# 生产线信息
class ProductionLineInfo(BaseModel):
    """生产线信息"""
    name: str = Field(..., description="生产线名称")
    code: str = Field(..., description="生产线编码")
    workshop: str = Field(..., description="所属车间")
    capacity: Optional[int] = Field(None, description="产能")
    equipment: List[str] = Field(default=[], description="设备列表")
    status: str = Field(..., description="状态")

# 生产计划趋势
class ProductionPlanTrend(BaseModel):
    """生产计划趋势"""
    plan_date: date = Field(..., description="日期")
    new_plans: int = Field(..., description="新增计划数")
    completed_plans: int = Field(..., description="完成计划数")
    in_progress_plans: int = Field(..., description="进行中计划数")
    total_plans: int = Field(..., description="总计划数")

# 生产效率分析
class ProductionEfficiencyAnalysis(BaseModel):
    """生产效率分析"""
    workshop: str = Field(..., description="车间")
    production_line: Optional[str] = Field(None, description="生产线")
    planned_quantity: Decimal = Field(..., description="计划数量")
    actual_quantity: Decimal = Field(..., description="实际数量")
    completion_rate: float = Field(..., description="完成率")
    efficiency_rate: float = Field(..., description="效率")
    avg_cycle_time: Optional[float] = Field(None, description="平均周期时间")

# 生产计划仪表板
class ProductionPlanDashboard(BaseModel):
    """生产计划仪表板"""
    stats: ProductionPlanStats = Field(..., description="统计信息")
    trends: List[ProductionPlanTrend] = Field(..., description="趋势数据")
    efficiency: List[ProductionEfficiencyAnalysis] = Field(..., description="效率分析")
    urgent_plans: List[ProductionPlanSummary] = Field(..., description="紧急计划")
    overdue_plans: List[ProductionPlanSummary] = Field(..., description="逾期计划")
    workshops: List[WorkshopInfo] = Field(..., description="车间信息")
    production_lines: List[ProductionLineInfo] = Field(..., description="生产线信息")