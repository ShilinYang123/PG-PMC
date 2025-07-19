#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全文件操作包装器
自动调用前置检查，确保文件操作符合规范
"""

import sys
import subprocess
from pathlib import Path

def check_and_execute(operation_type, file_path, *args):
    """检查并执行文件操作"""
    # 调用前置检查
    check_cmd = [
        sys.executable,
        "s:\PG-PMC\tools\pre_operation_check.py",
        "--check-file", file_path,
        "--operation", operation_type
    ]
    
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[阻止] 操作被阻止: {file_path}")
        print(result.stdout)
        return False
    
    print(f"[通过] 检查通过: {file_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python safe_file_operation.py <operation> <file_path> [args...]")
        sys.exit(1)
    
    operation = sys.argv[1]
    file_path = sys.argv[2]
    args = sys.argv[3:]
    
    if check_and_execute(operation, file_path, *args):
        print("操作已通过合规性检查")
    else:
        print("操作被合规性检查阻止")
        sys.exit(1)
