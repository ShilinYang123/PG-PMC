#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发任务合规性检查器
确保开发任务符合项目规范
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))
from pre_operation_check import ProjectComplianceChecker

def main():
    if len(sys.argv) < 3:
        print("用法: python check_development_task.py <task_description> <module_name>")
        sys.exit(1)
    
    task_description = sys.argv[1]
    module_name = sys.argv[2]
    
    checker = ProjectComplianceChecker()
    passed, messages = checker.check_development_task(task_description, module_name)
    
    print(f"\n{'='*60}")
    print(f"开发任务检查结果: {'通过' if passed else '未通过'}")
    print(f"{'='*60}")
    for message in messages:
        print(message)
    print(f"{'='*60}\n")
    
    if not passed:
        print("[错误] 开发任务不符合项目规范，请调整后重试")
        sys.exit(1)
    else:
        print("[成功] 开发任务符合项目规范，可以开始开发")

if __name__ == "__main__":
    main()
