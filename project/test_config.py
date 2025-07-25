#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理测试脚本
测试统一配置管理中心是否能正确加载和处理现有配置
"""

import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.config import (
        init_config,
        get_settings_manager,
        get_settings,
        get_config_manager,
        get_environment_manager,
        get_path_manager
    )
except ImportError as e:
    print(f"导入配置模块失败: {e}")
    sys.exit(1)

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    try:
        # 初始化配置
        config_file = "s:/PG-PMC/docs/03-管理/project_config.yaml"
        print(f"使用配置文件: {config_file}")
        
        init_config(config_file=config_file, env='development')
        print("✓ 配置初始化成功")
        
        # 获取配置管理器
        settings_manager = get_settings_manager()
        if settings_manager:
            print("✓ 获取设置管理器成功")
        else:
            print("✗ 获取设置管理器失败")
            return False
        
        # 获取应用设置
        settings = get_settings()
        if settings:
            print("✓ 获取应用设置成功")
            print(f"  项目名称: {settings.project_name}")
            print(f"  项目版本: {settings.version}")
            print(f"  当前环境: {settings.environment}")
        else:
            print("✗ 获取应用设置失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n" + "=" * 60)
    print("测试配置管理器")
    print("=" * 60)
    
    try:
        config_manager = get_config_manager()
        if not config_manager:
            print("✗ 获取配置管理器失败")
            return False
        
        print("✓ 获取配置管理器成功")
        
        # 测试获取各个配置部分
        sections = ['project', 'database', 'server', 'security', 'logging', 'paths']
        
        for section in sections:
            config_data = config_manager.get_config(section)
            if config_data:
                print(f"✓ 获取 {section} 配置成功")
                if section == 'project':
                    print(f"  项目名称: {config_data.get('name', 'N/A')}")
                elif section == 'database':
                    print(f"  数据库主机: {config_data.get('host', 'N/A')}")
                    print(f"  数据库端口: {config_data.get('port', 'N/A')}")
                elif section == 'server':
                    print(f"  服务器主机: {config_data.get('host', 'N/A')}")
                    print(f"  服务器端口: {config_data.get('port', 'N/A')}")
            else:
                print(f"✗ 获取 {section} 配置失败")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_manager():
    """测试环境管理器"""
    print("\n" + "=" * 60)
    print("测试环境管理器")
    print("=" * 60)
    
    try:
        env_manager = get_environment_manager()
        if not env_manager:
            print("✗ 获取环境管理器失败")
            return False
        
        print("✓ 获取环境管理器成功")
        
        # 获取当前环境
        current_env = env_manager.get_current_environment()
        print(f"✓ 当前环境: {current_env}")
        
        # 获取环境配置
        env_config = env_manager.get_environment_config()
        if env_config:
            print("✓ 获取环境配置成功")
            print(f"  调试模式: {env_config.debug}")
            print(f"  日志级别: {env_config.log_level}")
        else:
            print("✗ 获取环境配置失败")
        
        return True
        
    except Exception as e:
        print(f"✗ 环境管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_manager():
    """测试路径管理器"""
    print("\n" + "=" * 60)
    print("测试路径管理器")
    print("=" * 60)
    
    try:
        path_manager = get_path_manager()
        if not path_manager:
            print("✗ 获取路径管理器失败")
            return False
        
        print("✓ 获取路径管理器成功")
        
        # 测试获取各个路径
        path_keys = ['root', 'docs', 'logs', 'tools', 'backup']
        
        for key in path_keys:
            try:
                path = path_manager.get_path(key)
                if path:
                    print(f"✓ {key}: {path}")
                else:
                    print(f"✗ {key}: 未找到")
            except Exception as e:
                print(f"✗ {key}: 获取失败 - {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 路径管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_config():
    """测试数据库配置"""
    print("\n" + "=" * 60)
    print("测试数据库配置")
    print("=" * 60)
    
    try:
        settings = get_settings()
        if not settings:
            print("✗ 获取设置失败")
            return False
        
        print("✓ 数据库配置测试:")
        print(f"  数据库URL: {getattr(settings, 'database_url', 'N/A')}")
        print(f"  SQLite URL: {getattr(settings, 'sqlite_url', 'N/A')}")
        
        # 测试数据库连接字符串生成
        config_manager = get_config_manager()
        if config_manager:
            db_config = config_manager.get_config('database')
            if db_config:
                print(f"  数据库主机: {db_config.get('host', 'N/A')}")
                print(f"  数据库端口: {db_config.get('port', 'N/A')}")
                print(f"  数据库名称: {db_config.get('name', 'N/A')}")
                print(f"  用户名: {db_config.get('username', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("PMC统一配置管理中心测试")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_config_manager,
        test_environment_manager,
        test_path_manager,
        test_database_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！统一配置管理中心工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)