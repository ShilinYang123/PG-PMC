#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入导出数据模式

定义导入导出相关的请求和响应模式：
- 导入请求和响应
- 导出请求和响应
- 文件上传响应
- 模板请求
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class FileFormat(str, Enum):
    """文件格式枚举"""
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    PDF = "pdf"
    TXT = "txt"


class ImportStatus(str, Enum):
    """导入状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportStatus(str, Enum):
    """导出状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportRequest(BaseModel):
    """导入请求模式"""
    file_path: str = Field(..., description="文件路径")
    file_type: Optional[FileFormat] = Field(None, description="文件类型")
    sheet_name: Optional[str] = Field(None, description="工作表名称")
    header_row: Optional[int] = Field(0, description="标题行索引")
    max_rows: Optional[int] = Field(None, description="最大读取行数")
    field_mapping: Optional[Dict[str, str]] = Field(None, description="字段映射")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    skip_errors: bool = Field(False, description="是否跳过错误")
    batch_size: int = Field(1000, description="批处理大小")
    
    class Config:
        schema_extra = {
            "example": {
                "file_path": "/uploads/import/data.xlsx",
                "file_type": "xlsx",
                "sheet_name": "Sheet1",
                "header_row": 0,
                "max_rows": 10000,
                "field_mapping": {
                    "项目名称": "project_name",
                    "任务名称": "task_name",
                    "进度": "progress"
                },
                "filters": {
                    "status": "active"
                },
                "skip_errors": True,
                "batch_size": 500
            }
        }


class ExportRequest(BaseModel):
    """导出请求模式"""
    format: FileFormat = Field(FileFormat.XLSX, description="导出格式")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", description="排序方向")
    limit: Optional[int] = Field(None, description="限制数量")
    include_headers: bool = Field(True, description="是否包含标题")
    date_format: Optional[str] = Field("%Y-%m-%d", description="日期格式")
    style_config: Optional[Dict[str, Any]] = Field(None, description="样式配置")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "format": "xlsx",
                "fields": ["project_name", "task_name", "progress", "status"],
                "filters": {
                    "status": "active",
                    "created_date": {
                        "gte": "2024-01-01",
                        "lte": "2024-12-31"
                    }
                },
                "sort_by": "created_date",
                "sort_order": "desc",
                "limit": 1000,
                "include_headers": True,
                "date_format": "%Y-%m-%d %H:%M:%S"
            }
        }


class FileUploadResponse(BaseModel):
    """文件上传响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    file_url: str = Field(..., description="文件URL")
    file_size: int = Field(..., description="文件大小")
    file_type: str = Field(..., description="文件类型")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "文件上传成功",
                "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "filename": "data_20240101_123456.xlsx",
                "file_url": "/api/files/import/data_20240101_123456.xlsx",
                "file_size": 1024000,
                "file_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "upload_time": "2024-01-01T12:34:56"
            }
        }


class ImportResponse(BaseModel):
    """导入响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: str = Field(..., description="任务ID")
    total_rows: int = Field(..., description="总行数")
    preview_data: Optional[List[Dict[str, Any]]] = Field(None, description="预览数据")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="验证错误")
    estimated_time: Optional[int] = Field(None, description="预计处理时间（秒）")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "数据导入任务已启动",
                "task_id": "import_progress_20240101_123456",
                "total_rows": 1000,
                "preview_data": [
                    {
                        "project_name": "项目A",
                        "task_name": "任务1",
                        "progress": 50
                    }
                ],
                "validation_errors": [],
                "estimated_time": 30
            }
        }


class ExportResponse(BaseModel):
    """导出响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: str = Field(..., description="任务ID")
    estimated_rows: Optional[int] = Field(None, description="预计行数")
    estimated_time: Optional[int] = Field(None, description="预计处理时间（秒）")
    download_url: Optional[str] = Field(None, description="下载链接")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "数据导出任务已启动",
                "task_id": "export_progress_20240101_123456",
                "estimated_rows": 1000,
                "estimated_time": 30,
                "download_url": None
            }
        }


class TaskStatus(BaseModel):
    """任务状态模式"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    message: str = Field(..., description="状态消息")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "import_progress_20240101_123456",
                "status": "completed",
                "progress": 100,
                "message": "导入完成",
                "start_time": "2024-01-01T12:34:56",
                "end_time": "2024-01-01T12:35:26",
                "result": {
                    "success_count": 950,
                    "error_count": 50,
                    "total_count": 1000,
                    "errors": [
                        {
                            "row": 10,
                            "field": "progress",
                            "error": "进度值必须在0-100之间"
                        }
                    ]
                },
                "error": None
            }
        }


class TemplateRequest(BaseModel):
    """模板请求模式"""
    data_type: str = Field(..., description="数据类型")
    format: FileFormat = Field(FileFormat.XLSX, description="文件格式")
    include_sample_data: bool = Field(True, description="是否包含示例数据")
    language: str = Field("zh", description="语言")
    
    class Config:
        schema_extra = {
            "example": {
                "data_type": "progress",
                "format": "xlsx",
                "include_sample_data": True,
                "language": "zh"
            }
        }


class ValidationRule(BaseModel):
    """验证规则模式"""
    field: str = Field(..., description="字段名")
    rule_type: str = Field(..., description="规则类型")
    parameters: Dict[str, Any] = Field(..., description="规则参数")
    error_message: str = Field(..., description="错误消息")
    
    class Config:
        schema_extra = {
            "example": {
                "field": "progress",
                "rule_type": "range",
                "parameters": {
                    "min": 0,
                    "max": 100
                },
                "error_message": "进度值必须在0-100之间"
            }
        }


class ImportConfig(BaseModel):
    """导入配置模式"""
    data_type: str = Field(..., description="数据类型")
    required_fields: List[str] = Field(..., description="必需字段")
    optional_fields: List[str] = Field(default_factory=list, description="可选字段")
    field_mappings: Dict[str, str] = Field(default_factory=dict, description="字段映射")
    validation_rules: List[ValidationRule] = Field(default_factory=list, description="验证规则")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="默认值")
    
    class Config:
        schema_extra = {
            "example": {
                "data_type": "progress",
                "required_fields": ["project_name", "task_name", "progress"],
                "optional_fields": ["description", "assignee"],
                "field_mappings": {
                    "项目名称": "project_name",
                    "任务名称": "task_name",
                    "进度": "progress"
                },
                "validation_rules": [
                    {
                        "field": "progress",
                        "rule_type": "range",
                        "parameters": {"min": 0, "max": 100},
                        "error_message": "进度值必须在0-100之间"
                    }
                ],
                "default_values": {
                    "status": "active",
                    "created_by": "system"
                }
            }
        }


class ExportConfig(BaseModel):
    """导出配置模式"""
    data_type: str = Field(..., description="数据类型")
    available_fields: List[str] = Field(..., description="可用字段")
    default_fields: List[str] = Field(..., description="默认字段")
    field_labels: Dict[str, str] = Field(default_factory=dict, description="字段标签")
    supported_formats: List[FileFormat] = Field(default_factory=list, description="支持的格式")
    max_rows: int = Field(10000, description="最大导出行数")
    
    class Config:
        schema_extra = {
            "example": {
                "data_type": "progress",
                "available_fields": [
                    "project_name", "task_name", "progress", 
                    "status", "created_date", "updated_date"
                ],
                "default_fields": ["project_name", "task_name", "progress", "status"],
                "field_labels": {
                    "project_name": "项目名称",
                    "task_name": "任务名称",
                    "progress": "进度(%)",
                    "status": "状态"
                },
                "supported_formats": ["xlsx", "csv", "pdf"],
                "max_rows": 10000
            }
        }


class BatchOperationRequest(BaseModel):
    """批量操作请求模式"""
    operation: str = Field(..., description="操作类型")
    data_type: str = Field(..., description="数据类型")
    ids: List[int] = Field(..., description="ID列表")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "update_status",
                "data_type": "progress",
                "ids": [1, 2, 3, 4, 5],
                "parameters": {
                    "status": "completed",
                    "updated_by": "admin"
                }
            }
        }


class BatchOperationResponse(BaseModel):
    """批量操作响应模式"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    error_count: int = Field(..., description="失败数量")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误详情")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "批量操作完成",
                "total_count": 5,
                "success_count": 4,
                "error_count": 1,
                "errors": [
                    {
                        "id": 3,
                        "error": "记录不存在"
                    }
                ]
            }
        }


# 导出所有模式
__all__ = [
    'FileFormat',
    'ImportStatus',
    'ExportStatus',
    'ImportRequest',
    'ExportRequest',
    'FileUploadResponse',
    'ImportResponse',
    'ExportResponse',
    'TaskStatus',
    'TemplateRequest',
    'ValidationRule',
    'ImportConfig',
    'ExportConfig',
    'BatchOperationRequest',
    'BatchOperationResponse'
]