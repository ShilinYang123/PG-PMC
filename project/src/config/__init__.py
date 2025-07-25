#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理中心
提供项目的所有配置管理功能，包括配置加载、环境管理、路径管理和设置管理
"""

# 导入主要类和函数
from .config_manager import (
    ConfigManager,
    get_config_manager,
    load_project_config,
    save_project_config,
    get_config_value,
    set_config_value
)

from .environment import (
    Environment,
    EnvironmentManager,
    EnvironmentConfig,
    get_environment_manager,
    get_current_environment,
    get_current_config,
    is_development,
    is_production,
    is_testing
)

from .path_manager import (
    PathManager,
    PathConfig,
    get_path_manager,
    get_project_path,
    normalize_project_path,
    validate_project_paths
)

from .validator import (
    ConfigValidator,
    DefaultConfigProvider
)

from .settings import (
    ApplicationSettings,
    SettingsManager,
    get_settings_manager,
    get_settings,
    get_database_url,
    get_redis_url,
    get_secret_key,
    is_debug
)

# 版本信息
__version__ = "1.0.0"
__author__ = "PG-PMC Team"
__description__ = "统一配置管理中心"

# 导出的公共接口
__all__ = [
    # 配置管理器
    'ConfigManager',
    'get_config_manager',
    'load_project_config',
    'save_project_config',
    'get_config_value',
    'set_config_value',
    
    # 环境管理器
    'Environment',
    'EnvironmentManager',
    'EnvironmentConfig',
    'get_environment_manager',
    'get_current_environment',
    'get_current_config',
    'is_development',
    'is_production',
    'is_testing',
    
    # 路径管理器
    'PathManager',
    'PathConfig',
    'get_path_manager',
    'get_project_path',
    'normalize_project_path',
    'validate_project_paths',
    
    # 配置验证器
    'ConfigValidator',
    'DefaultConfigProvider',
    
    # 设置管理器
    'ApplicationSettings',
    'SettingsManager',
    'get_settings_manager',
    'get_settings',
    'get_database_url',
    'get_redis_url',
    'get_secret_key',
    'is_debug',
    
    # 便捷函数
    'init_config',
    'validate_all_configs',
    'export_all_env_vars',
    'create_default_env_file'
]


def init_config(config_file=None, env=None, project_root=None):
    """
    初始化配置系统
    
    Args:
        config_file: 配置文件路径
        env: 环境名称或Environment枚举
        project_root: 项目根目录
    
    Returns:
        SettingsManager: 设置管理器实例
    """
    # 初始化路径管理器
    if project_root:
        path_manager = get_path_manager()
        path_manager.update_project_root(project_root)
    
    # 初始化环境管理器
    if env:
        env_manager = get_environment_manager()
        env_manager.set_environment(env)
    
    # 初始化设置管理器
    settings_manager = SettingsManager(config_file)
    
    return settings_manager


def validate_all_configs():
    """
    验证所有配置
    
    Returns:
        dict: 验证结果
    """
    results = {
        'paths': validate_project_paths(),
        'environment': get_environment_manager().validate_config(),
        'settings': get_settings_manager().validate_settings()
    }
    
    # 汇总结果
    summary = {
        'total_errors': 0,
        'total_warnings': 0,
        'details': results
    }
    
    for category, result in results.items():
        if isinstance(result, dict):
            if 'errors' in result:
                summary['total_errors'] += len(result['errors'])
            if 'warnings' in result:
                summary['total_warnings'] += len(result['warnings'])
            if 'missing' in result:
                summary['total_errors'] += len(result['missing'])
            if 'permission_errors' in result:
                summary['total_errors'] += len(result['permission_errors'])
    
    return summary


def export_all_env_vars():
    """
    导出所有环境变量
    
    Returns:
        dict: 环境变量字典
    """
    env_vars = {}
    
    # 路径管理器的环境变量
    env_vars.update(get_path_manager().export_env_vars())
    
    # 环境管理器的环境变量
    env_vars.update(get_environment_manager().export_env_vars())
    
    # 设置管理器的环境变量
    env_vars.update(get_settings_manager().export_env_vars())
    
    return env_vars


def create_default_env_file(env_file='.env', env=None):
    """
    创建默认的.env文件
    
    Args:
        env_file: 环境文件路径
        env: 环境类型
    """
    settings_manager = get_settings_manager()
    
    if env:
        env_manager = get_environment_manager()
        env_manager.set_environment(env)
        settings_manager.reload_config()
    
    settings_manager.create_env_file(env_file)


def get_quick_config():
    """
    获取快速配置字典，包含最常用的配置项
    
    Returns:
        dict: 快速配置字典
    """
    settings = get_settings()
    
    return {
        # 基本信息
        'project_name': settings.project_name,
        'version': settings.version,
        'environment': settings.environment,
        'debug': settings.debug,
        
        # 服务器配置
        'host': settings.host,
        'port': settings.port,
        
        # 数据库配置
        'database_url': settings.database_url,
        'redis_url': settings.redis_url,
        
        # 安全配置
        'secret_key': settings.secret_key,
        
        # 路径配置
        'upload_dir': settings.upload_dir,
        'log_file': settings.log_file,
        
        # API配置
        'api_prefix': settings.api_v1_prefix,
        'cors_origins': settings.cors_origins,
        
        # 重要路径
        'project_root': str(get_project_path('root')),
        'docs_path': str(get_project_path('docs')),
        'logs_path': str(get_project_path('logs')),
        'config_path': str(get_project_path('config'))
    }


def print_config_summary():
    """
    打印配置摘要信息
    """
    config = get_quick_config()
    
    print("=" * 60)
    print(f"PG-PMC 配置摘要")
    print("=" * 60)
    
    print(f"项目名称: {config['project_name']}")
    print(f"版本: {config['version']}")
    print(f"环境: {config['environment']}")
    print(f"调试模式: {config['debug']}")
    print(f"服务器: {config['host']}:{config['port']}")
    print(f"API前缀: {config['api_prefix']}")
    
    print("\n路径配置:")
    print(f"  项目根目录: {config['project_root']}")
    print(f"  文档目录: {config['docs_path']}")
    print(f"  日志目录: {config['logs_path']}")
    print(f"  配置目录: {config['config_path']}")
    print(f"  上传目录: {config['upload_dir']}")
    
    print("\n数据库配置:")
    print(f"  数据库URL: {config['database_url'][:50]}..." if len(config['database_url']) > 50 else f"  数据库URL: {config['database_url']}")
    print(f"  Redis URL: {config['redis_url'][:50]}..." if len(config['redis_url']) > 50 else f"  Redis URL: {config['redis_url']}")
    
    print("\nCORS源:")
    for origin in config['cors_origins']:
        print(f"  - {origin}")
    
    print("=" * 60)
    
    # 验证配置
    validation = validate_all_configs()
    if validation['total_errors'] > 0 or validation['total_warnings'] > 0:
        print(f"\n配置验证: {validation['total_errors']} 个错误, {validation['total_warnings']} 个警告")
        
        for category, result in validation['details'].items():
            if isinstance(result, dict):
                errors = result.get('errors', []) + result.get('missing', []) + result.get('permission_errors', [])
                warnings = result.get('warnings', [])
                
                if errors:
                    print(f"\n{category} 错误:")
                    for error in errors:
                        print(f"  - {error}")
                
                if warnings:
                    print(f"\n{category} 警告:")
                    for warning in warnings:
                        print(f"  - {warning}")
    else:
        print("\n✓ 所有配置验证通过")
    
    print("=" * 60)


# 模块初始化时的自动配置
def _auto_init():
    """
    模块自动初始化
    """
    try:
        # 验证路径
        path_validation = validate_project_paths()
        
        # 创建缺失的目录
        if path_validation.get('missing') or path_validation.get('created'):
            get_path_manager().create_missing_directories()
        
    except Exception as e:
        print(f"配置模块初始化警告: {e}")


# 执行自动初始化
_auto_init()


if __name__ == '__main__':
    # 模块测试
    print("PG-PMC 统一配置管理中心")
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    
    print("\n" + "=" * 50)
    print_config_summary()