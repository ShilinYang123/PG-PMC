#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置管理器
整合配置管理器、环境管理器和路径管理器，提供统一的配置接口
"""

import os
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import yaml
import json
from dataclasses import dataclass, field

from .config_manager import ConfigManager, get_config_manager
from .environment import EnvironmentManager, Environment, get_environment_manager
from .path_manager import PathManager, get_path_manager
from .validator import ConfigValidator, DefaultConfigProvider


@dataclass
class ApplicationSettings:
    """应用程序设置"""
    # 基本信息
    project_name: str = "PG-PMC"
    version: str = "1.0.0"
    description: str = "生产管理控制系统"
    
    # 环境配置
    environment: str = "development"
    debug: bool = True
    
    # 服务器配置
    host: str = "localhost"
    port: int = 8000
    reload: bool = True
    
    # 数据库配置
    database_url: str = ""
    database_echo: bool = False
    
    # Redis配置
    redis_url: str = ""
    
    # 安全配置
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    
    # CORS配置
    cors_origins: List[str] = field(default_factory=list)
    
    # 文件配置
    upload_dir: str = ""
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = field(default_factory=lambda: [
        '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx'
    ])
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = ""
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # 缓存配置
    cache_timeout: int = 300  # 5分钟
    session_timeout: int = 3600  # 1小时
    
    # API配置
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # 邮件配置
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    
    # 分页配置
    default_page_size: int = 20
    max_page_size: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result


class SettingsManager:
    """设置管理器"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        # 初始化各个管理器
        self.config_manager = get_config_manager()
        self.env_manager = get_environment_manager()
        self.path_manager = get_path_manager()
        
        # 配置验证器
        self.validator = ConfigValidator()
        self.default_provider = DefaultConfigProvider()
        
        # 应用程序设置
        self.app_settings = ApplicationSettings()
        
        # 配置文件路径
        self.config_file = Path(config_file) if config_file else self.path_manager.get_path('docs_management') / 'project_config.yaml'
        
        # 加载配置
        self._load_configurations()
    
    def _load_configurations(self):
        """加载所有配置"""
        try:
            # 1. 加载主配置文件
            if self.config_file and self.config_file.exists():
                # ConfigManager在初始化时已经加载了配置文件
                pass
            
            # 2. 加载环境配置
            self._load_environment_config()
            
            # 3. 加载应用程序设置
            self._load_app_settings()
            
            # 4. 加载环境变量覆盖
            self._load_env_overrides()
            
        except Exception as e:
            print(f"加载配置时出错: {e}")
            # 使用默认配置
            self._load_default_config()
    
    def _load_environment_config(self):
        """加载环境配置"""
        current_env = self.env_manager.get_current_environment()
        env_config = self.env_manager.get_current_config()
        
        # 更新应用程序设置
        self.app_settings.environment = env_config.name
        self.app_settings.debug = env_config.debug
        self.app_settings.database_url = env_config.database_url
        self.app_settings.redis_url = env_config.redis_url
        self.app_settings.secret_key = env_config.secret_key
        self.app_settings.cors_origins = env_config.cors_origins
        self.app_settings.upload_dir = env_config.upload_dir
        self.app_settings.max_file_size = env_config.max_file_size
        self.app_settings.log_level = env_config.log_level
        self.app_settings.cache_timeout = env_config.cache_timeout
        self.app_settings.session_timeout = env_config.session_timeout
    
    def _load_app_settings(self):
        """加载应用程序设置"""
        config_data = self.config_manager.get_config()
        
        if 'application' in config_data:
            app_config = config_data['application']
            
            # 更新基本信息
            if 'project_info' in app_config:
                project_info = app_config['project_info']
                self.app_settings.project_name = project_info.get('name', self.app_settings.project_name)
                self.app_settings.version = project_info.get('version', self.app_settings.version)
                self.app_settings.description = project_info.get('description', self.app_settings.description)
            
            # 更新服务器配置
            if 'server' in app_config:
                server_config = app_config['server']
                self.app_settings.host = server_config.get('host', self.app_settings.host)
                self.app_settings.port = server_config.get('port', self.app_settings.port)
                self.app_settings.reload = server_config.get('reload', self.app_settings.reload)
            
            # 更新API配置
            if 'api' in app_config:
                api_config = app_config['api']
                self.app_settings.api_v1_prefix = api_config.get('v1_prefix', self.app_settings.api_v1_prefix)
                self.app_settings.docs_url = api_config.get('docs_url', self.app_settings.docs_url)
                self.app_settings.redoc_url = api_config.get('redoc_url', self.app_settings.redoc_url)
            
            # 更新分页配置
            if 'pagination' in app_config:
                pagination_config = app_config['pagination']
                self.app_settings.default_page_size = pagination_config.get('default_size', self.app_settings.default_page_size)
                self.app_settings.max_page_size = pagination_config.get('max_size', self.app_settings.max_page_size)
        
        # 更新路径配置
        self.app_settings.log_file = str(self.path_manager.get_path('logs') / 'app.log')
        
        # 如果上传目录为空，使用默认路径
        if not self.app_settings.upload_dir:
            self.app_settings.upload_dir = str(self.path_manager.get_path('uploads'))
    
    def _load_env_overrides(self):
        """加载环境变量覆盖"""
        # 环境变量映射
        env_mappings = {
            'PG_PMC_PROJECT_NAME': 'project_name',
            'PG_PMC_VERSION': 'version',
            'PG_PMC_HOST': 'host',
            'PG_PMC_PORT': 'port',
            'DATABASE_URL': 'database_url',
            'REDIS_URL': 'redis_url',
            'SECRET_KEY': 'secret_key',
            'LOG_LEVEL': 'log_level',
            'UPLOAD_DIR': 'upload_dir',
            'MAX_FILE_SIZE': 'max_file_size',
            'API_V1_PREFIX': 'api_v1_prefix',
            'DEFAULT_PAGE_SIZE': 'default_page_size',
            'MAX_PAGE_SIZE': 'max_page_size',
            'SMTP_SERVER': 'smtp_server',
            'SMTP_PORT': 'smtp_port',
            'SMTP_USERNAME': 'smtp_username',
            'SMTP_PASSWORD': 'smtp_password'
        }
        
        for env_var, setting_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # 类型转换
                if setting_key in ['port', 'max_file_size', 'default_page_size', 'max_page_size', 'smtp_port']:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                elif setting_key in ['debug', 'reload', 'database_echo', 'smtp_use_tls']:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                
                setattr(self.app_settings, setting_key, env_value)
        
        # 处理CORS源
        cors_origins = os.getenv('CORS_ORIGINS')
        if cors_origins:
            self.app_settings.cors_origins = [origin.strip() for origin in cors_origins.split(',')]
        
        # 处理允许的文件类型
        allowed_types = os.getenv('ALLOWED_FILE_TYPES')
        if allowed_types:
            self.app_settings.allowed_file_types = [ext.strip() for ext in allowed_types.split(',')]
    
    def _load_default_config(self):
        """加载默认配置"""
        current_env = self.env_manager.get_current_environment()
        default_config = self.default_provider.get_default_config(current_env)
        
        # 应用默认配置
        self.config_manager.config = default_config
        self._load_app_settings()
    
    def get_settings(self) -> ApplicationSettings:
        """获取应用程序设置"""
        return self.app_settings
    
    def get_database_url(self) -> str:
        """获取数据库URL"""
        return self.app_settings.database_url
    
    def get_redis_url(self) -> str:
        """获取Redis URL"""
        return self.app_settings.redis_url
    
    def get_secret_key(self) -> str:
        """获取密钥"""
        return self.app_settings.secret_key
    
    def get_cors_origins(self) -> List[str]:
        """获取CORS源"""
        return self.app_settings.cors_origins
    
    def get_upload_dir(self) -> str:
        """获取上传目录"""
        return self.app_settings.upload_dir
    
    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            'level': self.app_settings.log_level,
            'file': self.app_settings.log_file,
            'max_size': self.app_settings.log_max_size,
            'backup_count': self.app_settings.log_backup_count
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return {
            'host': self.app_settings.host,
            'port': self.app_settings.port,
            'reload': self.app_settings.reload,
            'debug': self.app_settings.debug
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return {
            'v1_prefix': self.app_settings.api_v1_prefix,
            'docs_url': self.app_settings.docs_url,
            'redoc_url': self.app_settings.redoc_url
        }
    
    def get_file_config(self) -> Dict[str, Any]:
        """获取文件配置"""
        return {
            'upload_dir': self.app_settings.upload_dir,
            'max_size': self.app_settings.max_file_size,
            'allowed_types': self.app_settings.allowed_file_types
        }
    
    def get_pagination_config(self) -> Dict[str, Any]:
        """获取分页配置"""
        return {
            'default_size': self.app_settings.default_page_size,
            'max_size': self.app_settings.max_page_size
        }
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """获取SMTP配置"""
        return {
            'server': self.app_settings.smtp_server,
            'port': self.app_settings.smtp_port,
            'username': self.app_settings.smtp_username,
            'password': self.app_settings.smtp_password,
            'use_tls': self.app_settings.smtp_use_tls
        }
    
    def is_debug(self) -> bool:
        """是否为调试模式"""
        return self.app_settings.debug
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.app_settings.environment == 'development'
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.app_settings.environment == 'production'
    
    def validate_settings(self) -> Dict[str, List[str]]:
        """验证设置"""
        errors = []
        warnings = []
        
        # 验证必需设置
        if not self.app_settings.secret_key:
            errors.append("SECRET_KEY未设置")
        elif len(self.app_settings.secret_key) < 32:
            warnings.append("SECRET_KEY长度建议至少32个字符")
        
        if not self.app_settings.database_url:
            errors.append("数据库URL未设置")
        
        # 验证端口
        if not (1 <= self.app_settings.port <= 65535):
            errors.append(f"无效的端口号: {self.app_settings.port}")
        
        # 验证上传目录
        upload_path = Path(self.app_settings.upload_dir)
        if not upload_path.exists():
            warnings.append(f"上传目录不存在: {self.app_settings.upload_dir}")
        
        # 验证日志文件目录
        log_path = Path(self.app_settings.log_file)
        if not log_path.parent.exists():
            warnings.append(f"日志目录不存在: {log_path.parent}")
        
        # 生产环境特殊检查
        if self.is_production():
            if self.app_settings.debug:
                errors.append("生产环境不应启用调试模式")
            
            if self.app_settings.log_level == 'DEBUG':
                warnings.append("生产环境建议使用INFO或更高日志级别")
            
            if not self.app_settings.cors_origins:
                warnings.append("生产环境应配置CORS源")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def export_env_vars(self) -> Dict[str, str]:
        """导出环境变量"""
        env_vars = {}
        
        # 基本配置
        env_vars['PG_PMC_PROJECT_NAME'] = self.app_settings.project_name
        env_vars['PG_PMC_VERSION'] = self.app_settings.version
        env_vars['PG_PMC_ENV'] = self.app_settings.environment
        env_vars['DEBUG'] = str(self.app_settings.debug).lower()
        
        # 服务器配置
        env_vars['PG_PMC_HOST'] = self.app_settings.host
        env_vars['PG_PMC_PORT'] = str(self.app_settings.port)
        
        # 数据库和缓存
        env_vars['DATABASE_URL'] = self.app_settings.database_url
        env_vars['REDIS_URL'] = self.app_settings.redis_url
        
        # 安全配置
        env_vars['SECRET_KEY'] = self.app_settings.secret_key
        
        # 文件配置
        env_vars['UPLOAD_DIR'] = self.app_settings.upload_dir
        env_vars['MAX_FILE_SIZE'] = str(self.app_settings.max_file_size)
        
        # 日志配置
        env_vars['LOG_LEVEL'] = self.app_settings.log_level
        env_vars['LOG_FILE'] = self.app_settings.log_file
        
        # API配置
        env_vars['API_V1_PREFIX'] = self.app_settings.api_v1_prefix
        
        # 其他配置
        env_vars['CORS_ORIGINS'] = ','.join(self.app_settings.cors_origins)
        env_vars['DEFAULT_PAGE_SIZE'] = str(self.app_settings.default_page_size)
        
        # 合并路径管理器的环境变量
        env_vars.update(self.path_manager.export_env_vars())
        
        return env_vars
    
    def save_config(self, file_path: Optional[Union[str, Path]] = None):
        """保存配置到文件"""
        file_path = Path(file_path) if file_path else self.config_file
        
        # 构建完整配置
        full_config = {
            'application': {
                'project_info': {
                    'name': self.app_settings.project_name,
                    'version': self.app_settings.version,
                    'description': self.app_settings.description
                },
                'server': {
                    'host': self.app_settings.host,
                    'port': self.app_settings.port,
                    'reload': self.app_settings.reload
                },
                'api': {
                    'v1_prefix': self.app_settings.api_v1_prefix,
                    'docs_url': self.app_settings.docs_url,
                    'redoc_url': self.app_settings.redoc_url
                },
                'pagination': {
                    'default_size': self.app_settings.default_page_size,
                    'max_size': self.app_settings.max_page_size
                }
            }
        }
        
        # 合并现有配置
        existing_config = self.config_manager.get_config()
        full_config.update(existing_config)
        
        # 保存配置
        self.config_manager.config = full_config
        self.config_manager.save_config(file_path)
    
    def reload_config(self):
        """重新加载配置"""
        self._load_configurations()
    
    def create_env_file(self, env_file: Union[str, Path]):
        """创建.env文件"""
        env_vars = self.export_env_vars()
        env_file = Path(env_file)
        
        # 确保目录存在
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"# PG-PMC 环境配置文件\n")
            f.write(f"# 环境: {self.app_settings.environment}\n")
            f.write(f"# 项目: {self.app_settings.project_name} v{self.app_settings.version}\n\n")
            
            # 按类别组织环境变量
            categories = {
                '基本配置': ['PG_PMC_PROJECT_NAME', 'PG_PMC_VERSION', 'PG_PMC_ENV', 'DEBUG'],
                '服务器配置': ['PG_PMC_HOST', 'PG_PMC_PORT'],
                '数据库配置': ['DATABASE_URL', 'REDIS_URL'],
                '安全配置': ['SECRET_KEY'],
                '文件配置': ['UPLOAD_DIR', 'MAX_FILE_SIZE'],
                '日志配置': ['LOG_LEVEL', 'LOG_FILE'],
                'API配置': ['API_V1_PREFIX', 'CORS_ORIGINS'],
                '路径配置': [k for k in env_vars.keys() if k.startswith('PG_PMC_') and k not in [
                    'PG_PMC_PROJECT_NAME', 'PG_PMC_VERSION', 'PG_PMC_ENV', 'PG_PMC_HOST', 'PG_PMC_PORT'
                ]]
            }
            
            for category, keys in categories.items():
                if any(key in env_vars for key in keys):
                    f.write(f"# {category}\n")
                    for key in keys:
                        if key in env_vars:
                            f.write(f"{key}={env_vars[key]}\n")
                    f.write("\n")


# 全局设置管理器实例
settings_manager = SettingsManager()


def get_settings_manager() -> SettingsManager:
    """获取设置管理器实例"""
    return settings_manager


def get_settings() -> ApplicationSettings:
    """获取应用程序设置"""
    return settings_manager.get_settings()


# 便捷函数
def get_database_url() -> str:
    """获取数据库URL"""
    return settings_manager.get_database_url()


def get_redis_url() -> str:
    """获取Redis URL"""
    return settings_manager.get_redis_url()


def get_secret_key() -> str:
    """获取密钥"""
    return settings_manager.get_secret_key()


def is_debug() -> bool:
    """是否为调试模式"""
    return settings_manager.is_debug()


def is_development() -> bool:
    """是否为开发环境"""
    return settings_manager.is_development()


def is_production() -> bool:
    """是否为生产环境"""
    return settings_manager.is_production()


if __name__ == '__main__':
    # 测试设置管理器
    sm = SettingsManager()
    
    print(f"项目名称: {sm.app_settings.project_name}")
    print(f"版本: {sm.app_settings.version}")
    print(f"环境: {sm.app_settings.environment}")
    print(f"调试模式: {sm.app_settings.debug}")
    print(f"服务器: {sm.app_settings.host}:{sm.app_settings.port}")
    print(f"数据库: {sm.app_settings.database_url}")
    
    print("\n配置验证:")
    validation = sm.validate_settings()
    if validation['errors']:
        print("错误:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")