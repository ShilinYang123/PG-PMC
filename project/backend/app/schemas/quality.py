from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum

# 枚举定义
class QualityCheckStatus(str, Enum):
    """质量检查状态"""
    PENDING = "pending"  # 待检查
    IN_PROGRESS = "in_progress"  # 检查中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消

class QualityResult(str, Enum):
    """质量检查结果"""
    PASS = "pass"  # 合格
    FAIL = "fail"  # 不合格
    REWORK = "rework"  # 返工
    SCRAP = "scrap"  # 报废

class IssueStatus(str, Enum):
    """问题状态"""
    OPEN = "open"  # 开放
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭
    CANCELLED = "cancelled"  # 已取消

class IssueSeverity(str, Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 严重
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低

class IssueType(str, Enum):
    """问题类型"""
    DEFECT = "defect"  # 缺陷
    DEVIATION = "deviation"  # 偏差
    NON_CONFORMANCE = "non_conformance"  # 不符合项
    IMPROVEMENT = "improvement"  # 改进建议

# 质量问题相关模式
class QualityIssueBase(BaseModel):
    """质量问题基础模式"""
    issue_number: str = Field(..., description="问题编号")
    issue_type: IssueType = Field(..., description="问题类型")
    severity: IssueSeverity = Field(..., description="严重程度")
    description: str = Field(..., description="问题描述")
    root_cause: Optional[str] = Field(None, description="根本原因")
    corrective_action: Optional[str] = Field(None, description="纠正措施")
    preventive_action: Optional[str] = Field(None, description="预防措施")
    responsible_person: Optional[str] = Field(None, description="负责人")
    due_date: Optional[date] = Field(None, description="截止日期")
    completion_date: Optional[date] = Field(None, description="完成日期")
    verification_result: Optional[str] = Field(None, description="验证结果")
    remark: Optional[str] = Field(None, description="备注")

class QualityIssueCreate(QualityIssueBase):
    """创建质量问题模式"""
    status: Optional[IssueStatus] = Field(IssueStatus.OPEN, description="状态")
    
    @validator('issue_number')
    def validate_issue_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('问题编号不能为空')
        if len(v) > 50:
            raise ValueError('问题编号长度不能超过50个字符')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('问题描述不能为空')
        if len(v) > 1000:
            raise ValueError('问题描述长度不能超过1000个字符')
        return v.strip()
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v < date.today():
            raise ValueError('截止日期不能早于今天')
        return v

class QualityIssueUpdate(BaseModel):
    """更新质量问题模式"""
    issue_type: Optional[IssueType] = Field(None, description="问题类型")
    severity: Optional[IssueSeverity] = Field(None, description="严重程度")
    description: Optional[str] = Field(None, description="问题描述")
    root_cause: Optional[str] = Field(None, description="根本原因")
    corrective_action: Optional[str] = Field(None, description="纠正措施")
    preventive_action: Optional[str] = Field(None, description="预防措施")
    responsible_person: Optional[str] = Field(None, description="负责人")
    due_date: Optional[date] = Field(None, description="截止日期")
    completion_date: Optional[date] = Field(None, description="完成日期")
    status: Optional[IssueStatus] = Field(None, description="状态")
    verification_result: Optional[str] = Field(None, description="验证结果")
    remark: Optional[str] = Field(None, description="备注")
    
    @validator('due_date')
    def validate_due_date(cls, v):
        if v and v < date.today():
            raise ValueError('截止日期不能早于今天')
        return v

class QualityIssueDetail(QualityIssueBase):
    """质量问题详情模式"""
    id: int = Field(..., description="问题ID")
    quality_check_id: int = Field(..., description="质量检查ID")
    status: IssueStatus = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

# 质量检查相关模式
class QualityCheckBase(BaseModel):
    """质量检查基础模式"""
    check_number: str = Field(..., description="检查编号")
    product_name: str = Field(..., description="产品名称")
    batch_number: str = Field(..., description="批次号")
    order_id: Optional[int] = Field(None, description="订单ID")
    production_plan_id: Optional[int] = Field(None, description="生产计划ID")
    check_date: date = Field(..., description="检查日期")
    inspector: str = Field(..., description="检查员")
    check_quantity: int = Field(..., description="检查数量")
    pass_quantity: Optional[int] = Field(0, description="合格数量")
    fail_quantity: Optional[int] = Field(0, description="不合格数量")
    defect_quantity: Optional[int] = Field(0, description="缺陷数量")
    check_items: Optional[str] = Field(None, description="检查项目")
    check_standards: Optional[str] = Field(None, description="检查标准")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    remark: Optional[str] = Field(None, description="备注")

class QualityCheckCreate(QualityCheckBase):
    """创建质量检查模式"""
    status: Optional[QualityCheckStatus] = Field(QualityCheckStatus.PENDING, description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    issues_found: Optional[int] = Field(0, description="发现问题数")
    issues: Optional[List[QualityIssueCreate]] = Field([], description="质量问题列表")
    
    @validator('check_number')
    def validate_check_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('检查编号不能为空')
        if len(v) > 50:
            raise ValueError('检查编号长度不能超过50个字符')
        return v.strip()
    
    @validator('product_name')
    def validate_product_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('产品名称不能为空')
        if len(v) > 100:
            raise ValueError('产品名称长度不能超过100个字符')
        return v.strip()
    
    @validator('batch_number')
    def validate_batch_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('批次号不能为空')
        if len(v) > 50:
            raise ValueError('批次号长度不能超过50个字符')
        return v.strip()
    
    @validator('inspector')
    def validate_inspector(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('检查员不能为空')
        if len(v) > 50:
            raise ValueError('检查员长度不能超过50个字符')
        return v.strip()
    
    @validator('check_quantity')
    def validate_check_quantity(cls, v):
        if v <= 0:
            raise ValueError('检查数量必须大于0')
        return v
    
    @validator('pass_quantity')
    def validate_pass_quantity(cls, v, values):
        if v < 0:
            raise ValueError('合格数量不能小于0')
        check_quantity = values.get('check_quantity', 0)
        if v > check_quantity:
            raise ValueError('合格数量不能大于检查数量')
        return v
    
    @validator('fail_quantity')
    def validate_fail_quantity(cls, v, values):
        if v < 0:
            raise ValueError('不合格数量不能小于0')
        check_quantity = values.get('check_quantity', 0)
        pass_quantity = values.get('pass_quantity', 0)
        if v > check_quantity - pass_quantity:
            raise ValueError('不合格数量不能大于剩余数量')
        return v
    
    @validator('check_date')
    def validate_check_date(cls, v):
        if v > date.today():
            raise ValueError('检查日期不能晚于今天')
        return v

class QualityCheckUpdate(BaseModel):
    """更新质量检查模式"""
    check_number: Optional[str] = Field(None, description="检查编号")
    product_name: Optional[str] = Field(None, description="产品名称")
    batch_number: Optional[str] = Field(None, description="批次号")
    check_date: Optional[date] = Field(None, description="检查日期")
    inspector: Optional[str] = Field(None, description="检查员")
    check_quantity: Optional[int] = Field(None, description="检查数量")
    pass_quantity: Optional[int] = Field(None, description="合格数量")
    fail_quantity: Optional[int] = Field(None, description="不合格数量")
    defect_quantity: Optional[int] = Field(None, description="缺陷数量")
    status: Optional[QualityCheckStatus] = Field(None, description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    check_items: Optional[str] = Field(None, description="检查项目")
    check_standards: Optional[str] = Field(None, description="检查标准")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    remark: Optional[str] = Field(None, description="备注")
    
    @validator('check_quantity')
    def validate_check_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('检查数量必须大于0')
        return v
    
    @validator('check_date')
    def validate_check_date(cls, v):
        if v and v > date.today():
            raise ValueError('检查日期不能晚于今天')
        return v

class QualityCheckQuery(BaseModel):
    """质量检查查询模式"""
    keyword: Optional[str] = Field(None, description="关键词搜索")
    status: Optional[QualityCheckStatus] = Field(None, description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    product_name: Optional[str] = Field(None, description="产品名称")
    batch_number: Optional[str] = Field(None, description="批次号")
    inspector: Optional[str] = Field(None, description="检查员")
    order_id: Optional[int] = Field(None, description="订单ID")
    production_plan_id: Optional[int] = Field(None, description="生产计划ID")
    check_date_start: Optional[date] = Field(None, description="检查开始日期")
    check_date_end: Optional[date] = Field(None, description="检查结束日期")
    has_issues: Optional[bool] = Field(None, description="是否有问题")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_field: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")

class QualityCheckDetail(QualityCheckBase):
    """质量检查详情模式"""
    id: int = Field(..., description="检查ID")
    status: QualityCheckStatus = Field(..., description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    pass_rate: float = Field(..., description="合格率")
    issues_found: int = Field(..., description="发现问题数")
    issues: Optional[List[QualityIssueDetail]] = Field([], description="质量问题列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

class QualityCheckSummary(BaseModel):
    """质量检查摘要模式"""
    id: int = Field(..., description="检查ID")
    check_number: str = Field(..., description="检查编号")
    product_name: str = Field(..., description="产品名称")
    batch_number: str = Field(..., description="批次号")
    check_date: date = Field(..., description="检查日期")
    inspector: str = Field(..., description="检查员")
    status: QualityCheckStatus = Field(..., description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    pass_rate: float = Field(..., description="合格率")
    issues_found: int = Field(..., description="发现问题数")
    
    class Config:
        from_attributes = True

class QualityCheckStatusUpdate(BaseModel):
    """质量检查状态更新模式"""
    status: QualityCheckStatus = Field(..., description="状态")
    result: Optional[QualityResult] = Field(None, description="检查结果")
    remark: Optional[str] = Field(None, description="备注")

# 质量标准相关模式
class QualityStandardBase(BaseModel):
    """质量标准基础模式"""
    standard_code: str = Field(..., description="标准编码")
    standard_name: str = Field(..., description="标准名称")
    product_category: str = Field(..., description="产品类别")
    check_items: str = Field(..., description="检查项目")
    acceptance_criteria: str = Field(..., description="验收标准")
    test_method: Optional[str] = Field(None, description="测试方法")
    equipment_required: Optional[str] = Field(None, description="所需设备")
    sample_size: Optional[int] = Field(None, description="样本大小")
    frequency: Optional[str] = Field(None, description="检查频率")
    is_active: bool = Field(True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")

class QualityStandardCreate(QualityStandardBase):
    """创建质量标准模式"""
    
    @validator('standard_code')
    def validate_standard_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('标准编码不能为空')
        if len(v) > 50:
            raise ValueError('标准编码长度不能超过50个字符')
        return v.strip()
    
    @validator('standard_name')
    def validate_standard_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('标准名称不能为空')
        if len(v) > 100:
            raise ValueError('标准名称长度不能超过100个字符')
        return v.strip()
    
    @validator('sample_size')
    def validate_sample_size(cls, v):
        if v is not None and v <= 0:
            raise ValueError('样本大小必须大于0')
        return v

class QualityStandardUpdate(BaseModel):
    """更新质量标准模式"""
    standard_name: Optional[str] = Field(None, description="标准名称")
    product_category: Optional[str] = Field(None, description="产品类别")
    check_items: Optional[str] = Field(None, description="检查项目")
    acceptance_criteria: Optional[str] = Field(None, description="验收标准")
    test_method: Optional[str] = Field(None, description="测试方法")
    equipment_required: Optional[str] = Field(None, description="所需设备")
    sample_size: Optional[int] = Field(None, description="样本大小")
    frequency: Optional[str] = Field(None, description="检查频率")
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")
    
    @validator('sample_size')
    def validate_sample_size(cls, v):
        if v is not None and v <= 0:
            raise ValueError('样本大小必须大于0')
        return v

class QualityStandardDetail(QualityStandardBase):
    """质量标准详情模式"""
    id: int = Field(..., description="标准ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")
    
    class Config:
        from_attributes = True

# 统计相关模式
class QualityStats(BaseModel):
    """质量统计模式"""
    # 检查统计
    total_checks: int = Field(..., description="总检查数")
    pending_checks: int = Field(..., description="待检查数")
    in_progress_checks: int = Field(..., description="检查中数")
    completed_checks: int = Field(..., description="已完成数")
    
    # 结果统计
    pass_checks: int = Field(..., description="合格检查数")
    fail_checks: int = Field(..., description="不合格检查数")
    rework_checks: int = Field(..., description="返工检查数")
    
    # 问题统计
    total_issues: int = Field(..., description="总问题数")
    open_issues: int = Field(..., description="开放问题数")
    in_progress_issues: int = Field(..., description="处理中问题数")
    resolved_issues: int = Field(..., description="已解决问题数")
    closed_issues: int = Field(..., description="已关闭问题数")
    
    # 严重程度统计
    critical_issues: int = Field(..., description="严重问题数")
    high_issues: int = Field(..., description="高级问题数")
    medium_issues: int = Field(..., description="中级问题数")
    low_issues: int = Field(..., description="低级问题数")
    
    # 质量指标
    overall_pass_rate: float = Field(..., description="整体合格率")
    monthly_checks: int = Field(..., description="本月检查数")
    monthly_issues: int = Field(..., description="本月问题数")
    monthly_pass_rate: float = Field(..., description="本月合格率")
    overdue_issues: int = Field(..., description="逾期问题数")

# 批量操作相关模式
class QualityCheckBatchOperation(BaseModel):
    """质量检查批量操作模式"""
    check_ids: List[int] = Field(..., description="检查ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")

class QualityIssueBatchOperation(BaseModel):
    """质量问题批量操作模式"""
    issue_ids: List[int] = Field(..., description="问题ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")

# 导入导出相关模式
class QualityCheckImport(BaseModel):
    """质量检查导入模式"""
    file_path: str = Field(..., description="文件路径")
    file_type: str = Field(..., description="文件类型")
    mapping: Dict[str, str] = Field(..., description="字段映射")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")

class QualityCheckExport(BaseModel):
    """质量检查导出模式"""
    check_ids: Optional[List[int]] = Field(None, description="检查ID列表")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    format: str = Field("excel", description="导出格式")
    options: Optional[Dict[str, Any]] = Field(None, description="导出选项")

# 分析相关模式
class QualityTrend(BaseModel):
    """质量趋势模式"""
    date: date = Field(..., description="日期")
    total_checks: int = Field(..., description="总检查数")
    pass_rate: float = Field(..., description="合格率")
    issues_count: int = Field(..., description="问题数量")
    defect_rate: float = Field(..., description="缺陷率")

class QualityAnalysis(BaseModel):
    """质量分析模式"""
    period: str = Field(..., description="分析周期")
    trends: List[QualityTrend] = Field(..., description="趋势数据")
    top_issues: List[Dict[str, Any]] = Field(..., description="主要问题")
    improvement_suggestions: List[str] = Field(..., description="改进建议")

class QualityDashboard(BaseModel):
    """质量仪表板模式"""
    stats: QualityStats = Field(..., description="统计数据")
    recent_checks: List[QualityCheckSummary] = Field(..., description="最近检查")
    urgent_issues: List[QualityIssueDetail] = Field(..., description="紧急问题")
    quality_trends: List[QualityTrend] = Field(..., description="质量趋势")
    alerts: List[Dict[str, Any]] = Field(..., description="质量警报")

# 报告相关模式
class QualityReport(BaseModel):
    """质量报告模式"""
    report_id: str = Field(..., description="报告ID")
    report_type: str = Field(..., description="报告类型")
    period_start: date = Field(..., description="开始日期")
    period_end: date = Field(..., description="结束日期")
    summary: Dict[str, Any] = Field(..., description="报告摘要")
    details: Dict[str, Any] = Field(..., description="详细数据")
    charts: List[Dict[str, Any]] = Field(..., description="图表数据")
    conclusions: List[str] = Field(..., description="结论")
    recommendations: List[str] = Field(..., description="建议")
    generated_at: datetime = Field(..., description="生成时间")
    generated_by: str = Field(..., description="生成人")

# 配置相关模式
class QualityConfig(BaseModel):
    """质量配置模式"""
    auto_check_enabled: bool = Field(True, description="自动检查启用")
    default_sample_size: int = Field(10, description="默认样本大小")
    alert_thresholds: Dict[str, float] = Field(..., description="警报阈值")
    notification_settings: Dict[str, Any] = Field(..., description="通知设置")
    workflow_settings: Dict[str, Any] = Field(..., description="工作流设置")

# 模板相关模式
class QualityTemplate(BaseModel):
    """质量模板模式"""
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    template_type: str = Field(..., description="模板类型")
    check_items: List[Dict[str, Any]] = Field(..., description="检查项目")
    standards: List[Dict[str, Any]] = Field(..., description="标准要求")
    procedures: List[str] = Field(..., description="检查程序")
    is_default: bool = Field(False, description="是否默认")
    is_active: bool = Field(True, description="是否启用")

# 审计相关模式
class QualityAudit(BaseModel):
    """质量审计模式"""
    audit_id: str = Field(..., description="审计ID")
    audit_type: str = Field(..., description="审计类型")
    audit_scope: str = Field(..., description="审计范围")
    auditor: str = Field(..., description="审计员")
    audit_date: date = Field(..., description="审计日期")
    findings: List[Dict[str, Any]] = Field(..., description="审计发现")
    recommendations: List[str] = Field(..., description="建议")
    status: str = Field(..., description="审计状态")
    follow_up_date: Optional[date] = Field(None, description="跟进日期")

# 培训相关模式
class QualityTraining(BaseModel):
    """质量培训模式"""
    training_id: str = Field(..., description="培训ID")
    training_name: str = Field(..., description="培训名称")
    training_type: str = Field(..., description="培训类型")
    trainer: str = Field(..., description="培训师")
    participants: List[str] = Field(..., description="参与者")
    training_date: date = Field(..., description="培训日期")
    duration: int = Field(..., description="培训时长(小时)")
    content: str = Field(..., description="培训内容")
    materials: List[str] = Field(..., description="培训材料")
    assessment_results: Optional[Dict[str, Any]] = Field(None, description="评估结果")
    effectiveness_score: Optional[float] = Field(None, description="有效性评分")

# 供应商质量相关模式
class SupplierQuality(BaseModel):
    """供应商质量模式"""
    supplier_id: int = Field(..., description="供应商ID")
    supplier_name: str = Field(..., description="供应商名称")
    quality_rating: float = Field(..., description="质量评级")
    defect_rate: float = Field(..., description="缺陷率")
    on_time_delivery_rate: float = Field(..., description="准时交付率")
    compliance_score: float = Field(..., description="合规评分")
    audit_results: List[Dict[str, Any]] = Field(..., description="审计结果")
    improvement_plans: List[str] = Field(..., description="改进计划")
    last_assessment_date: date = Field(..., description="最后评估日期")
    next_assessment_date: date = Field(..., description="下次评估日期")

# 客户投诉相关模式
class CustomerComplaint(BaseModel):
    """客户投诉模式"""
    complaint_id: str = Field(..., description="投诉ID")
    customer_name: str = Field(..., description="客户名称")
    product_name: str = Field(..., description="产品名称")
    batch_number: str = Field(..., description="批次号")
    complaint_type: str = Field(..., description="投诉类型")
    severity: IssueSeverity = Field(..., description="严重程度")
    description: str = Field(..., description="投诉描述")
    received_date: date = Field(..., description="接收日期")
    investigation_results: Optional[str] = Field(None, description="调查结果")
    corrective_actions: Optional[str] = Field(None, description="纠正措施")
    customer_satisfaction: Optional[int] = Field(None, description="客户满意度")
    status: str = Field(..., description="处理状态")
    closed_date: Optional[date] = Field(None, description="关闭日期")

# 成本相关模式
class QualityCost(BaseModel):
    """质量成本模式"""
    period: str = Field(..., description="统计周期")
    prevention_cost: float = Field(..., description="预防成本")
    appraisal_cost: float = Field(..., description="评价成本")
    internal_failure_cost: float = Field(..., description="内部失效成本")
    external_failure_cost: float = Field(..., description="外部失效成本")
    total_quality_cost: float = Field(..., description="总质量成本")
    cost_of_quality_ratio: float = Field(..., description="质量成本比率")
    cost_breakdown: Dict[str, float] = Field(..., description="成本分解")
    trends: List[Dict[str, Any]] = Field(..., description="成本趋势")

# 风险评估相关模式
class QualityRisk(BaseModel):
    """质量风险模式"""
    risk_id: str = Field(..., description="风险ID")
    risk_category: str = Field(..., description="风险类别")
    risk_description: str = Field(..., description="风险描述")
    probability: float = Field(..., description="发生概率")
    impact: float = Field(..., description="影响程度")
    risk_level: str = Field(..., description="风险等级")
    mitigation_measures: List[str] = Field(..., description="缓解措施")
    responsible_person: str = Field(..., description="负责人")
    review_date: date = Field(..., description="评审日期")
    status: str = Field(..., description="风险状态")

# 持续改进相关模式
class ContinuousImprovement(BaseModel):
    """持续改进模式"""
    improvement_id: str = Field(..., description="改进ID")
    improvement_title: str = Field(..., description="改进标题")
    current_state: str = Field(..., description="当前状态")
    target_state: str = Field(..., description="目标状态")
    improvement_actions: List[str] = Field(..., description="改进措施")
    responsible_team: str = Field(..., description="负责团队")
    start_date: date = Field(..., description="开始日期")
    target_completion_date: date = Field(..., description="目标完成日期")
    actual_completion_date: Optional[date] = Field(None, description="实际完成日期")
    success_metrics: List[Dict[str, Any]] = Field(..., description="成功指标")
    results: Optional[Dict[str, Any]] = Field(None, description="改进结果")
    lessons_learned: Optional[List[str]] = Field(None, description="经验教训")
    status: str = Field(..., description="改进状态")