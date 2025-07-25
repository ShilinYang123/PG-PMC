#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理中心
负责管理项目的所有配置信息，包括前端、后端、数据库、日志等配置
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class DatabaseConfig:
    """数据库配置"""
    sqlite_url: str = "sqlite:///./pmc.db"
    host: str = "localhost"
    port: int = 5432
    name: str = "pmc_db"
    username: str = "postgres"
    user: str = "postgres"  # 兼容现有配置中的user字段
    password: str = "password"
    database: str = "pmc_db"
    test_database: str = "pmc_test_db"
    dev_database: str = "pmc_dev_db"
    dev_name: str = "pmc_dev_db"
    test_name: str = "pmc_test_db"
    pool_size: int = 10
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_idle_timeout: int = 30000
    pool_max: int = 10
    pool_min: int = 2
    url_template: str = "postgresql://{username}:{password}@{host}:{port}/{database_name}"
    # 兼容现有配置文件中的字段，但不定义为字段，而是通过__post_init__处理
    _url: str = field(default="", init=False)
    _test_url: str = field(default="", init=False)
    
    def __post_init__(self):
        # 处理从配置文件传入的url和test_url字段
        pass
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def test_url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.test_database}"


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "localhost"
    port: int = 8000
    frontend_port: int = 3000
    debug: bool = True
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list = None
    api_port: int = 8000
    api_url: str = "http://localhost:8000/api"
    name: str = "PMC系统"
    url: str = "http://localhost:3000"
    version: str = "1.0.0"
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = [
                f"http://localhost:{self.frontend_port}",
                f"http://127.0.0.1:{self.frontend_port}"
            ]


@dataclass
class SecurityConfig:
    """安全配置"""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = "your-32-character-encryption-key"
    # 兼容现有配置文件中的字段
    cors_credentials: bool = True
    cors_origin: str = "http://localhost:3000"
    jwt_expires_in: str = "7d"
    jwt_refresh_expires_in: str = "30d"
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    session_max_age: int = 86400000
    session_secret: str = "your-session-secret-key-change-this"


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/pmc.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    rotation: str = "daily"
    # 兼容现有配置文件中的字段
    compress: bool = True
    date_pattern: str = "YYYY-MM-DD"
    dir: str = "./logs"
    max_files: int = 5
    max_size: str = "10m"


@dataclass
class FileConfig:
    """文件配置"""
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".xlsx", ".xls", ".csv"]


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    session_db: int = 1
    # 兼容现有配置文件中的字段，但不定义为字段
    _url: str = field(default="", init=False)
    
    def __post_init__(self):
        # 处理从配置文件传入的url字段
        pass
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class ConfigManager:
    """统一配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.project_root = Path(os.getenv('PG_PMC_ROOT', 's:/PG-PMC'))
        self.config_file = config_file or self.project_root / 'docs/03-管理/project_config.yaml'
        self._config_data = {}
        self._load_config()
        
        # 初始化各模块配置
        db_config = self._get_section('database', {})
        # 过滤掉url和test_url字段，因为它们是属性而不是字段
        db_config = {k: v for k, v in db_config.items() if k not in ['url', 'test_url']}
        self.database = DatabaseConfig(**db_config)
        self.server = ServerConfig(**self._get_section('server', {}))
        self.security = SecurityConfig(**self._get_section('security', {}))
        self.logging = LoggingConfig(**self._get_section('logging', {}))
        self.file = FileConfig(**self._get_section('file', {}))
        redis_config = self._get_section('redis', {})
        # 过滤掉url字段，因为它是属性而不是字段
        redis_config = {k: v for k, v in redis_config.items() if k not in ['url']}
        self.redis = RedisConfig(**redis_config)
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # 兼容现有配置格式
                    self._config_data = self._normalize_config(config)
            else:
                self._config_data = self._get_default_config()
                self.save_config()
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            self._config_data = self._get_default_config()
    
    def _get_section(self, section: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置段"""
        return self._config_data.get(section, default)
    
    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化配置格式，兼容现有配置"""
        normalized = {}
        
        # 项目信息
        if "project" in config:
            normalized["project"] = config["project"]
        else:
            normalized["project"] = {
                "name": config.get("project_name", "PG-PMC"),
                "version": config.get("project_version", "1.0.0"),
                "description": config.get("project_description", "3AI电器实业有限公司研发管理项目")
            }
        
        # 应用配置
        if "server" in config:
            normalized["server"] = config["server"]
        elif "app" in config:
            app_config = config["app"]
            normalized["server"] = {
                "host": "localhost",
                "port": app_config.get("api_port", 8000),
                "frontend_port": 3000,
                "debug": True,
                "cors_origins": None
            }
        
        # 数据库配置
        if "database" in config:
            normalized["database"] = config["database"]
        
        # 环境配置
        if "environment" in config:
            env_config = config["environment"]
            if "database" in env_config:
                normalized.setdefault("database", {}).update(env_config["database"])
            if "app" in env_config:
                normalized.setdefault("server", {}).update(env_config["app"])
        
        # 路径配置
        if "paths" in config:
            normalized["paths"] = config["paths"]
        
        # 日志配置
        if "logging" in config:
            normalized["logging"] = config["logging"]
        
        # 安全配置
        if "environment" in config and "security" in config["environment"]:
            normalized["security"] = config["environment"]["security"]
        
        # Redis配置
        if "environment" in config and "redis" in config["environment"]:
            normalized["redis"] = config["environment"]["redis"]
        
        # 文件配置
        if "environment" in config and "storage" in config["environment"]:
            storage = config["environment"]["storage"]
            normalized["file"] = {
                "upload_dir": storage.get("upload_dir", "uploads"),
                "max_file_size": storage.get("max_file_size", 10485760),
                "allowed_extensions": storage.get("allowed_file_types", "").split(",") if storage.get("allowed_file_types") else []
            }
        
        return normalized
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'project': {
                'name': 'PG-PMC',
                'version': '1.0.0',
                'description': '3AI电器实业有限公司研发管理项目',
                'root': str(self.project_root),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            },
            'database': asdict(DatabaseConfig()),
            'server': asdict(ServerConfig()),
            'security': asdict(SecurityConfig()),
            'logging': asdict(LoggingConfig()),
            'file': asdict(FileConfig()),
            'redis': asdict(RedisConfig()),
            'paths': {
                'root': str(self.project_root),
                'docs_dir': str(self.project_root / 'docs'),
                'logs_dir': str(self.project_root / 'logs'),
                'tools_dir': str(self.project_root / 'tools'),
                'project_dir': str(self.project_root / 'project'),
                'backup_dir': str(self.project_root / 'bak')
            },
            'environment': {
                'name': 'development',
                'debug': True,
                'testing': False
            }
        }
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """获取配置数据"""
        if section:
            return self._config_data.get(section, {})
        return self._config_data.copy()
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self._config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._config_data['project']['updated_at'] = datetime.now().isoformat()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性"""
        errors = []
        warnings = []
        
        # 检查必需的配置项
        required_sections = ['project', 'database', 'server', 'security', 'logging']
        for section in required_sections:
            if section not in self._config_data:
                errors.append(f"缺少必需的配置段: {section}")
        
        # 检查路径是否存在
        paths = self.get('paths', {})
        for path_name, path_value in paths.items():
            if path_value and not Path(path_value).exists():
                warnings.append(f"路径不存在: {path_name} = {path_value}")
        
        # 检查安全配置
        if self.security.secret_key == "your-secret-key-change-in-production":
            warnings.append("使用默认密钥，生产环境请更改")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_env_vars(self) -> Dict[str, str]:
        """获取环境变量格式的配置"""
        env_vars = {}
        
        # 数据库配置
        env_vars.update({
            'DATABASE_URL': self.database.url,
            'DATABASE_HOST': self.database.host,
            'DATABASE_PORT': str(self.database.port),
            'DATABASE_USER': self.database.username,
            'DATABASE_PASSWORD': self.database.password,
            'DATABASE_NAME': self.database.database
        })
        
        # 服务器配置
        env_vars.update({
            'SERVER_HOST': self.server.host,
            'SERVER_PORT': str(self.server.port),
            'FRONTEND_PORT': str(self.server.frontend_port),
            'DEBUG': str(self.server.debug).lower()
        })
        
        # 安全配置
        env_vars.update({
            'SECRET_KEY': self.security.secret_key,
            'ALGORITHM': self.security.algorithm,
            'ACCESS_TOKEN_EXPIRE_MINUTES': str(self.security.access_token_expire_minutes)
        })
        
        # Redis配置
        env_vars.update({
            'REDIS_URL': self.redis.url,
            'REDIS_HOST': self.redis.host,
            'REDIS_PORT': str(self.redis.port)
        })
        
        return env_vars
    
    def export_frontend_config(self) -> Dict[str, Any]:
        """导出前端配置"""
        return {
            'API_BASE_URL': f"http://{self.server.host}:{self.server.port}/api/v1",
            'APP_NAME': self.get('project.name'),
            'APP_VERSION': self.get('project.version'),
            'DEBUG': self.server.debug,
            'UPLOAD_MAX_SIZE': self.file.max_file_size,
            'ALLOWED_FILE_TYPES': self.file.allowed_extensions
        }
    
    def export_backend_config(self) -> Dict[str, Any]:
        """导出后端配置"""
        return {
            'PROJECT_NAME': self.get('project.name'),
            'VERSION': self.get('project.version'),
            'API_V1_STR': '/api/v1',
            'SERVER_HOST': self.server.host,
            'SERVER_PORT': self.server.port,
            'DATABASE_URL': self.database.url,
            'SECRET_KEY': self.security.secret_key,
            'ALGORITHM': self.security.algorithm,
            'ACCESS_TOKEN_EXPIRE_MINUTES': self.security.access_token_expire_minutes,
            'CORS_ORIGINS': self.server.cors_origins,
            'UPLOAD_DIR': self.file.upload_dir,
            'MAX_FILE_SIZE': self.file.max_file_size,
            'LOG_LEVEL': self.logging.level,
            'REDIS_URL': self.redis.url
        }


# 全局配置管理器实例
config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager

def load_project_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """加载项目配置文件"""
    manager = ConfigManager(config_file)
    return manager._config_data

def save_project_config(config_data: Dict[str, Any], config_file: Optional[str] = None):
    """保存项目配置文件"""
    manager = ConfigManager(config_file)
    manager._config_data = config_data
    manager.save_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_manager.get_config_value(key, default)

def set_config_value(key: str, value: Any):
    """设置配置值"""
    config_manager.set_config_value(key, value)


def get_config() -> ConfigManager:
    """获取配置管理器实例"""
    return config_manager


def reload_config() -> None:
    """重新加载配置"""
    global config_manager
    config_manager = ConfigManager()


if __name__ == '__main__':
    # 测试配置管理器
    config = get_config()
    
    print("配置验证结果:")
    validation = config.validate_config()
    print(f"有效: {validation['valid']}")
    
    if validation['errors']:
        print("错误:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print("\n数据库URL:", config.database.url)
    print("服务器配置:", f"{config.server.host}:{config.server.port}")
    print("前端配置:", config.export_frontend_config())