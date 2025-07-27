#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理API端点
提供前端获取统一配置的接口
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config import (
        get_settings_manager,
        get_settings,
        SettingsManager,
        ApplicationSettings
    )
except ImportError as e:
    print(f"警告: 无法导入统一配置管理中心: {e}")
    get_settings_manager = None
    get_settings = None
    SettingsManager = None
    ApplicationSettings = None

from app.core.config import settings as app_settings

router = APIRouter()


def get_config_manager() -> Optional[SettingsManager]:
    """获取配置管理器依赖"""
    if get_settings_manager:
        return get_settings_manager()
    return None


@router.get("/frontend", summary="获取前端配置")
async def get_frontend_config(
    config_manager: Optional[SettingsManager] = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取前端应用配置
    
    Returns:
        Dict[str, Any]: 前端配置信息
    """
    try:
        # 基础配置
        frontend_config = {
            "project_name": app_settings.PROJECT_NAME,
            "version": app_settings.VERSION,
            "description": app_settings.DESCRIPTION,
            "environment": app_settings.ENVIRONMENT,
            "debug": app_settings.DEBUG,
            
            # API配置
            "api_v1_prefix": app_settings.API_V1_STR,
            "host": app_settings.SERVER_HOST,
            "port": app_settings.SERVER_PORT,
            
            # 分页配置
            "default_page_size": app_settings.DEFAULT_PAGE_SIZE,
            "max_page_size": app_settings.MAX_PAGE_SIZE,
            
            # 文件上传配置
            "max_file_size": app_settings.MAX_FILE_SIZE,
            "allowed_file_types": app_settings.ALLOWED_EXTENSIONS,
            
            # CORS配置
            "cors_origins": app_settings.BACKEND_CORS_ORIGINS,
            
            # JWT配置（仅公开部分）
            "access_token_expire_minutes": app_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        }
        
        # 如果有统一配置管理器，使用统一配置
        if config_manager:
            unified_settings = get_settings()
            if unified_settings:
                frontend_config.update({
                    "project_name": unified_settings.project_name,
                    "version": unified_settings.version,
                    "description": unified_settings.description,
                    "environment": unified_settings.environment,
                    "debug": unified_settings.debug,
                    "api_v1_prefix": unified_settings.api_v1_prefix,
                    "host": unified_settings.host,
                    "port": unified_settings.port,
                    "default_page_size": unified_settings.default_page_size,
                    "max_page_size": unified_settings.max_page_size,
                    "max_file_size": unified_settings.max_file_size,
                    "allowed_file_types": unified_settings.allowed_file_types,
                    "cors_origins": unified_settings.cors_origins,
                    "access_token_expire_minutes": unified_settings.access_token_expire_minutes,
                })
        
        return frontend_config
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取前端配置失败: {str(e)}"
        )


@router.get("/backend", summary="获取后端配置")
async def get_backend_config(
    config_manager: Optional[SettingsManager] = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取后端应用配置（管理员接口）
    
    Returns:
        Dict[str, Any]: 后端配置信息
    """
    try:
        # 基础配置（不包含敏感信息）
        backend_config = {
            "project_name": app_settings.PROJECT_NAME,
            "version": app_settings.VERSION,
            "description": app_settings.DESCRIPTION,
            "environment": app_settings.ENVIRONMENT,
            "debug": app_settings.DEBUG,
            
            # 服务器配置
            "server": {
                "host": app_settings.SERVER_HOST,
                "port": app_settings.SERVER_PORT,
                "api_v1_prefix": app_settings.API_V1_STR,
            },
            
            # 数据库配置（不包含密码）
            "database": {
                "url_masked": app_settings.SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in app_settings.SQLALCHEMY_DATABASE_URI else "配置已隐藏",
                "pool_size": getattr(app_settings, 'DB_POOL_SIZE', 5),
                "max_overflow": getattr(app_settings, 'DB_MAX_OVERFLOW', 10),
            },
            
            # 文件配置
            "file": {
                "upload_dir": app_settings.UPLOAD_DIR,
                "max_file_size": app_settings.MAX_FILE_SIZE,
                "allowed_extensions": app_settings.ALLOWED_EXTENSIONS,
            },
            
            # 日志配置
            "logging": {
                "level": app_settings.LOG_LEVEL,
                "file": app_settings.LOG_FILE,
            },
            
            # 分页配置
            "pagination": {
                "default_page_size": app_settings.DEFAULT_PAGE_SIZE,
                "max_page_size": app_settings.MAX_PAGE_SIZE,
            },
            
            # CORS配置
            "cors": {
                "origins": app_settings.BACKEND_CORS_ORIGINS,
            },
            
            # JWT配置（不包含密钥）
            "jwt": {
                "algorithm": app_settings.ALGORITHM,
                "access_token_expire_minutes": app_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            },
            
            # Redis配置（不包含密码）
            "redis": {
                "url_masked": "配置已隐藏" if app_settings.REDIS_URL else "未配置",
            },
            
            # SMTP配置（不包含密码）
            "smtp": {
                "host": app_settings.SMTP_HOST or "未配置",
                "port": app_settings.SMTP_PORT,
                "use_tls": app_settings.SMTP_TLS,
                "from_email": app_settings.EMAILS_FROM_EMAIL or "未配置",
            },
        }
        
        # 如果有统一配置管理器，添加统一配置信息
        if config_manager:
            backend_config["unified_config"] = {
                "enabled": True,
                "config_file": str(config_manager.config_manager.config_file),
                "environment_manager": True,
                "path_manager": True,
                "validator": True,
            }
        else:
            backend_config["unified_config"] = {
                "enabled": False,
                "reason": "统一配置管理中心未加载",
            }
        
        return backend_config
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取后端配置失败: {str(e)}"
        )


@router.get("/health", summary="配置健康检查")
async def config_health_check(
    config_manager: Optional[SettingsManager] = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    配置系统健康检查
    
    Returns:
        Dict[str, Any]: 健康检查结果
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": None,
            "checks": {
                "app_settings": {
                    "status": "ok",
                    "details": "FastAPI配置正常"
                },
                "unified_config": {
                    "status": "ok" if config_manager else "warning",
                    "details": "统一配置管理中心正常" if config_manager else "统一配置管理中心未加载"
                },
                "database": {
                    "status": "ok" if app_settings.SQLALCHEMY_DATABASE_URI else "error",
                    "details": "数据库配置正常" if app_settings.SQLALCHEMY_DATABASE_URI else "数据库未配置"
                },
                "upload_dir": {
                    "status": "ok" if Path(app_settings.UPLOAD_DIR).exists() else "warning",
                    "details": "上传目录存在" if Path(app_settings.UPLOAD_DIR).exists() else "上传目录不存在"
                },
                "log_dir": {
                    "status": "ok" if Path(app_settings.LOG_FILE).parent.exists() else "warning",
                    "details": "日志目录存在" if Path(app_settings.LOG_FILE).parent.exists() else "日志目录不存在"
                }
            }
        }
        
        # 检查是否有错误
        has_errors = any(check["status"] == "error" for check in health_status["checks"].values())
        has_warnings = any(check["status"] == "warning" for check in health_status["checks"].values())
        
        if has_errors:
            health_status["status"] = "unhealthy"
        elif has_warnings:
            health_status["status"] = "degraded"
        
        # 添加时间戳
        from datetime import datetime
        health_status["timestamp"] = datetime.now().isoformat()
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "checks": {}
        }


@router.get("/validation", summary="配置验证")
async def validate_config(
    config_manager: Optional[SettingsManager] = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    验证当前配置
    
    Returns:
        Dict[str, Any]: 验证结果
    """
    try:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # 基础配置验证
        if not app_settings.PROJECT_NAME:
            validation_result["errors"].append("项目名称未配置")
        
        if not app_settings.SECRET_KEY or app_settings.SECRET_KEY == "your-secret-key-here-change-in-production":
            if app_settings.is_production():
                validation_result["errors"].append("生产环境必须设置安全的SECRET_KEY")
            else:
                validation_result["warnings"].append("使用默认SECRET_KEY，生产环境请更改")
        
        if not app_settings.SQLALCHEMY_DATABASE_URI:
            validation_result["errors"].append("数据库URL未配置")
        
        # 目录验证
        upload_path = Path(app_settings.UPLOAD_DIR)
        if not upload_path.exists():
            validation_result["warnings"].append(f"上传目录不存在: {app_settings.UPLOAD_DIR}")
        
        log_path = Path(app_settings.LOG_FILE).parent
        if not log_path.exists():
            validation_result["warnings"].append(f"日志目录不存在: {log_path}")
        
        # 生产环境特殊检查
        if app_settings.is_production():
            if app_settings.DEBUG:
                validation_result["errors"].append("生产环境不应启用调试模式")
            
            if app_settings.LOG_LEVEL == 'DEBUG':
                validation_result["warnings"].append("生产环境建议使用INFO或更高日志级别")
        
        # 统一配置验证
        if config_manager:
            try:
                unified_validation = config_manager.validate_config()
                if not unified_validation.get('valid', True):
                    validation_result["errors"].extend(unified_validation.get('errors', []))
                    validation_result["warnings"].extend(unified_validation.get('warnings', []))
                else:
                    validation_result["info"].append("统一配置验证通过")
            except Exception as e:
                validation_result["warnings"].append(f"统一配置验证失败: {str(e)}")
        else:
            validation_result["info"].append("统一配置管理中心未启用")
        
        # 设置总体验证状态
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置验证失败: {str(e)}"
        )


@router.get("/env-vars", summary="获取环境变量配置")
async def get_env_vars(
    config_manager: Optional[SettingsManager] = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    获取环境变量配置（用于生成.env文件）
    
    Returns:
        Dict[str, Any]: 环境变量配置
    """
    try:
        env_vars = {
            "backend": {
                "DATABASE_URL": "postgresql://user:password@localhost:5432/pmc_db",
                "SECRET_KEY": "your-secret-key-here",
                "ENVIRONMENT": "development",
                "DEBUG": "true",
                "LOG_LEVEL": "INFO",
                "REDIS_URL": "redis://localhost:6379/0",
                "SMTP_HOST": "",
                "SMTP_PORT": "587",
                "SMTP_USER": "",
                "SMTP_PASSWORD": "",
                "EMAILS_FROM_EMAIL": "",
            },
            "frontend": {
                "REACT_APP_API_BASE_URL": "http://localhost:8000",
                "REACT_APP_API_VERSION": "/api/v1",
                "REACT_APP_API_TIMEOUT": "30000",
                "REACT_APP_ENABLE_MOCK": "false",
                "REACT_APP_ENABLE_ANALYTICS": "false",
                "REACT_APP_PRIMARY_COLOR": "#1890ff",
                "REACT_APP_LAYOUT": "side",
                "REACT_APP_PAGE_SIZE": "20",
                "REACT_APP_MAX_FILE_SIZE": "10485760",
            }
        }
        
        # 如果有统一配置管理器，使用统一配置生成环境变量
        if config_manager:
            try:
                backend_env = config_manager.export_env_vars()
                frontend_env = config_manager.export_frontend_env_vars()
                
                env_vars["backend"].update(backend_env)
                env_vars["frontend"].update(frontend_env)
                
                env_vars["unified_config"] = True
            except Exception as e:
                env_vars["unified_config_error"] = str(e)
        
        return env_vars
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取环境变量配置失败: {str(e)}"
        )