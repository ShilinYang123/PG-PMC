from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum
from app.schemas.common import QueryParams

# 进度状态枚举
class ProgressStatus(str, Enum):
    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    PAUSED = "paused"           # 暂停
    CANCELLED = "cancelled"     # 取消

# 质量检查结果枚举
class QualityResult(str, Enum):
    PASS = "pass"               # 合格
    FAIL = "fail"               # 不合格
    REWORK = "rework"           # 返工
    SCRAP = "scrap"             # 报废

# 阶段记录基础模型
class StageRecordBase(BaseModel):
    stage_name: str = Field(..., description="阶段名称")
    stage_sequence: int = Field(..., description="阶段顺序")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    responsible_person: Optional[str] = Field(None, description="负责人")
    remark: Optional[str] = Field(None, description="备注")

# 创建阶段记录
class StageRecordCreate(StageRecordBase):
    pass

# 更新阶段记录
class StageRecordUpdate(BaseModel):
    stage_name: Optional[str] = Field(None, description="阶段名称")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    status: Optional[ProgressStatus] = Field(None, description="状态")
    progress: Optional[float] = Field(None, ge=0, le=100, description="进度百分比")
    responsible_person: Optional[str] = Field(None, description="负责人")
    remark: Optional[str] = Field(None, description="备注")

# 阶段记录详情
class StageRecordDetail(StageRecordBase):
    id: int = Field(..., description="阶段记录ID")
    progress_id: int = Field(..., description="进度记录ID")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    status: ProgressStatus = Field(ProgressStatus.NOT_STARTED, description="状态")
    progress: float = Field(0, ge=0, le=100, description="进度百分比")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True

# 质量记录基础模型
class QualityRecordBase(BaseModel):
    checkpoint_name: str = Field(..., description="检查点名称")
    check_date: date = Field(..., description="检查日期")
    checker: str = Field(..., description="检查员")
    check_result: QualityResult = Field(..., description="检查结果")
    check_details: Optional[str] = Field(None, description="检查详情")
    defect_quantity: Optional[int] = Field(0, ge=0, description="缺陷数量")
    rework_quantity: Optional[int] = Field(0, ge=0, description="返工数量")
    scrap_quantity: Optional[int] = Field(0, ge=0, description="报废数量")
    remark: Optional[str] = Field(None, description="备注")

# 创建质量记录
class QualityRecordCreate(QualityRecordBase):
    @validator('check_date')
    def validate_check_date(cls, v):
        if v > date.today():
            raise ValueError('检查日期不能是未来日期')
        return v

# 更新质量记录
class QualityRecordUpdate(BaseModel):
    checkpoint_name: Optional[str] = Field(None, description="检查点名称")
    check_date: Optional[date] = Field(None, description="检查日期")
    checker: Optional[str] = Field(None, description="检查员")
    check_result: Optional[QualityResult] = Field(None, description="检查结果")
    check_details: Optional[str] = Field(None, description="检查详情")
    defect_quantity: Optional[int] = Field(None, ge=0, description="缺陷数量")
    rework_quantity: Optional[int] = Field(None, ge=0, description="返工数量")
    scrap_quantity: Optional[int] = Field(None, ge=0, description="报废数量")
    remark: Optional[str] = Field(None, description="备注")

# 质量记录详情
class QualityRecordDetail(QualityRecordBase):
    id: int = Field(..., description="质量记录ID")
    progress_id: int = Field(..., description="进度记录ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

# 进度更新基础模型
class ProgressUpdateBase(BaseModel):
    update_date: date = Field(..., description="更新日期")
    current_progress: float = Field(..., ge=0, le=100, description="当前进度")
    update_content: str = Field(..., description="更新内容")
    achievements: Optional[str] = Field(None, description="已完成工作")
    issues: Optional[str] = Field(None, description="遇到的问题")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    attachments: Optional[List[str]] = Field(None, description="附件列表")

# 创建进度更新
class ProgressUpdateCreate(ProgressUpdateBase):
    pass

# 进度更新详情
class ProgressUpdateDetail(ProgressUpdateBase):
    id: int = Field(..., description="更新记录ID")
    progress_id: int = Field(..., description="进度记录ID")
    previous_progress: float = Field(..., ge=0, le=100, description="之前进度")
    updater: str = Field(..., description="更新人")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

# 进度记录基础模型
class ProgressRecordBase(BaseModel):
    record_number: str = Field(..., description="记录编号")
    task_name: str = Field(..., description="任务名称")
    plan_id: Optional[int] = Field(None, description="关联生产计划ID")
    order_id: Optional[int] = Field(None, description="关联订单ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    planned_duration: Optional[int] = Field(None, ge=0, description="计划工期(天)")
    responsible_person: str = Field(..., description="负责人")
    team_members: Optional[List[str]] = Field(None, description="团队成员")
    description: Optional[str] = Field(None, description="任务描述")
    remark: Optional[str] = Field(None, description="备注")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('结束日期不能早于开始日期')
        return v

    @validator('record_number')
    def validate_record_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('记录编号不能为空')
        if len(v) > 50:
            raise ValueError('记录编号长度不能超过50个字符')
        return v.strip()

    @validator('task_name')
    def validate_task_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('任务名称不能为空')
        if len(v) > 200:
            raise ValueError('任务名称长度不能超过200个字符')
        return v.strip()

# 创建进度记录
class ProgressRecordCreate(ProgressRecordBase):
    status: Optional[ProgressStatus] = Field(ProgressStatus.NOT_STARTED, description="状态")
    progress: Optional[float] = Field(0, ge=0, le=100, description="进度百分比")
    stages: Optional[List[StageRecordCreate]] = Field(None, description="阶段列表")

# 更新进度记录
class ProgressRecordUpdate(BaseModel):
    task_name: Optional[str] = Field(None, description="任务名称")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    planned_duration: Optional[int] = Field(None, ge=0, description="计划工期(天)")
    actual_duration: Optional[int] = Field(None, ge=0, description="实际工期(天)")
    status: Optional[ProgressStatus] = Field(None, description="状态")
    progress: Optional[float] = Field(None, ge=0, le=100, description="进度百分比")
    responsible_person: Optional[str] = Field(None, description="负责人")
    team_members: Optional[List[str]] = Field(None, description="团队成员")
    description: Optional[str] = Field(None, description="任务描述")
    achievements: Optional[str] = Field(None, description="已完成工作")
    issues: Optional[str] = Field(None, description="遇到的问题")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    remark: Optional[str] = Field(None, description="备注")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('结束日期不能早于开始日期')
        return v

# 进度记录查询
class ProgressRecordQuery(QueryParams):
    keyword: Optional[str] = Field(None, description="关键词搜索")
    status: Optional[ProgressStatus] = Field(None, description="状态")
    plan_id: Optional[int] = Field(None, description="生产计划ID")
    order_id: Optional[int] = Field(None, description="订单ID")
    responsible_person: Optional[str] = Field(None, description="负责人")
    start_date_start: Optional[date] = Field(None, description="开始日期范围-开始")
    start_date_end: Optional[date] = Field(None, description="开始日期范围-结束")
    end_date_start: Optional[date] = Field(None, description="结束日期范围-开始")
    end_date_end: Optional[date] = Field(None, description="结束日期范围-结束")
    progress_min: Optional[float] = Field(None, ge=0, le=100, description="最小进度")
    progress_max: Optional[float] = Field(None, ge=0, le=100, description="最大进度")

# 进度记录详情
class ProgressRecordDetail(ProgressRecordBase):
    id: int = Field(..., description="进度记录ID")
    plan_number: Optional[str] = Field(None, description="生产计划编号")
    order_number: Optional[str] = Field(None, description="订单编号")
    actual_duration: Optional[int] = Field(None, description="实际工期(天)")
    status: ProgressStatus = Field(..., description="状态")
    progress: float = Field(..., description="进度百分比")
    achievements: Optional[str] = Field(None, description="已完成工作")
    issues: Optional[str] = Field(None, description="遇到的问题")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    stages: Optional[List[StageRecordDetail]] = Field(None, description="阶段列表")
    quality_records: Optional[List[QualityRecordDetail]] = Field(None, description="质量记录")
    updates: Optional[List[ProgressUpdateDetail]] = Field(None, description="进度更新记录")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: str = Field(..., description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")

    class Config:
        from_attributes = True

# 进度记录摘要
class ProgressRecordSummary(BaseModel):
    id: int = Field(..., description="进度记录ID")
    record_number: str = Field(..., description="记录编号")
    task_name: str = Field(..., description="任务名称")
    plan_number: Optional[str] = Field(None, description="生产计划编号")
    order_number: Optional[str] = Field(None, description="订单编号")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    status: ProgressStatus = Field(..., description="状态")
    progress: float = Field(..., description="进度百分比")
    responsible_person: str = Field(..., description="负责人")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True

# 进度统计
class ProgressStats(BaseModel):
    total_records: int = Field(..., description="总记录数")
    not_started_records: int = Field(..., description="未开始记录数")
    in_progress_records: int = Field(..., description="进行中记录数")
    completed_records: int = Field(..., description="已完成记录数")
    paused_records: int = Field(..., description="暂停记录数")
    cancelled_records: int = Field(..., description="取消记录数")
    overdue_records: int = Field(..., description="逾期记录数")
    avg_progress: float = Field(..., description="平均进度")
    monthly_new_records: int = Field(..., description="本月新增记录数")
    monthly_completed_records: int = Field(..., description="本月完成记录数")
    total_quality_checks: int = Field(..., description="总质量检查数")
    passed_quality_checks: int = Field(..., description="通过质量检查数")
    failed_quality_checks: int = Field(..., description="未通过质量检查数")

# 进度状态更新
class ProgressStatusUpdate(BaseModel):
    status: ProgressStatus = Field(..., description="状态")
    remark: Optional[str] = Field(None, description="备注")

# 进度更新
class ProgressProgressUpdate(BaseModel):
    progress: float = Field(..., ge=0, le=100, description="进度百分比")
    achievements: Optional[str] = Field(None, description="已完成工作")
    issues: Optional[str] = Field(None, description="遇到的问题")
    next_steps: Optional[str] = Field(None, description="下一步计划")
    remark: Optional[str] = Field(None, description="备注")

# 批量操作
class ProgressBatchOperation(BaseModel):
    record_ids: List[int] = Field(..., description="记录ID列表")
    operation: str = Field(..., description="操作类型")
    data: Optional[Dict[str, Any]] = Field(None, description="操作数据")

# 进度导入
class ProgressImport(BaseModel):
    file_url: str = Field(..., description="文件URL")
    file_type: str = Field(..., description="文件类型")
    mapping: Dict[str, str] = Field(..., description="字段映射")

# 进度导出
class ProgressExport(BaseModel):
    record_ids: Optional[List[int]] = Field(None, description="记录ID列表")
    export_type: str = Field(..., description="导出类型")
    include_stages: bool = Field(True, description="包含阶段信息")
    include_quality: bool = Field(True, description="包含质量信息")
    include_updates: bool = Field(True, description="包含更新记录")

# 项目信息
class ProjectInfo(BaseModel):
    id: int = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    code: str = Field(..., description="项目编码")
    status: str = Field(..., description="项目状态")

# 任务信息
class TaskInfo(BaseModel):
    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    type: str = Field(..., description="任务类型")
    priority: str = Field(..., description="优先级")

# 进度趋势
class ProgressTrend(BaseModel):
    trend_date: date = Field(..., description="日期")
    total_records: int = Field(..., description="总记录数")
    completed_records: int = Field(..., description="完成记录数")
    avg_progress: float = Field(..., description="平均进度")
    completion_rate: float = Field(..., description="完成率")

# 效率分析
class EfficiencyAnalysis(BaseModel):
    responsible_person: str = Field(..., description="负责人")
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="完成任务数")
    avg_completion_time: float = Field(..., description="平均完成时间")
    on_time_rate: float = Field(..., description="按时完成率")
    efficiency_score: float = Field(..., description="效率评分")

# 质量分析
class QualityAnalysis(BaseModel):
    checkpoint_name: str = Field(..., description="检查点名称")
    total_checks: int = Field(..., description="总检查次数")
    pass_rate: float = Field(..., description="合格率")
    avg_defect_rate: float = Field(..., description="平均缺陷率")
    rework_rate: float = Field(..., description="返工率")
    scrap_rate: float = Field(..., description="报废率")

# 进度仪表板
class ProgressDashboard(BaseModel):
    overview_stats: ProgressStats = Field(..., description="概览统计")
    progress_trends: List[ProgressTrend] = Field(..., description="进度趋势")
    efficiency_analysis: List[EfficiencyAnalysis] = Field(..., description="效率分析")
    quality_analysis: List[QualityAnalysis] = Field(..., description="质量分析")
    recent_updates: List[ProgressUpdateDetail] = Field(..., description="最近更新")
    overdue_tasks: List[ProgressRecordSummary] = Field(..., description="逾期任务")
    urgent_issues: List[str] = Field(..., description="紧急问题")

# 进度报告
class ProgressReport(BaseModel):
    report_id: str = Field(..., description="报告ID")
    report_name: str = Field(..., description="报告名称")
    report_period: str = Field(..., description="报告周期")
    generated_at: datetime = Field(..., description="生成时间")
    generated_by: str = Field(..., description="生成人")
    summary: str = Field(..., description="总结")
    key_achievements: List[str] = Field(..., description="关键成就")
    major_issues: List[str] = Field(..., description="主要问题")
    recommendations: List[str] = Field(..., description="建议")
    attachments: List[str] = Field(..., description="附件")

# 里程碑
class Milestone(BaseModel):
    id: int = Field(..., description="里程碑ID")
    name: str = Field(..., description="里程碑名称")
    description: str = Field(..., description="描述")
    target_date: date = Field(..., description="目标日期")
    actual_date: Optional[date] = Field(None, description="实际日期")
    status: str = Field(..., description="状态")
    progress_id: int = Field(..., description="关联进度记录ID")
    created_at: datetime = Field(..., description="创建时间")

# 风险评估
class RiskAssessment(BaseModel):
    risk_id: str = Field(..., description="风险ID")
    risk_name: str = Field(..., description="风险名称")
    risk_level: str = Field(..., description="风险等级")
    probability: float = Field(..., ge=0, le=1, description="发生概率")
    impact: float = Field(..., ge=0, le=10, description="影响程度")
    mitigation_plan: str = Field(..., description="缓解计划")
    owner: str = Field(..., description="负责人")
    status: str = Field(..., description="状态")
    progress_id: int = Field(..., description="关联进度记录ID")

# 资源使用情况
class ResourceUsage(BaseModel):
    resource_type: str = Field(..., description="资源类型")
    resource_name: str = Field(..., description="资源名称")
    allocated_amount: float = Field(..., description="分配数量")
    used_amount: float = Field(..., description="使用数量")
    utilization_rate: float = Field(..., description="利用率")
    cost: float = Field(..., description="成本")
    progress_id: int = Field(..., description="关联进度记录ID")

# 协作记录
class CollaborationRecord(BaseModel):
    id: int = Field(..., description="协作记录ID")
    progress_id: int = Field(..., description="进度记录ID")
    collaborator: str = Field(..., description="协作者")
    collaboration_type: str = Field(..., description="协作类型")
    content: str = Field(..., description="协作内容")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")

# 通知设置
class NotificationSetting(BaseModel):
    user_id: int = Field(..., description="用户ID")
    progress_update: bool = Field(True, description="进度更新通知")
    milestone_reached: bool = Field(True, description="里程碑达成通知")
    deadline_approaching: bool = Field(True, description="截止日期临近通知")
    quality_issue: bool = Field(True, description="质量问题通知")
    risk_alert: bool = Field(True, description="风险预警通知")
    email_enabled: bool = Field(True, description="邮件通知")
    sms_enabled: bool = Field(False, description="短信通知")
    in_app_enabled: bool = Field(True, description="应用内通知")

# 进度模板
class ProgressTemplate(BaseModel):
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    category: str = Field(..., description="模板分类")
    stages: List[Dict[str, Any]] = Field(..., description="阶段模板")
    quality_checkpoints: List[Dict[str, Any]] = Field(..., description="质量检查点模板")
    is_active: bool = Field(True, description="是否启用")
    created_by: str = Field(..., description="创建人")
    created_at: datetime = Field(..., description="创建时间")

# 进度配置
class ProgressConfig(BaseModel):
    auto_update_enabled: bool = Field(True, description="自动更新启用")
    notification_enabled: bool = Field(True, description="通知启用")
    quality_check_required: bool = Field(True, description="质量检查必需")
    milestone_tracking: bool = Field(True, description="里程碑跟踪")
    risk_assessment: bool = Field(True, description="风险评估")
    resource_tracking: bool = Field(True, description="资源跟踪")
    collaboration_enabled: bool = Field(True, description="协作启用")
    report_generation: bool = Field(True, description="报告生成")
    data_retention_days: int = Field(365, description="数据保留天数")
    backup_enabled: bool = Field(True, description="备份启用")

# 进度汇总
class ProgressSummary(BaseModel):
    total_tasks: int = Field(..., description="总任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    in_progress_tasks: int = Field(..., description="进行中任务数")
    pending_tasks: int = Field(..., description="待开始任务数")
    overdue_tasks: int = Field(..., description="逾期任务数")
    completion_rate: float = Field(..., description="完成率")
    average_progress: float = Field(..., description="平均进度")
    on_time_rate: float = Field(..., description="按时完成率")
    quality_pass_rate: float = Field(..., description="质量通过率")
    
    class Config:
        from_attributes = True