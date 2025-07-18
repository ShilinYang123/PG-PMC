#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的配置系统测试
"""

import sys
from pathlib import Path

# 添加项目src目录到路径
project_root = Path(__file__).parent.parent.parent
project_src = project_root / "src"
sys.path.insert(0, str(project_src))

print(f"项目根目录: {project_root}")
print(f"项目src目录: {project_src}")
print(f"当前Python路径: {sys.path[:3]}")

try:
    print("\n=== 测试导入 ===")
    from core.config_center import ConfigCenter, get_config_center

    print("✅ 成功导入 ConfigCenter")

    print("\n=== 测试配置中心创建 ===")
    config_center = ConfigCenter(project_root)
    print("✅ 成功创建配置中心")

    print("\n=== 测试配置加载 ===")
    config = config_center.load_config()
    print(f"✅ 成功加载配置，配置项数量: {len(config)}")

    print("\n=== 测试配置获取 ===")
    app_name = config_center.get_config("app.name", "默认应用名")
    print(f"✅ 应用名称: {app_name}")

    print("\n=== 测试配置设置 ===")
    success = config_center.set_config("test.value", "测试值")
    print(f"✅ 设置配置: {success}")

    test_value = config_center.get_config("test.value")
    print(f"✅ 获取测试值: {test_value}")

    print("\n=== 测试便捷函数 ===")
    from core.config_center import get_config, set_config

    # 使用便捷函数
    app_version = get_config("app.version", "1.0.0")
    print(f"✅ 应用版本: {app_version}")

    set_success = set_config("test.convenience", "便捷函数测试")
    print(f"✅ 便捷函数设置: {set_success}")

    convenience_value = get_config("test.convenience")
    print(f"✅ 便捷函数获取: {convenience_value}")

    print("\n🎉 所有测试通过！")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
