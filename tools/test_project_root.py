#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 PROJECT_ROOT 变量的值和类型
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入 finish 模块
    import finish

    print("=== PROJECT_ROOT 测试 ===")
    print("PROJECT_ROOT 值:", finish.PROJECT_ROOT)
    print("PROJECT_ROOT 类型:", type(finish.PROJECT_ROOT))
    print("PROJECT_ROOT 是否存在:", finish.PROJECT_ROOT.exists())

    # 测试路径拼接
    test_path = finish.PROJECT_ROOT / "docs" / "01-设计" / "目录结构标准清单.md"
    print("\n=== 路径拼接测试 ===")
    print("拼接路径:", test_path)
    print("拼接路径类型:", type(test_path))
    print("拼接路径是否存在:", test_path.exists())

    # 测试 get_project_root 函数
    if hasattr(finish, "get_project_root"):
        direct_root = finish.get_project_root()
        print("\n=== get_project_root() 测试 ===")
        print("直接调用结果:", direct_root)
        print("直接调用类型:", type(direct_root))
        print("与 PROJECT_ROOT 是否相等:", direct_root == finish.PROJECT_ROOT)

    print("\n=== 测试完成 ===\n")

except Exception as e:
    print(f"导入或测试失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
