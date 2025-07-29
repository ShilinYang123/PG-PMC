#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入导出API

提供数据导入导出功能：
- 文件上传
- Excel数据导入
- 数据导出
- 模板下载
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from loguru import logger
import pandas as pd
from datetime import datetime
import io
import json

from ..database import get_db
from ..services.file_service import file_service
from ..models.progress import ProgressRecord
from ..models.equipment import Equipment
from ..models.material import Material
from ..models.production_plan import ProductionPlan
from ..models.order import Order
from ..models.user import User
from ..models.quality import QualityRecord
from ..models.notification import NotificationRecord
from ..schemas.import_export import (
    ImportRequest, ExportRequest, ImportResponse, ExportResponse,
    FileUploadResponse, TemplateRequest
)
from ..core.exceptions import ValidationException, BusinessException
from ..core.auth import get_current_user
from ..core.celery_app import celery_app

router = APIRouter(prefix="/import-export", tags=["数据导入导出"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query("general", description="文件分类"),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件
    
    Args:
        file: 上传的文件
        category: 文件分类（general, import, export, template）
        current_user: 当前用户
        
    Returns:
        FileUploadResponse: 文件上传结果
    """
    try:
        # 上传文件
        file_info = await file_service.upload_file(
            file=file,
            category=category
        )
        
        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_id=file_info["file_id"],
            filename=file_info["filename"],
            file_url=file_info["file_url"],
            file_size=file_info["file_size"],
            file_type=file_info["file_type"]
        )
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import/{data_type}", response_model=ImportResponse)
async def import_data(
    data_type: str,
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入数据
    
    Args:
        data_type: 数据类型（progress, equipment, material, production_plan, order）
        request: 导入请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        ImportResponse: 导入结果
    """
    try:
        # 验证数据类型
        supported_types = [
            "progress", "equipment", "material", 
            "production_plan", "order", "user"
        ]
        
        if data_type not in supported_types:
            raise ValidationException(
                f"不支持的数据类型: {data_type}。"
                f"支持的类型: {', '.join(supported_types)}"
            )
        
        # 读取Excel文件
        df = file_service.read_excel(
            file_path=request.file_path,
            sheet_name=request.sheet_name,
            header_row=request.header_row or 0,
            max_rows=request.max_rows
        )
        
        # 应用字段映射
        if request.field_mapping:
            df = df.rename(columns=request.field_mapping)
        
        # 应用过滤条件
        if request.filters:
            for field, value in request.filters.items():
                if field in df.columns:
                    df = df[df[field] == value]
        
        # 数据验证和清理
        df = _clean_import_data(df, data_type)
        
        # 启动Celery后台任务处理数据
        from ..tasks.import_export_tasks import process_import_data_task
        
        task = process_import_data_task.delay(
            data_type=data_type,
            data=df.to_dict('records'),
            user_id=current_user.id
        )
        task_id = task.id
        
        return ImportResponse(
            success=True,
            message="数据导入任务已启动",
            task_id=task_id,
            total_rows=len(df),
            preview_data=df.head(5).to_dict('records')
        )
        
    except Exception as e:
        logger.error(f"数据导入失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/{data_type}", response_model=ExportResponse)
async def export_data(
    data_type: str,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出数据
    
    Args:
        data_type: 数据类型
        request: 导出请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        ExportResponse: 导出结果
    """
    try:
        # 验证数据类型
        supported_types = [
            "progress", "equipment", "material", 
            "production_plan", "order", "user"
        ]
        
        if data_type not in supported_types:
            raise ValidationException(
                f"不支持的数据类型: {data_type}。"
                f"支持的类型: {', '.join(supported_types)}"
            )
        
        # 启动Celery后台任务处理数据
        from ..tasks.import_export_tasks import process_export_data_task
        
        task = process_export_data_task.delay(
            data_type=data_type,
            request=request.dict(),
            user_id=current_user.id
        )
        task_id = task.id
        
        return ExportResponse(
            success=True,
            message="数据导出任务已启动",
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"数据导出失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/template/{data_type}")
async def download_template(
    data_type: str,
    format: str = Query("xlsx", description="文件格式"),
    current_user: User = Depends(get_current_user)
):
    """
    下载导入模板
    
    Args:
        data_type: 数据类型
        format: 文件格式
        current_user: 当前用户
        
    Returns:
        FileResponse: 模板文件
    """
    try:
        # 获取模板数据
        template_data = _get_template_data(data_type)
        
        # 生成模板文件
        filename = f"{data_type}_template.{format}"
        file_info = file_service.generate_export_file(
            data=template_data,
            filename=filename,
            file_format=format,
            style_config={
                'header_style': {
                    'font': {'bold': True, 'color': 'FFFFFF'},
                    'fill': {'start_color': '4472C4', 'end_color': '4472C4', 'fill_type': 'solid'},
                    'alignment': {'horizontal': 'center', 'vertical': 'center'}
                }
            }
        )
        
        return FileResponse(
            path=file_info["file_path"],
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"下载模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载文件
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        
    Returns:
        FileResponse: 文件
    """
    try:
        # 这里应该从数据库查询文件信息
        # 暂时使用简单的文件路径查找
        export_dir = file_service.export_dir
        
        for file_path in export_dir.iterdir():
            if file_id in file_path.name:
                return FileResponse(
                    path=str(file_path),
                    filename=file_path.name
                )
        
        raise HTTPException(status_code=404, detail="文件不存在")
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        current_user: 当前用户
        
    Returns:
        Dict: 任务状态
    """
    try:
        # 从Celery获取任务状态
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "任务等待处理",
                "result": None
            }
        elif task_result.state == 'PROGRESS':
            response = {
                "task_id": task_id,
                "status": "processing",
                "progress": task_result.info.get('progress', 0),
                "message": task_result.info.get('message', '任务处理中'),
                "result": task_result.info.get('result', None)
            }
        elif task_result.state == 'SUCCESS':
            response = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "message": "任务已完成",
                "result": task_result.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "status": "failed",
                "progress": 0,
                "message": str(task_result.info),
                "result": None
            }
        
        return response
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


def _clean_import_data(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """
    清理导入数据
    
    Args:
        df: 数据框
        data_type: 数据类型
        
    Returns:
        DataFrame: 清理后的数据
    """
    try:
        # 删除空行
        df = df.dropna(how='all')
        
        # 根据数据类型进行特定清理
        if data_type == "progress":
            # 进度数据清理
            required_columns = ['project_name', 'task_name', 'progress']
            for col in required_columns:
                if col not in df.columns:
                    raise ValidationException(f"缺少必需列: {col}")
            
            # 进度值验证
            if 'progress' in df.columns:
                df['progress'] = pd.to_numeric(df['progress'], errors='coerce')
                df = df[df['progress'].between(0, 100)]
        
        elif data_type == "equipment":
            # 设备数据清理
            required_columns = ['equipment_name', 'equipment_type']
            for col in required_columns:
                if col not in df.columns:
                    raise ValidationException(f"缺少必需列: {col}")
        
        elif data_type == "material":
            # 物料数据清理
            required_columns = ['material_name', 'material_code']
            for col in required_columns:
                if col not in df.columns:
                    raise ValidationException(f"缺少必需列: {col}")
        
        # 通用数据清理
        # 去除前后空格
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
        
        # 替换空字符串为None
        df = df.replace('', None)
        
        return df
        
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        raise BusinessException(f"数据清理失败: {str(e)}")


def _get_template_data(data_type: str) -> List[Dict[str, Any]]:
    """
    获取模板数据
    
    Args:
        data_type: 数据类型
        
    Returns:
        List: 模板数据
    """
    templates = {
        "progress": [
            {
                "项目名称": "示例项目",
                "任务名称": "示例任务",
                "进度(%)": 50,
                "开始时间": "2024-01-01",
                "结束时间": "2024-01-31",
                "负责人": "张三",
                "状态": "进行中",
                "备注": "示例备注"
            }
        ],
        "equipment": [
            {
                "设备名称": "示例设备",
                "设备编号": "EQ001",
                "设备类型": "生产设备",
                "状态": "正常",
                "产能": 100,
                "位置": "车间A",
                "负责人": "李四",
                "备注": "示例备注"
            }
        ],
        "material": [
            {
                "物料名称": "示例物料",
                "物料编号": "MAT001",
                "物料类型": "原材料",
                "单位": "kg",
                "库存数量": 1000,
                "安全库存": 100,
                "供应商": "供应商A",
                "备注": "示例备注"
            }
        ],
        "production_plan": [
            {
                "计划名称": "示例生产计划",
                "产品名称": "产品A",
                "计划数量": 1000,
                "开始时间": "2024-01-01",
                "结束时间": "2024-01-31",
                "优先级": "高",
                "状态": "计划中",
                "备注": "示例备注"
            }
        ],
        "order": [
            {
                "订单编号": "ORD001",
                "客户名称": "客户A",
                "产品名称": "产品A",
                "订单数量": 100,
                "交期": "2024-01-31",
                "状态": "待生产",
                "备注": "示例备注"
            }
        ],
        "user": [
            {
                "用户名": "user001",
                "姓名": "张三",
                "邮箱": "zhangsan@example.com",
                "电话": "13800138000",
                "部门": "生产部",
                "角色": "操作员",
                "状态": "激活"
            }
        ]
    }
    
    return templates.get(data_type, [])


async def _process_import_data(
    task_id: str,
    data_type: str,
    data: List[Dict[str, Any]],
    user_id: int,
    db: Session
):
    """
    处理导入数据（后台任务）
    
    Args:
        task_id: 任务ID
        data_type: 数据类型
        data: 数据
        user_id: 用户ID
        db: 数据库会话
    """
    try:
        logger.info(f"开始处理导入任务: {task_id}")
        
        success_count = 0
        error_count = 0
        
        for item in data:
            try:
                # 根据数据类型处理数据
                if data_type == "progress":
                    # 处理进度数据
                    pass
                elif data_type == "equipment":
                    # 处理设备数据
                    pass
                elif data_type == "material":
                    # 处理物料数据
                    pass
                # ... 其他数据类型
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"处理数据项失败: {e}")
                error_count += 1
        
        logger.info(
            f"导入任务完成: {task_id}, "
            f"成功: {success_count}, 失败: {error_count}"
        )
        
    except Exception as e:
        logger.error(f"处理导入任务失败: {task_id}, {e}")


async def _process_export_data(
    task_id: str,
    data_type: str,
    request: ExportRequest,
    user_id: int,
    db: Session
):
    """
    处理导出数据（后台任务）
    
    Args:
        task_id: 任务ID
        data_type: 数据类型
        request: 导出请求
        user_id: 用户ID
        db: 数据库会话
    """
    try:
        logger.info(f"开始处理导出任务: {task_id}")
        
        # 查询数据
        data = []
        
        if data_type == "progress":
            # 查询进度数据
            pass
        elif data_type == "equipment":
            # 查询设备数据
            pass
        elif data_type == "material":
            # 查询物料数据
            pass
        # ... 其他数据类型
        
        # 生成导出文件
        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_info = file_service.generate_export_file(
            data=data,
            filename=filename,
            file_format=request.format or "xlsx"
        )
        
        logger.info(f"导出任务完成: {task_id}, 文件: {file_info['filename']}")
        
    except Exception as e:
        logger.error(f"处理导出任务失败: {task_id}, {e}")