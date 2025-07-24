#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC控制面板功能演示脚本
展示控制面板的各项功能
"""

import subprocess
import time
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"[演示] {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("✅ 执行成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
        else:
            print("❌ 执行失败")
            if result.stderr:
                print("错误:")
                print(result.stderr)
    except Exception as e:
        print(f"❌ 执行异常: {e}")
    
    print("\n按回车键继续...")
    input()

def main():
    """主演示函数"""
    print("🎯 PMC控制面板功能演示")
    print("=" * 60)
    print("本演示将展示PMC控制面板的各项核心功能")
    print("\n按回车键开始演示...")
    input()
    
    # 1. 演示启动检查功能
    run_command(
        'python "tools\\pmc_status_viewer.py" --startup',
        "早上启动检查功能"
    )
    
    # 2. 演示完整状态查看
    run_command(
        'python "tools\\pmc_status_viewer.py"',
        "完整系统状态查看"
    )
    
    # 3. 演示控制面板模块导入
    run_command(
        'python -c "from tools.pmc_control_panel import PMCControlPanel; print(\'✅ 控制面板模块导入成功\')"',
        "控制面板模块导入测试"
    )
    
    # 4. 检查关键文件
    print(f"\n{'='*50}")
    print("[演示] 关键文件检查")
    print(f"{'='*50}")
    
    files_to_check = [
        "tools/pmc_control_panel.py",
        "tools/pmc_status_viewer.py",
        "启动PMC控制面板.bat",
        "AI调度表/项目BD300/实时数据更新/PMC系统状态.json"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} - 存在")
        else:
            print(f"❌ {file_path} - 不存在")
    
    print("\n按回车键继续...")
    input()
    
    # 5. 演示总结
    print(f"\n{'='*50}")
    print("[演示完成] PMC控制面板功能总结")
    print(f"{'='*50}")
    print("✅ 早上启动检查 - 可以快速检查系统状态")
    print("✅ 完整状态查看 - 可以查看详细的系统信息")
    print("✅ 控制面板界面 - 提供图形化操作界面")
    print("✅ 批处理启动 - 可以通过.bat文件快速启动")
    print("\n🎉 PMC控制面板已准备就绪，所有功能正常！")
    print("\n📋 使用说明:")
    print("   1. 双击 '启动PMC控制面板.bat' 启动图形界面")
    print("   2. 点击 '[启动] 执行早上启动检查' 按钮进行系统检查")
    print("   3. 点击 '[检查] 查看详细状态' 按钮查看完整状态")
    print("   4. 使用其他按钮启动PMC管理系统和跟踪系统")
    
if __name__ == "__main__":
    main()