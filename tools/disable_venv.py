#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
禁用虚拟环境自动激活工具
杨老师专用 - 确保脚本在系统Python环境中运行
"""

import os
import sys
from pathlib import Path

def disable_virtual_env():
    """
    禁用虚拟环境，确保使用系统Python
    """
    print("=== 虚拟环境禁用工具 ===")
    
    # 检查当前是否在虚拟环境中
    if 'VIRTUAL_ENV' in os.environ:
        print(f"检测到虚拟环境: {os.environ['VIRTUAL_ENV']}")
        print("正在禁用虚拟环境...")
        
        # 移除虚拟环境相关的环境变量
        if 'VIRTUAL_ENV' in os.environ:
            del os.environ['VIRTUAL_ENV']
            print("✓ 已移除 VIRTUAL_ENV 环境变量")
        
        if 'VIRTUAL_ENV_PROMPT' in os.environ:
            del os.environ['VIRTUAL_ENV_PROMPT']
            print("✓ 已移除 VIRTUAL_ENV_PROMPT 环境变量")
        
        # 恢复系统PATH
        path = os.environ.get('PATH', '')
        path_parts = path.split(os.pathsep)
        
        # 移除虚拟环境相关的路径
        cleaned_paths = []
        for part in path_parts:
            if '.venv' not in part.lower() and 'virtual' not in part.lower():
                cleaned_paths.append(part)
        
        os.environ['PATH'] = os.pathsep.join(cleaned_paths)
        print("✓ 已清理PATH环境变量")
        
    else:
        print("当前未检测到虚拟环境")
    
    # 显示当前Python环境信息
    print("\n=== 当前Python环境信息 ===")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")
    
    # 检查是否为系统Python
    if '.venv' in sys.executable.lower() or 'virtual' in sys.executable.lower():
        print("⚠️  警告: 仍在虚拟环境中，请重新启动终端")
        return False
    else:
        print("✓ 成功切换到系统Python环境")
        return True

def create_no_venv_script():
    """
    创建无虚拟环境运行脚本
    """
    script_content = '''@echo off
REM 禁用虚拟环境的批处理脚本
REM 杨老师专用 - 确保使用系统Python

echo === 禁用虚拟环境运行模式 ===

REM 清除虚拟环境变量
set VIRTUAL_ENV=
set VIRTUAL_ENV_PROMPT=

REM 使用系统Python运行脚本
if "%1"=="" (
    echo 用法: no_venv.bat [Python脚本路径]
    echo 示例: no_venv.bat tools\\check_structure.py
    pause
    exit /b 1
)

echo 正在使用系统Python运行: %1
python %*

echo.
echo 脚本执行完成
pause
'''
    
    batch_file = Path("s:/PG-PMC/tools/no_venv.bat")
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✓ 已创建无虚拟环境运行脚本: {batch_file}")
    print("使用方法: no_venv.bat tools\\check_structure.py")

def main():
    """
    主函数
    """
    print("杨老师，正在为您禁用虚拟环境...")
    
    # 禁用虚拟环境
    success = disable_virtual_env()
    
    # 创建便捷脚本
    create_no_venv_script()
    
    print("\n=== 解决方案说明 ===")
    print("1. 虚拟环境自动激活是由IDE终端设置导致的")
    print("2. 已为您创建 no_venv.bat 脚本，可直接使用系统Python")
    print("3. 建议使用: no_venv.bat tools\\check_structure.py")
    print("4. 这样可以避免虚拟环境导致的性能问题")
    
    if success:
        print("\n✓ 虚拟环境已成功禁用")
    else:
        print("\n⚠️  请重新启动终端以完全禁用虚拟环境")

if __name__ == "__main__":
    main()