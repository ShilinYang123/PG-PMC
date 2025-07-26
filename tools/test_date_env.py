#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日期环境变量设置
创建时间: 2025年07月26日
"""

import os
import sys
from pathlib import Path

def test_environment_variables():
    """测试日期相关的环境变量"""
    print("=== 测试日期环境变量 ===")
    
    # 要检查的环境变量列表
    date_env_vars = [
        'SYSTEM_CURRENT_DATE',
        'SYSTEM_CURRENT_DATETIME', 
        'SYSTEM_CURRENT_DATE_FORMATTED',
        'SYSTEM_CURRENT_YEAR',
        'SYSTEM_CURRENT_MONTH',
        'SYSTEM_CURRENT_DAY',
        'SYSTEM_CURRENT_WEEKDAY',
        'SYSTEM_TIMESTAMP'
    ]
    
    found_vars = 0
    for var_name in date_env_vars:
        value = os.environ.get(var_name)
        if value:
            print(f"✓ {var_name}: {value}")
            found_vars += 1
        else:
            print(f"✗ {var_name}: 未设置")
    
    print(f"\n找到 {found_vars}/{len(date_env_vars)} 个环境变量")
    
    return found_vars > 0

def test_config_files():
    """测试日期配置文件"""
    print("\n=== 测试日期配置文件 ===")
    
    tools_dir = Path(__file__).parent
    
    # 检查JSON配置文件
    json_file = tools_dir / "current_date.json"
    if json_file.exists():
        print(f"✓ JSON配置文件存在: {json_file}")
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                formatted_date = data.get('ai_instructions', {}).get('formatted_date', '未找到')
                print(f"  当前日期: {formatted_date}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print(f"✗ JSON配置文件不存在: {json_file}")
    
    # 检查文本配置文件
    txt_file = tools_dir / "current_date.txt"
    if txt_file.exists():
        print(f"✓ 文本配置文件存在: {txt_file}")
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"  内容预览: {content.split(chr(10))[0]}")
        except Exception as e:
            print(f"  读取失败: {e}")
    else:
        print(f"✗ 文本配置文件不存在: {txt_file}")

def set_test_environment_variables():
    """手动设置测试环境变量"""
    print("\n=== 手动设置环境变量 ===")
    
    from datetime import datetime
    
    now = datetime.now()
    
    # 设置环境变量
    test_vars = {
        'SYSTEM_CURRENT_DATE': now.strftime('%Y-%m-%d'),
        'SYSTEM_CURRENT_DATETIME': now.strftime('%Y-%m-%d %H:%M:%S'),
        'SYSTEM_CURRENT_DATE_FORMATTED': now.strftime('%Y年%m月%d日'),
        'SYSTEM_CURRENT_YEAR': str(now.year),
        'SYSTEM_CURRENT_MONTH': str(now.month),
        'SYSTEM_CURRENT_DAY': str(now.day),
        'SYSTEM_CURRENT_WEEKDAY': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()],
        'SYSTEM_TIMESTAMP': now.isoformat()
    }
    
    for var_name, value in test_vars.items():
        os.environ[var_name] = value
        print(f"✓ 设置 {var_name} = {value}")
    
    print("\n环境变量设置完成！")
    return True

def main():
    """主函数"""
    print("日期环境变量测试工具")
    print("=" * 50)
    
    # 测试现有环境变量
    has_env_vars = test_environment_variables()
    
    # 测试配置文件
    test_config_files()
    
    # 如果没有环境变量，手动设置
    if not has_env_vars:
        print("\n检测到环境变量未设置，正在手动设置...")
        set_test_environment_variables()
        
        # 重新测试
        test_environment_variables()
    
    # 显示AI日期指令
    print("\n=== AI日期使用指令 ===")
    formatted_date = os.environ.get('SYSTEM_CURRENT_DATE_FORMATTED', '2025年07月26日')
    iso_date = os.environ.get('SYSTEM_CURRENT_DATE', '2025-07-26')
    full_datetime = os.environ.get('SYSTEM_CURRENT_DATETIME', '2025-07-26 00:00:00')
    weekday = os.environ.get('SYSTEM_CURRENT_WEEKDAY', '周六')
    
    instruction = f"""当前系统日期: {formatted_date} ({weekday})
ISO格式: {iso_date}
完整时间: {full_datetime}

重要提醒:
1. 在生成任何需要日期的内容时，请使用上述当前系统日期
2. 不要使用AI训练数据中的历史日期或进行日期推测
3. 如需引用具体日期，请使用: {formatted_date}
4. 环境变量 SYSTEM_CURRENT_DATE_FORMATTED 包含格式化日期
5. 可读取 tools/current_date.json 获取完整日期信息"""
    
    print(instruction)
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()