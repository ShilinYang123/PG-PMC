#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环境变量验证功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_validator import ConfigValidator
from config_loader import load_yaml_config

def test_environment_validation():
    """测试环境变量验证功能"""
    print("=== 测试环境变量验证功能 ===")
    
    # 加载项目配置
    config_path = "s:\\3AI\\docs\\03-管理\\project_config.yaml"
    try:
        config = load_yaml_config(config_path)
        print(f"成功加载配置文件: {config_path}")
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return
    
    # 创建验证器
    validator = ConfigValidator()
    
    # 测试环境变量验证
    print("\n--- 开始验证环境变量配置 ---")
    result = validator.validate_environment_config(config)
    
    print(f"\n验证结果: {'通过' if result else '失败'}")
    print(f"错误数量: {len(validator.errors)}")
    print(f"警告数量: {len(validator.warnings)}")
    
    if validator.errors:
        print("\n错误列表:")
        for i, error in enumerate(validator.errors, 1):
            print(f"  {i}. {error}")
    
    if validator.warnings:
        print("\n警告列表:")
        for i, warning in enumerate(validator.warnings, 1):
            print(f"  {i}. {warning}")
    
    # 检查环境变量配置是否存在
    if 'environment' in config:
        env_config = config['environment']
        print(f"\n环境变量配置节存在，包含以下子节:")
        for key in env_config.keys():
            print(f"  - {key}")
        
        # 详细检查各个子配置
        if 'app' in env_config:
            app_config = env_config['app']
            print(f"\napp 配置: {app_config}")
        
        if 'database' in env_config:
            db_config = env_config['database']
            print(f"\ndatabase 配置: {db_config}")
        
        if 'redis' in env_config:
            redis_config = env_config['redis']
            print(f"\nredis 配置: {redis_config}")
        
        if 'security' in env_config:
            security_config = env_config['security']
            print(f"\nsecurity 配置: {security_config}")
    else:
        print("\n环境变量配置节不存在")

if __name__ == "__main__":
    test_environment_validation()