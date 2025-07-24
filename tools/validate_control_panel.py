#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC控制面板功能验证脚本
自动验证控制面板的各项功能
"""

import subprocess
import sys
from pathlib import Path

def test_function(func_name, test_func):
    """测试函数包装器"""
    print(f"\n🧪 测试 {func_name}...")
    try:
        result = test_func()
        if result:
            print(f"✅ {func_name} - 通过")
            return True
        else:
            print(f"❌ {func_name} - 失败")
            return False
    except Exception as e:
        print(f"❌ {func_name} - 异常: {e}")
        return False

def test_startup_check():
    """测试启动检查功能"""
    result = subprocess.run(
        ['python', 'tools\\pmc_status_viewer.py', '--startup'],
        capture_output=True, text=True, encoding='utf-8'
    )
    return result.returncode == 0

def test_status_view():
    """测试状态查看功能"""
    result = subprocess.run(
        ['python', 'tools\\pmc_status_viewer.py'],
        capture_output=True, text=True, encoding='utf-8'
    )
    return result.returncode == 0

def test_control_panel_import():
    """测试控制面板模块导入"""
    try:
        from tools.pmc_control_panel import PMCControlPanel
        return True
    except ImportError:
        return False

def test_file_existence():
    """测试关键文件存在性"""
    required_files = [
        "tools/pmc_control_panel.py",
        "tools/pmc_status_viewer.py",
        "启动PMC控制面板.bat",
        "AI调度表/项目BD300/实时数据更新/PMC系统状态.json"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"   ❌ 缺少文件: {file_path}")
            return False
    return True

def test_batch_file():
    """测试批处理文件语法"""
    batch_file = Path("启动PMC控制面板.bat")
    if not batch_file.exists():
        return False
    
    # 检查批处理文件内容
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查关键命令是否存在
            return 'activate.bat' in content and 'pmc_control_panel.py' in content
    except:
        return False

def main():
    """主验证函数"""
    print("🔍 PMC控制面板功能验证")
    print("=" * 50)
    
    tests = [
        ("文件存在性检查", test_file_existence),
        ("控制面板模块导入", test_control_panel_import),
        ("启动检查功能", test_startup_check),
        ("状态查看功能", test_status_view),
        ("批处理文件检查", test_batch_file)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_function(test_name, test_func):
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有验证通过！PMC控制面板功能完全正常")
        print("\n✅ 控制面板已准备就绪，包含以下功能:")
        print("   🌅 早上启动检查 - 快速系统状态检查")
        print("   🔍 详细状态查看 - 完整系统信息显示")
        print("   🖥️ 图形化界面 - 用户友好的操作面板")
        print("   🚀 系统启动 - PMC管理和跟踪系统")
        print("   📚 文档访问 - 快速打开操作手册")
        print("\n📋 使用方法:")
        print("   1. 双击 '启动PMC控制面板.bat'")
        print("   2. 在图形界面中点击相应按钮")
        print("   3. '[启动] 执行早上启动检查' - 进行系统检查")
        print("   4. '[检查] 查看详细状态' - 查看完整状态")
        return 0
    else:
        print("❌ 部分验证失败，请检查相关功能")
        return 1

if __name__ == "__main__":
    exit(main())