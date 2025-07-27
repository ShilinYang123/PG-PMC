#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC 统一配置管理中心使用示例

这个文件展示了如何使用统一配置管理中心的各种功能，
包括基本配置管理、环境切换、配置验证、热重载等。
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入配置管理模块
from config import (
    # 快速设置
    quick_setup,
    initialize_config_system,
    get_system_status,
    cleanup_config_system,
    
    # 基本配置管理
    get_config_manager,
    get_config,
    set_config,
    save_config,
    
    # 环境管理
    get_current_environment,
    get_environment_manager,
    is_development,
    is_production,
    
    # 路径管理
    get_project_path,
    validate_paths,
    
    # 配置验证
    validate_config,
    migrate_configs,
    
    # 配置监控
    start_config_watching,
    stop_config_watching,
    add_config_change_callback,
    
    # 配置模板
    generate_template,
    
    # 配置同步
    sync_config_to_target,
    get_sync_manager,
    
    # 命令行工具
    ConfigCLI
)


def example_basic_usage():
    """
    基本使用示例
    """
    print("\n" + "=" * 60)
    print("基本使用示例")
    print("=" * 60)
    
    # 1. 快速设置配置系统
    print("\n1. 快速设置配置系统")
    success = quick_setup(
        environment='development',
        enable_watching=False,  # 示例中不启用监控
        enable_validation=True
    )
    
    if not success:
        print("❌ 配置系统设置失败")
        return
    
    # 2. 获取配置信息
    print("\n2. 获取配置信息")
    current_env = get_current_environment()
    print(f"当前环境: {current_env}")
    print(f"是否开发环境: {is_development()}")
    print(f"是否生产环境: {is_production()}")
    
    # 3. 获取路径信息
    print("\n3. 路径信息")
    try:
        project_root = get_project_path('root')
        docs_path = get_project_path('docs')
        logs_path = get_project_path('logs')
        
        print(f"项目根目录: {project_root}")
        print(f"文档目录: {docs_path}")
        print(f"日志目录: {logs_path}")
    except Exception as e:
        print(f"获取路径失败: {e}")
    
    # 4. 配置操作
    print("\n4. 配置操作")
    try:
        # 获取配置
        config_manager = get_config_manager()
        app_name = get_config('project.name', 'PG-PMC')
        print(f"应用名称: {app_name}")
        
        # 设置配置
        set_config('example.test_value', 'Hello World')
        test_value = get_config('example.test_value')
        print(f"测试值: {test_value}")
        
    except Exception as e:
        print(f"配置操作失败: {e}")
    
    # 5. 系统状态
    print("\n5. 系统状态")
    status = get_system_status()
    print(f"整体健康状态: {status['overall_health']}")
    print(f"时间戳: {status['timestamp']}")


def example_environment_management():
    """
    环境管理示例
    """
    print("\n" + "=" * 60)
    print("环境管理示例")
    print("=" * 60)
    
    # 保存当前环境
    original_env = get_current_environment()
    print(f"原始环境: {original_env}")
    
    # 切换到不同环境
    environments = ['development', 'testing', 'production']
    
    for env in environments:
        print(f"\n切换到 {env} 环境:")
        try:
            env_manager = get_environment_manager()
            env_manager.set_environment(env)
            current = get_current_environment()
            print(f"  当前环境: {current}")
            print(f"  是否开发环境: {is_development()}")
            print(f"  是否生产环境: {is_production()}")
        except Exception as e:
            print(f"  环境切换失败: {e}")
    
    # 恢复原始环境
    print(f"\n恢复到原始环境: {original_env}")
    env_manager = get_environment_manager()
    env_manager.set_environment(original_env)


def example_config_validation():
    """
    配置验证示例
    """
    print("\n" + "=" * 60)
    print("配置验证示例")
    print("=" * 60)
    
    # 验证配置
    print("\n验证当前配置:")
    try:
        is_valid = validate_config()
        print(f"配置有效性: {'✅ 有效' if is_valid else '❌ 无效'}")
    except Exception as e:
        print(f"配置验证失败: {e}")
    
    # 验证路径
    print("\n验证路径配置:")
    try:
        path_validation = validate_paths()
        print(f"有效路径: {len(path_validation.get('valid', []))}")
        print(f"缺失路径: {len(path_validation.get('missing', []))}")
        print(f"权限错误: {len(path_validation.get('permission_errors', []))}")
        
        if path_validation.get('missing'):
            print("缺失的路径:")
            for path in path_validation['missing'][:3]:  # 只显示前3个
                print(f"  - {path}")
    except Exception as e:
        print(f"路径验证失败: {e}")


def example_config_templates():
    """
    配置模板示例
    """
    print("\n" + "=" * 60)
    print("配置模板示例")
    print("=" * 60)
    
    # 生成不同环境的配置模板
    template_types = ['development', 'production', 'docker', 'minimal']
    
    for template_type in template_types:
        print(f"\n生成 {template_type} 配置模板:")
        try:
            template = generate_template(template_type)
            if template:
                print(f"  ✅ 模板生成成功")
                # 显示模板的一些关键信息
                if isinstance(template, dict):
                    if 'project' in template:
                        print(f"  项目名称: {template['project'].get('name', 'N/A')}")
                    if 'environment' in template:
                        print(f"  环境配置: {len(template['environment'])} 项")
                    if 'database' in template:
                        print(f"  数据库配置: {len(template['database'])} 项")
            else:
                print(f"  ❌ 模板生成失败")
        except Exception as e:
            print(f"  ❌ 模板生成异常: {e}")


def example_config_monitoring():
    """
    配置监控示例
    """
    print("\n" + "=" * 60)
    print("配置监控示例")
    print("=" * 60)
    
    # 定义配置变更回调
    def config_change_callback(file_path, event_type):
        print(f"📝 配置文件变更: {file_path} ({event_type})")
    
    print("\n启动配置监控:")
    try:
        # 添加回调
        add_config_change_callback(config_change_callback)
        
        # 启动监控
        watcher = start_config_watching()
        print("✅ 配置监控已启动")
        
        # 模拟一些操作
        print("\n模拟配置变更...")
        import time
        time.sleep(1)
        
        # 停止监控
        print("\n停止配置监控:")
        stop_config_watching()
        print("✅ 配置监控已停止")
        
    except Exception as e:
        print(f"❌ 配置监控失败: {e}")


def example_config_sync():
    """
    配置同步示例
    """
    print("\n" + "=" * 60)
    print("配置同步示例")
    print("=" * 60)
    
    try:
        # 获取同步管理器
        sync_manager = get_sync_manager()
        print("✅ 同步管理器初始化成功")
        
        # 显示同步状态
        status = sync_manager.get_sync_status()
        print(f"同步状态: {status}")
        
        # 注意: 实际的同步操作需要配置同步目标
        print("\n注意: 配置同步需要先配置同步目标")
        print("可以通过以下方式添加同步目标:")
        print("  sync_manager.add_sync_target('file', '/path/to/target')")
        print("  sync_manager.add_sync_target('git', 'repo_url')")
        
    except Exception as e:
        print(f"❌ 配置同步失败: {e}")


def example_cli_usage():
    """
    命令行工具使用示例
    """
    print("\n" + "=" * 60)
    print("命令行工具使用示例")
    print("=" * 60)
    
    try:
        # 创建CLI实例
        cli = ConfigCLI()
        print("✅ CLI工具初始化成功")
        
        print("\n可用的CLI命令:")
        print("  python -m config.config_cli show          # 显示配置")
        print("  python -m config.config_cli validate      # 验证配置")
        print("  python -m config.config_cli migrate       # 迁移配置")
        print("  python -m config.config_cli create-env    # 创建.env文件")
        print("  python -m config.config_cli export        # 导出配置")
        print("  python -m config.config_cli paths         # 显示路径")
        print("  python -m config.config_cli health        # 健康检查")
        print("  python -m config.config_cli reset         # 重置配置")
        print("  python -m config.config_cli backup        # 备份配置")
        
    except Exception as e:
        print(f"❌ CLI工具失败: {e}")


def example_advanced_usage():
    """
    高级使用示例
    """
    print("\n" + "=" * 60)
    print("高级使用示例")
    print("=" * 60)
    
    # 完整的配置系统初始化
    print("\n1. 完整配置系统初始化")
    result = initialize_config_system(
        auto_migrate=True,
        start_watching=False
    )
    
    print(f"初始化结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"初始化组件: {list(result['components'].keys())}")
    
    if result['warnings']:
        print(f"警告: {len(result['warnings'])} 个")
        for warning in result['warnings'][:3]:  # 只显示前3个
            print(f"  - {warning}")
    
    if result['errors']:
        print(f"错误: {len(result['errors'])} 个")
        for error in result['errors']:
            print(f"  - {error}")
    
    # 详细系统状态
    print("\n2. 详细系统状态")
    status = get_system_status()
    
    print(f"整体健康: {status['overall_health']}")
    print(f"当前环境: {status['environment']}")
    
    if 'legacy_config' in status:
        legacy = status['legacy_config']
        if 'error' not in legacy:
            print(f"原有配置: {legacy['total_errors']} 错误, {legacy['total_warnings']} 警告")
    
    if 'new_config' in status:
        new_config = status['new_config']
        if 'error' not in new_config:
            print(f"新配置: {'有效' if new_config['config_valid'] else '无效'}")


def main():
    """
    主函数 - 运行所有示例
    """
    print("PG-PMC 统一配置管理中心 - 使用示例")
    print("=" * 80)
    
    try:
        # 运行各种示例
        example_basic_usage()
        example_environment_management()
        example_config_validation()
        example_config_templates()
        example_config_monitoring()
        example_config_sync()
        example_cli_usage()
        example_advanced_usage()
        
        print("\n" + "=" * 80)
        print("所有示例运行完成")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n\n示例运行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n清理配置系统资源...")
        cleanup_config_system()


if __name__ == '__main__':
    main()