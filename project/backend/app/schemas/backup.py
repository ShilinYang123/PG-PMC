from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class BackupType(str, Enum):
    """备份类型枚举"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DATABASE = "database"
    FILES = "files"
    CONFIG = "config"


class BackupStatus(str, Enum):
    """备份状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RestoreStatus(str, Enum):
    """恢复状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SortOrder(str, Enum):
    """排序方向枚举"""
    ASC = "asc"
    DESC = "desc"


class BackupCreate(BaseModel):
    """创建备份请求模型"""
    backup_type: BackupType = Field(..., description="备份类型")
    description: Optional[str] = Field(None, description="备份描述")
    include_files: bool = Field(True, description="是否包含文件")
    include_config: bool = Field(True, description="是否包含配置")
    
    class Config:
        schema_extra = {
            "example": {
                "backup_type": "full",
                "description": "每日完整备份",
                "include_files": True,
                "include_config": True
            }
        }


class BackupResponse(BaseModel):
    """备份响应模型"""
    backup_id: str = Field(..., description="备份ID")
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="操作消息")
    backup_path: Optional[str] = Field(None, description="备份文件路径")
    backup_size: Optional[int] = Field(None, description="备份文件大小（字节）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    
    class Config:
        schema_extra = {
            "example": {
                "backup_id": "backup_20240101_120000",
                "status": "success",
                "message": "备份创建成功",
                "backup_path": "/backups/backup_20240101_120000.zip",
                "backup_size": 1048576,
                "created_at": "2024-01-01T12:00:00"
            }
        }


class BackupRecord(BaseModel):
    """备份记录模型"""
    backup_id: str = Field(..., description="备份ID")
    backup_type: str = Field(..., description="备份类型")
    status: BackupStatus = Field(..., description="备份状态")
    description: Optional[str] = Field(None, description="备份描述")
    backup_path: str = Field(..., description="备份文件路径")
    backup_size: int = Field(..., description="备份文件大小（字节）")
    checksum: Optional[str] = Field(None, description="文件校验和")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        orm_mode = True


class BackupListResponse(BaseModel):
    """备份列表响应模型"""
    backups: List[BackupRecord] = Field(..., description="备份记录列表")
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="限制数量")
    offset: int = Field(..., description="偏移量")
    
    class Config:
        schema_extra = {
            "example": {
                "backups": [
                    {
                        "backup_id": "backup_20240101_120000",
                        "backup_type": "full",
                        "status": "completed",
                        "description": "每日完整备份",
                        "backup_path": "/backups/backup_20240101_120000.zip",
                        "backup_size": 1048576,
                        "checksum": "abc123def456",
                        "created_at": "2024-01-01T12:00:00",
                        "completed_at": "2024-01-01T12:05:00",
                        "error_message": None
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


class RestoreRequest(BaseModel):
    """恢复请求模型"""
    backup_id: str = Field(..., description="备份ID")
    restore_types: List[str] = Field(..., description="恢复类型列表")
    target_path: Optional[str] = Field(None, description="目标路径")
    force_overwrite: bool = Field(False, description="强制覆盖")
    
    @validator('restore_types')
    def validate_restore_types(cls, v):
        valid_types = ['database', 'files', 'config', 'logs']
        for restore_type in v:
            if restore_type not in valid_types:
                raise ValueError(f'无效的恢复类型: {restore_type}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "backup_id": "backup_20240101_120000",
                "restore_types": ["database", "files"],
                "target_path": "/restore/target",
                "force_overwrite": False
            }
        }


class RestoreResponse(BaseModel):
    """恢复响应模型"""
    restore_id: str = Field(..., description="恢复ID")
    status: str = Field(..., description="操作状态")
    message: str = Field(..., description="操作消息")
    restored_files: List[str] = Field(default_factory=list, description="已恢复文件列表")
    restore_time: Optional[datetime] = Field(None, description="恢复时间")
    
    class Config:
        schema_extra = {
            "example": {
                "restore_id": "restore_20240101_130000",
                "status": "success",
                "message": "备份恢复成功",
                "restored_files": ["/data/database.db", "/uploads/file1.txt"],
                "restore_time": "2024-01-01T13:00:00"
            }
        }


class BackupSearchParams(BaseModel):
    """备份搜索参数模型"""
    backup_type: Optional[str] = Field(None, description="备份类型")
    status: Optional[BackupStatus] = Field(None, description="备份状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    min_size: Optional[int] = Field(None, description="最小文件大小（字节）")
    max_size: Optional[int] = Field(None, description="最大文件大小（字节）")
    description_pattern: Optional[str] = Field(None, description="描述匹配模式")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: SortOrder = Field(SortOrder.DESC, description="排序方向")
    limit: int = Field(50, description="返回数量限制")
    offset: int = Field(0, description="偏移量")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_fields = ['created_at', 'backup_size', 'backup_type', 'status']
        if v not in valid_fields:
            raise ValueError(f'无效的排序字段: {v}')
        return v


class BackupStatistics(BaseModel):
    """备份统计模型"""
    total_backups: int = Field(..., description="总备份数量")
    successful_backups: int = Field(..., description="成功备份数量")
    failed_backups: int = Field(..., description="失败备份数量")
    total_size: int = Field(..., description="总备份大小（字节）")
    average_size: float = Field(..., description="平均备份大小（字节）")
    backup_types: Dict[str, int] = Field(..., description="按类型统计")
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计")
    storage_usage: Dict[str, Any] = Field(..., description="存储使用情况")
    
    class Config:
        schema_extra = {
            "example": {
                "total_backups": 100,
                "successful_backups": 95,
                "failed_backups": 5,
                "total_size": 10737418240,
                "average_size": 107374182,
                "backup_types": {
                    "full": 30,
                    "incremental": 60,
                    "database": 10
                },
                "daily_stats": [
                    {
                        "date": "2024-01-01",
                        "count": 3,
                        "size": 314572800
                    }
                ],
                "storage_usage": {
                    "total_space": 107374182400,
                    "used_space": 10737418240,
                    "free_space": 96636764160,
                    "usage_percentage": 10.0
                }
            }
        }


class BackupHistory(BaseModel):
    """备份历史模型"""
    backup_id: str = Field(..., description="备份ID")
    backup_record: BackupRecord = Field(..., description="备份记录")
    restore_records: List[Dict[str, Any]] = Field(default_factory=list, description="恢复记录")
    verification_records: List[Dict[str, Any]] = Field(default_factory=list, description="验证记录")
    operation_records: List[Dict[str, Any]] = Field(default_factory=list, description="操作记录")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="时间线")
    
    class Config:
        schema_extra = {
            "example": {
                "backup_id": "backup_20240101_120000",
                "backup_record": {
                    "backup_id": "backup_20240101_120000",
                    "backup_type": "full",
                    "status": "completed",
                    "description": "每日完整备份",
                    "backup_path": "/backups/backup_20240101_120000.zip",
                    "backup_size": 1048576,
                    "checksum": "abc123def456",
                    "created_at": "2024-01-01T12:00:00",
                    "completed_at": "2024-01-01T12:05:00",
                    "error_message": None
                },
                "restore_records": [
                    {
                        "restore_id": "restore_20240102_100000",
                        "restore_time": "2024-01-02T10:00:00",
                        "status": "completed"
                    }
                ],
                "verification_records": [
                    {
                        "verify_time": "2024-01-01T12:10:00",
                        "status": "passed",
                        "checksum_valid": True
                    }
                ],
                "operation_records": [
                    {
                        "operation": "create",
                        "timestamp": "2024-01-01T12:00:00",
                        "user": "admin"
                    }
                ],
                "timeline": [
                    {
                        "timestamp": "2024-01-01T12:00:00",
                        "event": "backup_started",
                        "description": "备份开始"
                    },
                    {
                        "timestamp": "2024-01-01T12:05:00",
                        "event": "backup_completed",
                        "description": "备份完成"
                    }
                ]
            }
        }


class BackupVerifyResponse(BaseModel):
    """备份验证响应模型"""
    backup_id: str = Field(..., description="备份ID")
    is_valid: bool = Field(..., description="是否有效")
    file_exists: bool = Field(..., description="文件是否存在")
    size_match: bool = Field(..., description="大小是否匹配")
    checksum_valid: bool = Field(..., description="校验和是否有效")
    archive_valid: Optional[bool] = Field(None, description="压缩文件是否有效")
    content_valid: Optional[bool] = Field(None, description="内容是否有效")
    verification_time: datetime = Field(..., description="验证时间")
    error_details: Optional[List[str]] = Field(None, description="错误详情")
    
    class Config:
        schema_extra = {
            "example": {
                "backup_id": "backup_20240101_120000",
                "is_valid": True,
                "file_exists": True,
                "size_match": True,
                "checksum_valid": True,
                "archive_valid": True,
                "content_valid": True,
                "verification_time": "2024-01-01T12:10:00",
                "error_details": None
            }
        }


class BackupManageRequest(BaseModel):
    """备份管理请求模型"""
    operation: str = Field(..., description="操作类型")
    target_path: Optional[str] = Field(None, description="目标路径")
    new_name: Optional[str] = Field(None, description="新名称")
    compression_level: Optional[int] = Field(9, description="压缩级别")
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_operations = ['rename', 'move', 'copy', 'compress']
        if v not in valid_operations:
            raise ValueError(f'无效的操作类型: {v}')
        return v
    
    @validator('compression_level')
    def validate_compression_level(cls, v):
        if v is not None and (v < 0 or v > 9):
            raise ValueError('压缩级别必须在0-9之间')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "rename",
                "new_name": "backup_renamed.zip",
                "compression_level": 9
            }
        }