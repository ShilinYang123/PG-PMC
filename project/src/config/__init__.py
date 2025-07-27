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

# 新增的配置管理模块
from .config_validator import (
    ConfigValidator as NewConfigValidator,
    ConfigMigrator,
    validate_config,
    migrate_configs
)

from .default_config import (
    DefaultConfigProvider as NewDefaultConfigProvider,
    get_default_provider,
    get_default_config,
    get_minimal_config
)

from .config_cli import (
    ConfigCLI
)

from .config_watcher import (
    ConfigWatcher,
    get_config_watcher,
    start_config_watching,
    stop_config_watching,
    add_config_change_callback,
    remove_config_change_callback
)

from .config_templates import (
    ConfigTemplateGenerator,
    get_template_generator,
    generate_template
)

from .config_sync import (
    ConfigSyncManager,
    SyncTarget,
    SyncDirection,
    SyncStatus,
    get_sync_manager,
    sync_config_to_target,
    sync_config_from_target,
    sync_all_targets
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
    'get_config',
    'set_config',
    'save_config',
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
    'validate_paths',
    
    # 配置验证器（原有）
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
    
    # 新增配置管理功能
    'NewConfigValidator',
    'ConfigMigrator',
    'validate_config',
    'migrate_configs',
    'NewDefaultConfigProvider',
    'get_default_provider',
    'get_default_config',
    'get_minimal_config',
    'ConfigCLI',
    'ConfigWatcher',
    'get_config_watcher',
    'start_config_watching',
    'stop_config_watching',
    'add_config_change_callback',
    'remove_config_change_callback',
    'ConfigTemplateGenerator',
    'get_template_generator',
    'generate_template',
    'ConfigSyncManager',
    'SyncTarget',
    'SyncDirection',
    'SyncStatus',
    'get_sync_manager',
    'sync_config_to_target',
    'sync_config_from_target',
    'sync_all_targets',
    
    # 便捷函数
    'init_config',
    'validate_all_configs',
    'export_all_env_vars',
    'create_default_env_file',
    'initialize_config_system',
    'get_system_status',
    'cleanup_config_system',
    'quick_setup'
]


def get_config(key: str = None, default=None):
    """
    获取配置值
    
    Args:
        key: 配置键名，支持点分隔的嵌套键（如 'database.host'）
        default: 默认值
    
    Returns:
        配置值或默认值
    """
    config_manager = get_config_manager()
    if key is None:
        return config_manager.get_config()
    return config_manager.get_config(key, default)


def set_config(key: str, value, save: bool = True):
    """
    设置配置值
    
    Args:
        key: 配置键名，支持点分隔的嵌套键（如 'database.host'）
        value: 配置值
        save: 是否立即保存到文件
    """
    config_manager = get_config_manager()
    config_manager.set_config(key, value)
    if save:
        config_manager.save_config()


def save_config():
    """
    保存配置到文件
    """
    config_manager = get_config_manager()
    config_manager.save_config()


def validate_paths():
    """
    验证项目路径
    
    Returns:
        dict: 路径验证结果
    """
    path_manager = get_path_manager()
    return path_manager.validate_paths()


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


# 新增的配置系统管理功能
def initialize_config_system(config_file: str = None, 
                            auto_migrate: bool = True,
                            start_watching: bool = False) -> dict:
    """
    初始化完整配置系统
    
    Args:
        config_file: 配置文件路径（可选）
        auto_migrate: 是否自动迁移配置
        start_watching: 是否启动配置监控
    
    Returns:
        dict: 初始化结果
    """
    result = {
        'success': True,
        'errors': [],
        'warnings': [],
        'components': {}
    }
    
    try:
        # 1. 初始化原有配置系统
        if config_file:
            init_config(config_file=config_file)
        else:
            init_config()
        result['components']['legacy_config'] = 'initialized'
        
        # 2. 初始化新配置验证器
        try:
            validator = NewConfigValidator()
            validation_result = validator.validate_all()
            
            if not validation_result['valid']:
                result['warnings'].extend(validation_result['errors'])
            
            result['components']['validator'] = 'initialized'
        except Exception as e:
            result['warnings'].append(f"配置验证器初始化警告: {e}")
        
        # 3. 自动迁移（如果需要）
        if auto_migrate:
            try:
                migrate_configs()
                result['components']['migrator'] = 'initialized'
            except Exception as e:
                result['warnings'].append(f"配置迁移警告: {e}")
        
        # 4. 启动配置监控（如果需要）
        if start_watching:
            try:
                watcher = start_config_watching()
                result['components']['watcher'] = 'started'
            except Exception as e:
                result['warnings'].append(f"配置监控启动失败: {e}")
        
        # 5. 初始化其他组件
        try:
            get_template_generator()
            result['components']['template_generator'] = 'initialized'
        except Exception as e:
            result['warnings'].append(f"模板生成器初始化警告: {e}")
        
        try:
            get_sync_manager()
            result['components']['sync_manager'] = 'initialized'
        except Exception as e:
            result['warnings'].append(f"同步管理器初始化警告: {e}")
        
    except Exception as e:
        result['success'] = False
        result['errors'].append(f"配置系统初始化失败: {e}")
    
    return result


def get_system_status() -> dict:
    """
    获取配置系统状态
    
    Returns:
        dict: 系统状态信息
    """
    status = {
        'timestamp': None,
        'environment': None,
        'legacy_config': {},
        'new_config': {},
        'overall_health': 'unknown'
    }
    
    try:
        from datetime import datetime
        status['timestamp'] = datetime.now().isoformat()
        
        # 环境信息
        status['environment'] = get_current_environment()
        
        # 原有配置系统状态
        try:
            validation = validate_all_configs()
            status['legacy_config'] = {
                'total_errors': validation['total_errors'],
                'total_warnings': validation['total_warnings'],
                'details': validation['details']
            }
        except Exception as e:
            status['legacy_config'] = {'error': str(e)}
        
        # 新配置系统状态
        try:
            validator = NewConfigValidator()
            validation_result = validator.validate_all()
            status['new_config'] = {
                'config_valid': validation_result['valid'],
                'errors_count': len(validation_result['errors']),
                'warnings_count': len(validation_result['warnings'])
            }
        except Exception as e:
            status['new_config'] = {'error': str(e)}
        
        # 整体健康状态
        health_issues = 0
        
        if status['legacy_config'].get('total_errors', 0) > 0:
            health_issues += 1
        
        if not status['new_config'].get('config_valid', True):
            health_issues += 1
        
        if health_issues == 0:
            status['overall_health'] = 'healthy'
        elif health_issues == 1:
            status['overall_health'] = 'warning'
        else:
            status['overall_health'] = 'critical'
    
    except Exception as e:
        status['overall_health'] = 'error'
        status['error'] = str(e)
    
    return status


def cleanup_config_system():
    """
    清理配置系统资源
    """
    try:
        # 停止配置监控
        try:
            stop_config_watching()
        except Exception:
            pass
        
        # 清理同步历史
        try:
            sync_manager = get_sync_manager()
            sync_manager.cleanup_history()
        except Exception:
            pass
        
        print("✅ 配置系统清理完成")
        
    except Exception as e:
        print(f"❌ 配置系统清理失败: {e}")


def quick_setup(environment: str = 'development', 
               enable_watching: bool = True,
               enable_validation: bool = True) -> bool:
    """
    快速设置配置系统
    
    Args:
        environment: 环境名称
        enable_watching: 是否启用配置监控
        enable_validation: 是否启用配置验证
    
    Returns:
        bool: 设置是否成功
    """
    try:
        print(f"🚀 快速设置配置系统 - 环境: {environment}")
        
        # 初始化配置系统
        result = initialize_config_system(
            auto_migrate=True,
            start_watching=enable_watching
        )
        
        if not result['success']:
            print(f"❌ 配置系统初始化失败: {result['errors']}")
            return False
        
        if result['warnings']:
            print(f"⚠️  警告: {result['warnings']}")
        
        # 验证配置（如果启用）
        if enable_validation:
            try:
                if not validate_config():
                    print("⚠️  配置验证发现问题，请检查配置")
            except Exception as e:
                print(f"⚠️  配置验证失败: {e}")
        
        print("✅ 配置系统设置完成")
        
        # 显示状态
        status = get_system_status()
        print(f"📊 系统健康状态: {status['overall_health']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速设置失败: {e}")
        return False


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
    
    # 显示新配置系统状态
    print("\n" + "=" * 50)
    print("配置系统状态")
    print("=" * 50)
    
    status = get_system_status()
    print(f"整体健康状态: {status['overall_health']}")
    print(f"当前环境: {status['environment']}")
    print(f"时间戳: {status['timestamp']}")
    
    if 'legacy_config' in status:
        legacy = status['legacy_config']
        if 'error' not in legacy:
            print(f"\n原有配置系统: {legacy['total_errors']} 错误, {legacy['total_warnings']} 警告")
        else:
            print(f"\n原有配置系统: {legacy['error']}")
    
    if 'new_config' in status:
        new_config = status['new_config']
        if 'error' not in new_config:
            print(f"新配置系统: {'有效' if new_config['config_valid'] else '无效'}, {new_config['errors_count']} 错误, {new_config['warnings_count']} 警告")
        else:
            print(f"新配置系统: {new_config['error']}")
    
    print("\n可用的新功能:")
    print("  • 配置验证和迁移")
    print("  • 配置热重载监控")
    print("  • 配置模板生成")
    print("  • 配置同步管理")
    print("  • 命令行工具")
    print("  • 默认配置提供")
    
    print("\n快速开始:")
    print("  from config import quick_setup")
    print("  quick_setup('development')")
    
    print("=" * 50)