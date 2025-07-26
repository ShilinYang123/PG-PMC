#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端应用配置
集成统一配置管理中心，提供FastAPI应用的配置支持
"""

from typing import List, Union, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config import (
        get_settings_manager,
        get_settings,
        get_database_url,
        get_redis_url,
        get_secret_key,
        is_debug,
        is_development,
        is_production
    )
    
    # 获取统一配置
    unified_settings = get_settings()
    settings_manager = get_settings_manager()
    
except ImportError as e:
    print(f"警告: 无法导入统一配置管理中心: {e}")
    print("使用默认配置...")
    unified_settings = None
    settings_manager = None


class Settings(BaseSettings):
    """FastAPI应用配置"""
    
    def __init__(self, **kwargs):
        # 如果有统一配置，使用统一配置的值
        if unified_settings:
            kwargs.setdefault('PROJECT_NAME', unified_settings.project_name)
            kwargs.setdefault('VERSION', unified_settings.version)
            kwargs.setdefault('DESCRIPTION', unified_settings.description)
            kwargs.setdefault('API_V1_STR', unified_settings.api_v1_prefix)
            kwargs.setdefault('SERVER_HOST', unified_settings.host)
            kwargs.setdefault('SERVER_PORT', unified_settings.port)
            kwargs.setdefault('DATABASE_URL', unified_settings.database_url)
            kwargs.setdefault('REDIS_URL', unified_settings.redis_url)
            kwargs.setdefault('SECRET_KEY', unified_settings.secret_key)
            kwargs.setdefault('UPLOAD_DIR', unified_settings.upload_dir)
            kwargs.setdefault('MAX_FILE_SIZE', unified_settings.max_file_size)
            kwargs.setdefault('LOG_LEVEL', unified_settings.log_level)
            kwargs.setdefault('LOG_FILE', unified_settings.log_file)
            kwargs.setdefault('DEFAULT_PAGE_SIZE', unified_settings.default_page_size)
            kwargs.setdefault('MAX_PAGE_SIZE', unified_settings.max_page_size)
            kwargs.setdefault('ENVIRONMENT', unified_settings.environment)
            kwargs.setdefault('DEBUG', unified_settings.debug)
            kwargs.setdefault('BACKEND_CORS_ORIGINS', unified_settings.cors_origins)
            kwargs.setdefault('ACCESS_TOKEN_EXPIRE_MINUTES', unified_settings.access_token_expire_minutes)
            kwargs.setdefault('ALLOWED_EXTENSIONS', unified_settings.allowed_file_types)
            
            # SMTP配置
            smtp_config = settings_manager.get_smtp_config() if settings_manager else {}
            kwargs.setdefault('SMTP_HOST', smtp_config.get('server', ''))
            kwargs.setdefault('SMTP_PORT', smtp_config.get('port', 587))
            kwargs.setdefault('SMTP_USER', smtp_config.get('username', ''))
            kwargs.setdefault('SMTP_PASSWORD', smtp_config.get('password', ''))
            kwargs.setdefault('SMTP_TLS', smtp_config.get('use_tls', True))
        
        super().__init__(**kwargs)
    
    # 项目基本信息
    PROJECT_NAME: str = "PMC全流程管理系统"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "PMC全流程管理系统后端API"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/pmc_db"
    
    # 如果使用SQLite（开发环境）
    SQLITE_URL: str = "sqlite:///./pmc.db"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """获取数据库URI"""
        if unified_settings and unified_settings.database_url:
            return unified_settings.database_url
        elif is_development() if unified_settings else self.ENVIRONMENT == "development":
            return self.SQLITE_URL
        else:
            return self.DATABASE_URL
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".xlsx", ".xls", ".csv"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/pmc.log"
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    
    @property
    def EMAILS_FROM_NAME(self) -> str:
        """发件人名称"""
        return self.PROJECT_NAME
    
    # 环境配置
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # 安全配置
    BCRYPT_ROUNDS: int = 12
    
    # 缓存配置
    CACHE_TIMEOUT: int = 300  # 5分钟
    SESSION_TIMEOUT: int = 3600  # 1小时
    CACHE_TTL: int = 3600  # 缓存过期时间（秒）
    CACHE_MAX_SIZE: int = 1000  # 缓存最大条目数
    
    # 中间件配置
    ENABLE_AUTH: bool = True  # 启用认证中间件
    ENABLE_RATE_LIMIT: bool = True  # 启用速率限制
    RATE_LIMIT_CALLS: int = 100  # 速率限制调用次数
    RATE_LIMIT_PERIOD: int = 60  # 速率限制时间窗口（秒）
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # 优先级：环境变量 > 统一配置 > 默认值
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    def get_database_config(self) -> dict:
        """获取数据库配置"""
        return {
            'url': self.SQLALCHEMY_DATABASE_URI,
            'pool_size': self.DB_POOL_SIZE,
            'max_overflow': self.DB_MAX_OVERFLOW,
            'pool_timeout': self.DB_POOL_TIMEOUT,
            'pool_recycle': self.DB_POOL_RECYCLE
        }
    
    def get_redis_config(self) -> dict:
        """获取Redis配置"""
        return {
            'url': self.REDIS_URL,
            'timeout': self.CACHE_TIMEOUT
        }
    
    def get_cors_config(self) -> dict:
        """获取CORS配置"""
        return {
            'allow_origins': self.BACKEND_CORS_ORIGINS,
            'allow_credentials': True,
            'allow_methods': ["*"],
            'allow_headers': ["*"]
        }
    
    def get_upload_config(self) -> dict:
        """获取文件上传配置"""
        return {
            'upload_dir': self.UPLOAD_DIR,
            'max_file_size': self.MAX_FILE_SIZE,
            'allowed_extensions': self.ALLOWED_EXTENSIONS
        }
    
    def get_jwt_config(self) -> dict:
        """获取JWT配置"""
        return {
            'secret_key': self.SECRET_KEY,
            'algorithm': self.ALGORITHM,
            'access_token_expire_minutes': self.ACCESS_TOKEN_EXPIRE_MINUTES
        }
    
    def get_smtp_config(self) -> dict:
        """获取SMTP配置"""
        return {
            'host': self.SMTP_HOST,
            'port': self.SMTP_PORT,
            'username': self.SMTP_USER,
            'password': self.SMTP_PASSWORD,
            'use_tls': self.SMTP_TLS,
            'from_email': self.EMAILS_FROM_EMAIL,
            'from_name': self.EMAILS_FROM_NAME
        }
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT.lower() in ['development', 'dev', 'local']
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT.lower() in ['production', 'prod']
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT.lower() in ['testing', 'test']


# 创建配置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.UPLOAD_DIR,
        Path(settings.LOG_FILE).parent,
        "static",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# 初始化目录
ensure_directories()

# 配置验证
def validate_config():
    """验证配置"""
    errors = []
    warnings = []
    
    # 检查必需配置
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here-change-in-production":
        if settings.is_production():
            errors.append("生产环境必须设置安全的SECRET_KEY")
        else:
            warnings.append("使用默认SECRET_KEY，生产环境请更改")
    
    if not settings.SQLALCHEMY_DATABASE_URI:
        errors.append("数据库URL未配置")
    
    # 检查上传目录
    upload_path = Path(settings.UPLOAD_DIR)
    if not upload_path.exists():
        warnings.append(f"上传目录不存在，将自动创建: {settings.UPLOAD_DIR}")
        upload_path.mkdir(parents=True, exist_ok=True)
    
    # 生产环境特殊检查
    if settings.is_production():
        if settings.DEBUG:
            errors.append("生产环境不应启用调试模式")
        
        if settings.LOG_LEVEL == 'DEBUG':
            warnings.append("生产环境建议使用INFO或更高日志级别")
    
    return {'errors': errors, 'warnings': warnings}

# 执行配置验证
validation_result = validate_config()
if validation_result['errors']:
    print("配置错误:")
    for error in validation_result['errors']:
        print(f"  - {error}")

if validation_result['warnings']:
    print("配置警告:")
    for warning in validation_result['warnings']:
        print(f"  - {warning}")

# 导出常用配置函数
def get_database_url() -> str:
    """获取数据库URL"""
    return settings.SQLALCHEMY_DATABASE_URI

def get_redis_url() -> str:
    """获取Redis URL"""
    return settings.REDIS_URL

def get_secret_key() -> str:
    """获取密钥"""
    return settings.SECRET_KEY

def is_debug() -> bool:
    """是否为调试模式"""
    return settings.DEBUG