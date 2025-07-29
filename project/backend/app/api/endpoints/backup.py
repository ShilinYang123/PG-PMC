from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import json
from io import BytesIO
from loguru import logger

from ...core.deps import get_current_user, get_db
from ...core.permissions import require_permission, Permission
from ...models.user import User
from ...services.backup_service import backup_service
from ...services.backup_scheduler import backup_scheduler
from ...schemas.backup import (
    BackupCreate, BackupResponse, BackupListResponse,
    BackupStatistics, BackupHistory, BackupSearchParams,
    RestoreRequest, RestoreResponse, BackupVerifyResponse
)

router = APIRouter()


@router.post("/create", response_model=BackupResponse)
@require_permission(Permission.ADMIN)
def create_backup(
    backup_data: BackupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建备份
    
    支持的备份类型:
    - full: 完整备份（数据库+文件+配置）
    - incremental: 增量备份
    - database: 仅数据库备份
    - files: 仅文件备份
    - config: 仅配置备份
    """
    try:
        if backup_data.backup_type == "full":
            result = backup_service.create_full_backup(
                description=backup_data.description,
                include_files=backup_data.include_files,
                include_config=backup_data.include_config
            )
        elif backup_data.backup_type == "incremental":
            result = backup_service.create_incremental_backup(
                description=backup_data.description
            )
        else:
            # 自定义备份类型
            backup_types = {
                "database": ["database"],
                "files": ["files"],
                "config": ["config"]
            }
            
            if backup_data.backup_type not in backup_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的备份类型: {backup_data.backup_type}"
                )
            
            result = backup_service.create_custom_backup(
                backup_types=backup_types[backup_data.backup_type],
                description=backup_data.description
            )
        
        return BackupResponse(
            backup_id=result["backup_id"],
            status="success",
            message="备份创建成功",
            backup_path=result["backup_path"],
            backup_size=result["backup_size"],
            created_at=result["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"备份创建失败: {str(e)}"
        )


@router.post("/restore", response_model=RestoreResponse)
@require_permission(Permission.ADMIN)
def restore_backup(
    restore_data: RestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    恢复备份
    """
    try:
        result = backup_service.restore_backup(
            backup_id=restore_data.backup_id,
            restore_types=restore_data.restore_types,
            target_path=restore_data.target_path,
            force_overwrite=restore_data.force_overwrite
        )
        
        return RestoreResponse(
            restore_id=result["restore_id"],
            status="success",
            message="备份恢复成功",
            restored_files=result.get("restored_files", []),
            restore_time=result["restore_time"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"备份恢复失败: {str(e)}"
        )


@router.get("/list", response_model=BackupListResponse)
@require_permission(Permission.ADMIN)
def list_backups(
    backup_type: Optional[str] = Query(None, description="备份类型过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(50, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取备份列表
    """
    try:
        backups = backup_service.get_backup_records(
            backup_type=backup_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return BackupListResponse(
            backups=backups,
            total=len(backups),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取备份列表失败: {str(e)}"
        )


@router.get("/search", response_model=BackupListResponse)
@require_permission(Permission.ADMIN)
def search_backups(
    search_params: BackupSearchParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索备份
    """
    try:
        backups = backup_service.search_backups(
            backup_type=search_params.backup_type,
            status=search_params.status,
            start_date=search_params.start_date,
            end_date=search_params.end_date,
            min_size=search_params.min_size,
            max_size=search_params.max_size,
            description_pattern=search_params.description_pattern,
            sort_by=search_params.sort_by,
            sort_order=search_params.sort_order,
            limit=search_params.limit,
            offset=search_params.offset
        )
        
        return BackupListResponse(
            backups=backups,
            total=len(backups),
            limit=search_params.limit,
            offset=search_params.offset
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索备份失败: {str(e)}"
        )


@router.get("/statistics", response_model=BackupStatistics)
@require_permission(Permission.ADMIN)
def get_backup_statistics(
    start_date: Optional[datetime] = Query(None, description="统计开始日期"),
    end_date: Optional[datetime] = Query(None, description="统计结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取备份统计信息
    """
    try:
        stats = backup_service.get_backup_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        return BackupStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取备份统计失败: {str(e)}"
        )


@router.get("/history/{backup_id}", response_model=BackupHistory)
@require_permission(Permission.ADMIN)
def get_backup_history(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定备份的历史记录
    """
    try:
        history = backup_service.get_backup_history(backup_id)
        
        return BackupHistory(**history)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取备份历史失败: {str(e)}"
        )


@router.post("/verify/{backup_id}", response_model=BackupVerifyResponse)
@require_permission(Permission.ADMIN)
def verify_backup(
    backup_id: str,
    deep_check: bool = Query(False, description="是否进行深度验证"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证备份完整性
    """
    try:
        result = backup_service.verify_backup(
            backup_id=backup_id,
            deep_check=deep_check
        )
        
        return BackupVerifyResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"备份验证失败: {str(e)}"
        )


@router.delete("/delete/{backup_id}")
@require_permission(Permission.ADMIN)
def delete_backup(
    backup_id: str,
    force: bool = Query(False, description="强制删除"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除备份
    """
    try:
        result = backup_service.delete_backup(
            backup_id=backup_id,
            force=force
        )
        
        return {
            "status": "success",
            "message": "备份删除成功",
            "deleted_files": result.get("deleted_files", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除备份失败: {str(e)}"
        )


@router.post("/cleanup")
@require_permission(Permission.ADMIN)
def cleanup_old_backups(
    retention_days: int = Query(30, description="保留天数"),
    backup_type: Optional[str] = Query(None, description="备份类型"),
    dry_run: bool = Query(False, description="试运行模式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清理过期备份
    """
    try:
        result = backup_service.cleanup_old_backups(
            retention_days=retention_days,
            backup_type=backup_type,
            dry_run=dry_run
        )
        
        return {
            "status": "success",
            "message": "备份清理完成" if not dry_run else "备份清理预览完成",
            "cleaned_count": result.get("cleaned_count", 0),
            "freed_space": result.get("freed_space", 0),
            "cleaned_backups": result.get("cleaned_backups", [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"备份清理失败: {str(e)}"
        )


@router.post("/manage/{backup_id}")
@require_permission(Permission.ADMIN)
def manage_backup_file(
    backup_id: str,
    operation: str = Body(..., description="操作类型: rename, move, copy, compress"),
    target_path: Optional[str] = Body(None, description="目标路径"),
    new_name: Optional[str] = Body(None, description="新名称"),
    compression_level: Optional[int] = Body(9, description="压缩级别"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    管理备份文件
    """
    try:
        result = backup_service.manage_backup_file(
            backup_id=backup_id,
            operation=operation,
            target_path=target_path,
            new_name=new_name,
            compression_level=compression_level
        )
        
        return {
            "status": "success",
            "message": f"备份文件{operation}操作完成",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"备份文件管理失败: {str(e)}"
        )


@router.get("/download/{backup_id}")
@require_permission(Permission.ADMIN)
def download_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载备份文件
    """
    try:
        backup_record = backup_service._get_backup_record(backup_id)
        if not backup_record:
            raise HTTPException(
                status_code=404,
                detail="备份记录不存在"
            )
        
        backup_path = backup_record["backup_path"]
        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=404,
                detail="备份文件不存在"
            )
        
        filename = os.path.basename(backup_path)
        return FileResponse(
            path=backup_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"下载备份失败: {str(e)}"
        )


@router.get("/export/metadata")
@require_permission(Permission.ADMIN)
def export_backup_metadata(
    format: str = Query("json", description="导出格式: json, csv"),
    backup_ids: Optional[List[str]] = Query(None, description="指定备份ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出备份元数据
    """
    try:
        result = backup_service.export_backup_metadata(
            format=format,
            backup_ids=backup_ids
        )
        
        if format.lower() == "csv":
            media_type = "text/csv"
            filename = f"backup_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            media_type = "application/json"
            filename = f"backup_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return StreamingResponse(
            BytesIO(result.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"导出备份元数据失败: {str(e)}"
        )


@router.get("/health")
def backup_service_health():
    """
    备份服务健康检查
    """
    try:
        # 检查备份目录是否可访问
        backup_dir = backup_service.backup_dir
        if not os.path.exists(backup_dir):
            return {
                "status": "unhealthy",
                "message": "备份目录不存在",
                "backup_dir": backup_dir
            }
        
        # 检查磁盘空间
        import shutil
        total, used, free = shutil.disk_usage(backup_dir)
        free_gb = free // (1024**3)
        
        if free_gb < 1:  # 少于1GB空间
            return {
                "status": "warning",
                "message": "磁盘空间不足",
                "free_space_gb": free_gb
            }
        
        return {
            "status": "healthy",
            "message": "备份服务正常",
            "backup_dir": backup_dir,
            "free_space_gb": free_gb
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"健康检查失败: {str(e)}"
        }


# 备份调度器管理接口
@router.get("/scheduler/status")
@require_permission(Permission.ADMIN)
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取备份调度器状态"""
    try:
        status = await backup_scheduler.get_status()
        return {
            "success": True,
            "data": status,
            "message": "获取调度器状态成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取调度器状态失败: {str(e)}"
        )


@router.post("/scheduler/start")
@require_permission(Permission.ADMIN)
async def start_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启动备份调度器"""
    try:
        await backup_scheduler.start()
        return {
            "success": True,
            "message": "备份调度器启动成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动备份调度器失败: {str(e)}"
        )


@router.post("/scheduler/stop")
@require_permission(Permission.ADMIN)
async def stop_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """停止备份调度器"""
    try:
        await backup_scheduler.stop()
        return {
            "success": True,
            "message": "备份调度器停止成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"停止备份调度器失败: {str(e)}"
        )


@router.get("/scheduler/jobs")
@require_permission(Permission.ADMIN)
async def list_backup_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有备份任务"""
    try:
        jobs = await backup_scheduler.list_jobs()
        return {
            "success": True,
            "data": jobs,
            "message": "获取备份任务列表成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取备份任务列表失败: {str(e)}"
        )


@router.post("/scheduler/jobs")
@require_permission(Permission.ADMIN)
async def add_backup_job(
    job_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加自定义备份任务"""
    try:
        job_id = await backup_scheduler.add_custom_backup_job(
            job_config.get('name'),
            job_config.get('trigger_type'),
            job_config.get('trigger_config', {}),
            job_config.get('backup_config', {})
        )
        return {
            "success": True,
            "data": {"job_id": job_id},
            "message": "添加备份任务成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"添加备份任务失败: {str(e)}"
        )


@router.delete("/scheduler/jobs/{job_id}")
@require_permission(Permission.ADMIN)
async def remove_backup_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除备份任务"""
    try:
        await backup_scheduler.remove_job(job_id)
        return {
            "success": True,
            "message": "删除备份任务成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除备份任务失败: {str(e)}"
        )


@router.put("/scheduler/jobs/{job_id}")
@require_permission(Permission.ADMIN)
async def modify_backup_job(
    job_id: str,
    job_config: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改备份任务"""
    try:
        await backup_scheduler.modify_job(
            job_id,
            job_config.get('trigger_type'),
            job_config.get('trigger_config', {}),
            job_config.get('backup_config', {})
        )
        return {
            "success": True,
            "message": "修改备份任务成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"修改备份任务失败: {str(e)}"
        )


@router.post("/scheduler/jobs/{job_id}/pause")
@require_permission(Permission.ADMIN)
async def pause_backup_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """暂停备份任务"""
    try:
        await backup_scheduler.pause_job(job_id)
        return {
            "success": True,
            "message": "暂停备份任务成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"暂停备份任务失败: {str(e)}"
        )


@router.post("/scheduler/jobs/{job_id}/resume")
@require_permission(Permission.ADMIN)
async def resume_backup_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """恢复备份任务"""
    try:
        await backup_scheduler.resume_job(job_id)
        return {
            "success": True,
            "message": "恢复备份任务成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"恢复备份任务失败: {str(e)}"
        )


@router.post("/scheduler/jobs/{job_id}/run")
@require_permission(Permission.ADMIN)
async def run_backup_job_now(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """立即执行备份任务"""
    try:
        result = await backup_scheduler.run_job_now(job_id)
        return {
            "success": True,
            "data": result,
            "message": "备份任务执行成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"执行备份任务失败: {str(e)}"
        )