from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

class PageInfo(BaseModel):
    """分页信息模型"""
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页大小")
    total: int = Field(0, description="总记录数")
    total_pages: int = Field(0, description="总页数")
    has_next: bool = Field(False, description="是否有下一页")
    has_prev: bool = Field(False, description="是否有上一页")

class PagedResponseModel(BaseModel, Generic[T]):
    """分页响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: List[T] = Field([], description="响应数据列表")
    page_info: PageInfo = Field(description="分页信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

class QueryParams(BaseModel):
    """查询参数基类"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页大小")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")

class DateRangeFilter(BaseModel):
    """日期范围过滤器"""
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")

class StatusFilter(BaseModel):
    """状态过滤器"""
    status: Optional[str] = Field(None, description="状态")
    status_list: Optional[List[str]] = Field(None, description="状态列表")

class IdListRequest(BaseModel):
    """ID列表请求"""
    ids: List[int] = Field(..., description="ID列表")

class BulkOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[int] = Field(..., description="操作对象ID列表")
    operation: str = Field(..., description="操作类型")
    params: Optional[dict] = Field(None, description="操作参数")

class ImportRequest(BaseModel):
    """导入请求"""
    file_url: str = Field(..., description="文件URL")
    file_type: str = Field(..., description="文件类型")
    options: Optional[dict] = Field(None, description="导入选项")

class ExportRequest(BaseModel):
    """导出请求"""
    export_type: str = Field("excel", description="导出类型")
    filters: Optional[dict] = Field(None, description="过滤条件")
    fields: Optional[List[str]] = Field(None, description="导出字段")

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str = Field(..., description="文件ID")
    file_name: str = Field(..., description="文件名")
    file_url: str = Field(..., description="文件URL")
    file_size: int = Field(..., description="文件大小")
    file_type: str = Field(..., description="文件类型")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")

class ErrorDetail(BaseModel):
    """错误详情"""
    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")

class ValidationErrorResponse(BaseModel):
    """验证错误响应"""
    code: int = Field(422, description="响应状态码")
    message: str = Field("数据验证失败", description="响应消息")
    errors: List[ErrorDetail] = Field(..., description="错误详情列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

class OperationLog(BaseModel):
    """操作日志"""
    operation: str = Field(..., description="操作类型")
    target: str = Field(..., description="操作对象")
    target_id: Optional[int] = Field(None, description="操作对象ID")
    details: Optional[dict] = Field(None, description="操作详情")
    operator: str = Field(..., description="操作人")
    operation_time: datetime = Field(default_factory=datetime.now, description="操作时间")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")

class StatisticsData(BaseModel):
    """统计数据"""
    name: str = Field(..., description="统计项名称")
    value: Any = Field(..., description="统计值")
    unit: Optional[str] = Field(None, description="单位")
    change: Optional[float] = Field(None, description="变化量")
    change_rate: Optional[float] = Field(None, description="变化率")
    trend: Optional[str] = Field(None, description="趋势")

class ChartData(BaseModel):
    """图表数据"""
    labels: List[str] = Field(..., description="标签列表")
    datasets: List[dict] = Field(..., description="数据集列表")
    options: Optional[dict] = Field(None, description="图表选项")

class DashboardData(BaseModel):
    """仪表板数据"""
    statistics: List[StatisticsData] = Field(..., description="统计数据")
    charts: List[ChartData] = Field(..., description="图表数据")
    alerts: Optional[List[dict]] = Field(None, description="告警信息")
    notifications: Optional[List[dict]] = Field(None, description="通知信息")