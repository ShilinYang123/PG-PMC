#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理器
处理不同环境（开发、测试、生产）的配置加载和管理
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml
import json
from dataclasses import dataclass, asdict


class Environment(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    LOCAL = "local"


@dataclass
class EnvironmentConfig:
    """环境配置类"""
    name: str
    debug: bool
    log_level: str
    database_url: str
    redis_url: str
    secret_key: str
    cors_origins: list
    upload_dir: str
    max_file_size: int
    session_timeout: int
    cache_timeout: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        self.config_file = Path(config_file) if config_file else None
        self.current_env = self._detect_environment()
        self._env_configs: Dict[Environment, EnvironmentConfig] = {}
        self._load_default_configs()
        
        if self.config_file and self.config_file.exists():
            self._load_from_file()
    
    def _detect_environment(self) -> Environment:
        """检测当前环境"""
        env_name = os.getenv('PG_PMC_ENV', os.getenv('ENVIRONMENT', 'development')).lower()
        
        env_mapping = {
            'dev': Environment.DEVELOPMENT,
            'development': Environment.DEVELOPMENT,
            'test': Environment.TESTING,
            'testing': Environment.TESTING,
            'prod': Environment.PRODUCTION,
            'production': Environment.PRODUCTION,
            'local': Environment.LOCAL
        }
        
        return env_mapping.get(env_name, Environment.DEVELOPMENT)
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 开发环境配置
        self._env_configs[Environment.DEVELOPMENT] = EnvironmentConfig(
            name="development",
            debug=True,
            log_level="DEBUG",
            database_url=os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/pg_pmc_dev'),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            secret_key=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            cors_origins=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ],
            upload_dir=os.getenv('UPLOAD_DIR', 's:/PG-PMC/uploads'),
            max_file_size=50 * 1024 * 1024,  # 50MB
            session_timeout=3600,  # 1小时
            cache_timeout=300  # 5分钟
        )
        
        # 测试环境配置
        self._env_configs[Environment.TESTING] = EnvironmentConfig(
            name="testing",
            debug=True,
            log_level="INFO",
            database_url=os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:password@localhost:5432/pg_pmc_test'),
            redis_url=os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1'),
            secret_key=os.getenv('TEST_SECRET_KEY', 'test-secret-key'),
            cors_origins=["http://localhost:3000"],
            upload_dir=os.getenv('TEST_UPLOAD_DIR', 's:/PG-PMC/temp/test_uploads'),
            max_file_size=10 * 1024 * 1024,  # 10MB
            session_timeout=1800,  # 30分钟
            cache_timeout=60  # 1分钟
        )
        
        # 生产环境配置
        self._env_configs[Environment.PRODUCTION] = EnvironmentConfig(
            name="production",
            debug=False,
            log_level="WARNING",
            database_url=os.getenv('DATABASE_URL', ''),
            redis_url=os.getenv('REDIS_URL', ''),
            secret_key=os.getenv('SECRET_KEY', ''),
            cors_origins=os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else [],
            upload_dir=os.getenv('UPLOAD_DIR', '/var/uploads'),
            max_file_size=100 * 1024 * 1024,  # 100MB
            session_timeout=7200,  # 2小时
            cache_timeout=3600  # 1小时
        )
        
        # 本地环境配置（继承开发环境）
        local_config = self._env_configs[Environment.DEVELOPMENT]
        self._env_configs[Environment.LOCAL] = EnvironmentConfig(
            name="local",
            debug=local_config.debug,
            log_level="DEBUG",
            database_url=os.getenv('LOCAL_DATABASE_URL', local_config.database_url),
            redis_url=os.getenv('LOCAL_REDIS_URL', local_config.redis_url),
            secret_key=os.getenv('LOCAL_SECRET_KEY', 'local-secret-key'),
            cors_origins=local_config.cors_origins,
            upload_dir=os.getenv('LOCAL_UPLOAD_DIR', 's:/PG-PMC/uploads/local'),
            max_file_size=local_config.max_file_size,
            session_timeout=local_config.session_timeout,
            cache_timeout=local_config.cache_timeout
        )
    
    def _load_from_file(self):
        """从配置文件加载环境配置"""
        try:
            if self.config_file.suffix.lower() in ['.yaml', '.yml']:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            elif self.config_file.suffix.lower() == '.json':
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                return
            
            # 加载环境配置
            environments = config_data.get('environments', {})
            for env_name, env_config in environments.items():
                try:
                    env_enum = Environment(env_name)
                    if 'config' in env_config:
                        config = env_config['config']
                        self._env_configs[env_enum] = EnvironmentConfig(
                            name=env_name,
                            debug=config.get('debug', False),
                            log_level=config.get('log_level', 'INFO'),
                            database_url=config.get('database_url', ''),
                            redis_url=config.get('redis_url', ''),
                            secret_key=config.get('secret_key', ''),
                            cors_origins=config.get('cors_origins', []),
                            upload_dir=config.get('upload_dir', ''),
                            max_file_size=config.get('max_file_size', 50 * 1024 * 1024),
                            session_timeout=config.get('session_timeout', 3600),
                            cache_timeout=config.get('cache_timeout', 300)
                        )
                except ValueError:
                    # 未知环境名称，跳过
                    continue
                    
        except Exception as e:
            print(f"加载环境配置文件失败: {e}")
    
    def get_current_environment(self) -> Environment:
        """获取当前环境"""
        return self.current_env
    
    def set_environment(self, env: Union[Environment, str]):
        """设置当前环境"""
        if isinstance(env, str):
            env = Environment(env)
        self.current_env = env
    
    def get_config(self, env: Optional[Environment] = None) -> EnvironmentConfig:
        """获取环境配置"""
        env = env or self.current_env
        return self._env_configs.get(env, self._env_configs[Environment.DEVELOPMENT])
    
    def get_current_config(self) -> EnvironmentConfig:
        """获取当前环境配置"""
        return self.get_config(self.current_env)
    
    def get_environment_config(self, env: Optional[Environment] = None) -> EnvironmentConfig:
        """获取环境配置（别名方法）"""
        return self.get_config(env)
    
    def update_config(self, env: Environment, **kwargs):
        """更新环境配置"""
        if env in self._env_configs:
            config = self._env_configs[env]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    def get_database_url(self, env: Optional[Environment] = None) -> str:
        """获取数据库URL"""
        config = self.get_config(env)
        return config.database_url
    
    def get_redis_url(self, env: Optional[Environment] = None) -> str:
        """获取Redis URL"""
        config = self.get_config(env)
        return config.redis_url
    
    def is_debug_mode(self, env: Optional[Environment] = None) -> bool:
        """是否为调试模式"""
        config = self.get_config(env)
        return config.debug
    
    def get_log_level(self, env: Optional[Environment] = None) -> str:
        """获取日志级别"""
        config = self.get_config(env)
        return config.log_level
    
    def get_cors_origins(self, env: Optional[Environment] = None) -> list:
        """获取CORS源"""
        config = self.get_config(env)
        return config.cors_origins
    
    def get_upload_dir(self, env: Optional[Environment] = None) -> str:
        """获取上传目录"""
        config = self.get_config(env)
        return config.upload_dir
    
    def get_secret_key(self, env: Optional[Environment] = None) -> str:
        """获取密钥"""
        config = self.get_config(env)
        return config.secret_key
    
    def export_env_vars(self, env: Optional[Environment] = None) -> Dict[str, str]:
        """导出环境变量"""
        config = self.get_config(env)
        
        return {
            'PG_PMC_ENV': config.name,
            'DEBUG': str(config.debug).lower(),
            'LOG_LEVEL': config.log_level,
            'DATABASE_URL': config.database_url,
            'REDIS_URL': config.redis_url,
            'SECRET_KEY': config.secret_key,
            'CORS_ORIGINS': ','.join(config.cors_origins),
            'UPLOAD_DIR': config.upload_dir,
            'MAX_FILE_SIZE': str(config.max_file_size),
            'SESSION_TIMEOUT': str(config.session_timeout),
            'CACHE_TIMEOUT': str(config.cache_timeout)
        }
    
    def validate_config(self, env: Optional[Environment] = None) -> Dict[str, list]:
        """验证环境配置"""
        config = self.get_config(env)
        errors = []
        warnings = []
        
        # 检查必需配置
        if not config.secret_key or config.secret_key in ['dev-secret-key-change-in-production', 'test-secret-key']:
            if env == Environment.PRODUCTION:
                errors.append("生产环境必须设置安全的SECRET_KEY")
            else:
                warnings.append(f"{config.name}环境使用默认SECRET_KEY")
        
        if not config.database_url:
            errors.append("数据库URL未配置")
        
        if not config.redis_url:
            warnings.append("Redis URL未配置")
        
        # 检查上传目录
        upload_path = Path(config.upload_dir)
        if not upload_path.exists():
            warnings.append(f"上传目录不存在: {config.upload_dir}")
        
        # 检查生产环境特殊要求
        if env == Environment.PRODUCTION:
            if config.debug:
                errors.append("生产环境不应启用调试模式")
            
            if config.log_level == 'DEBUG':
                warnings.append("生产环境建议使用INFO或更高日志级别")
            
            if not config.cors_origins:
                warnings.append("生产环境应配置CORS源")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def save_to_file(self, file_path: Optional[Union[str, Path]] = None):
        """保存配置到文件"""
        file_path = Path(file_path) if file_path else self.config_file
        if not file_path:
            raise ValueError("未指定配置文件路径")
        
        config_data = {
            'environments': {}
        }
        
        for env, config in self._env_configs.items():
            config_data['environments'][env.value] = {
                'config': config.to_dict()
            }
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    def load_env_file(self, env_file: Union[str, Path]):
        """加载.env文件"""
        env_file = Path(env_file)
        if not env_file.exists():
            return
        
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    os.environ[key] = value
    
    def create_env_file(self, env_file: Union[str, Path], env: Optional[Environment] = None):
        """创建.env文件"""
        env_vars = self.export_env_vars(env)
        env_file = Path(env_file)
        
        # 确保目录存在
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"# PG-PMC 环境配置文件\n")
            f.write(f"# 环境: {self.get_config(env).name}\n")
            f.write(f"# 生成时间: {os.popen('date').read().strip()}\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")


# 全局环境管理器实例
env_manager = EnvironmentManager()


def get_environment_manager() -> EnvironmentManager:
    """获取环境管理器实例"""
    return env_manager


def get_current_environment() -> Environment:
    """获取当前环境"""
    return env_manager.get_current_environment()


def get_current_config() -> EnvironmentConfig:
    """获取当前环境配置"""
    return env_manager.get_current_config()


def is_development() -> bool:
    """是否为开发环境"""
    return env_manager.get_current_environment() == Environment.DEVELOPMENT


def is_production() -> bool:
    """是否为生产环境"""
    return env_manager.get_current_environment() == Environment.PRODUCTION


def is_testing() -> bool:
    """是否为测试环境"""
    return env_manager.get_current_environment() == Environment.TESTING


if __name__ == '__main__':
    # 测试环境管理器
    em = EnvironmentManager()
    
    print(f"当前环境: {em.get_current_environment().value}")
    print(f"调试模式: {em.is_debug_mode()}")
    print(f"日志级别: {em.get_log_level()}")
    print(f"数据库URL: {em.get_database_url()}")
    
    print("\n环境变量:")
    env_vars = em.export_env_vars()
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    
    print("\n配置验证:")
    validation = em.validate_config()
    if validation['errors']:
        print("错误:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("警告:")
        for warning in validation['warnings']:
            print(f"  - {warning}")