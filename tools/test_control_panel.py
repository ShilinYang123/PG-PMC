#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC控制面板功能测试脚本
验证控制面板的各项功能是否正常工作
"""

import subprocess
import sys
import os
from pathlib import Path

def test_startup_check():
    """测试启动检查功能"""
    print("🧪 测试启动检查功能...")
    try:
        result = subprocess.run(
            ["python", "tools\\pmc_status_viewer.py", "--startup"],
            capture_output=True,
            text=True,
            cwd="S:/PG-PMC"
        )
        if result.returncode == 0:
            print("✅ 启动检查功能正常")
            return True
        else:
            print(f"❌ 启动检查失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 启动检查异常: {e}")
        return False

def test_status_viewer():
    """测试状态查看功能"""
    print("🧪 测试状态查看功能...")
    try:
        result = subprocess.run(
            ["python", "tools\\pmc_status_viewer.py"],
            capture_output=True,
            text=True,
            cwd="S:/PG-PMC"
        )
        if result.returncode == 0:
            print("✅ 状态查看功能正常")
            return True
        else:
            print(f"❌ 状态查看失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 状态查看异常: {e}")
        return False

def test_file_existence():
    """测试必要文件是否存在"""
    print("🧪 测试必要文件存在性...")
    
    required_files = [
        "tools/pmc_control_panel.py",
        "tools/pmc_status_viewer.py",
        "AI调度表/项目BD300/实时数据更新/PMC系统状态.json",
        "AI调度表/项目BD300/分析报告/BD300项目PMC控制系统快速操作手册.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path("S:/PG-PMC") / file_path
        if full_path.exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def test_control_panel_import():
    """测试控制面板模块导入"""
    print("🧪 测试控制面板模块导入...")
    try:
        # 添加项目路径
        sys.path.insert(0, "S:/PG-PMC")
        
        # 尝试导入控制面板模块
        from tools.pmc_control_panel import PMCControlPanel
        print("✅ 控制面板模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 控制面板模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始PMC控制面板功能测试")
    print("=" * 50)
    
    tests = [
        ("文件存在性检查", test_file_existence),
        ("控制面板模块导入", test_control_panel_import),
        ("启动检查功能", test_startup_check),
        ("状态查看功能", test_status_viewer)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！PMC控制面板功能正常")
        print("\n✅ 控制面板已准备就绪，可以正常使用")
        print("📋 使用方法:")
        print("   1. 运行: python tools\\pmc_control_panel.py")
        print("   2. 或者双击: 启动PMC控制面板.bat")
        print("   3. 点击'🌅 执行早上启动检查'按钮进行系统检查")
    else:
        print("❌ 部分测试失败，请检查相关功能")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())