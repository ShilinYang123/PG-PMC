#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统当前日期获取工具
确保AI和脚本使用正确的系统当前日期，而不是训练数据中的历史日期

使用方法:
1. 直接运行: python tools/get_current_date.py
2. 导入使用: from tools.get_current_date import get_system_date
3. 读取配置文件: tools/current_date.json
4. 读取环境变量: SYSTEM_CURRENT_DATE_FORMATTED
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def get_system_date():
    """获取当前系统日期（多种格式）"""
    try:
        now = datetime.now()
        
        date_info = {
            'timestamp': now.isoformat(),
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'formatted': now.strftime('%Y年%m月%d日'),
            'year': str(now.year),
            'month': str(now.month),
            'day': str(now.day),
            'weekday': now.strftime('%A'),
            'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()],
            'unix_timestamp': str(int(now.timestamp()))
        }
        
        return date_info
        
    except Exception as e:
        print(f"获取系统日期失败: {e}")
        # 返回默认值
        return {
            'timestamp': '2025-07-26T00:00:00',
            'date': '2025-07-26',
            'datetime': '2025-07-26 00:00:00',
            'formatted': '2025年07月26日',
            'year': '2025',
            'month': '7',
            'day': '26',
            'weekday': 'Friday',
            'weekday_cn': '周五',
            'unix_timestamp': '1721952000'
        }

def update_date_config():
    """更新日期配置文件"""
    try:
        # 获取当前日期
        date_info = get_system_date()
        
        # 获取工具目录路径
        tools_dir = Path(__file__).parent
        
        # 创建JSON格式的日期配置文件
        date_config_file = tools_dir / "current_date.json"
        
        config_data = {
            "system_date_info": date_info,
            "last_updated": date_info['timestamp'],
            "ai_instructions": {
                "current_date": date_info['date'],
                "formatted_date": date_info['formatted'],
                "usage_note": "AI应使用此文件中的日期信息，而不是训练数据中的历史日期",
                "priority": "系统当前日期优先于AI知识库中的日期信息"
            }
        }
        
        with open(date_config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
            
        print(f"✓ 日期配置文件已更新: {date_config_file}")
        
        # 同时创建简单的文本文件供快速读取
        date_text_file = tools_dir / "current_date.txt"
        with open(date_text_file, 'w', encoding='utf-8') as f:
            f.write(f"当前系统日期: {date_info['formatted']}\n")
            f.write(f"ISO格式: {date_info['date']}\n")
            f.write(f"完整时间: {date_info['datetime']}\n")
            f.write(f"星期: {date_info['weekday_cn']}\n")
            f.write(f"\n注意: AI应使用此文件中的日期，而不是训练数据中的历史日期\n")
            
        print(f"✓ 日期文本文件已更新: {date_text_file}")
        
        # 设置环境变量
        os.environ['SYSTEM_CURRENT_DATE'] = date_info['date']
        os.environ['SYSTEM_CURRENT_DATETIME'] = date_info['datetime']
        os.environ['SYSTEM_CURRENT_DATE_FORMATTED'] = date_info['formatted']
        os.environ['SYSTEM_CURRENT_YEAR'] = date_info['year']
        os.environ['SYSTEM_CURRENT_MONTH'] = date_info['month']
        os.environ['SYSTEM_CURRENT_DAY'] = date_info['day']
        os.environ['SYSTEM_CURRENT_WEEKDAY'] = date_info['weekday_cn']
        os.environ['SYSTEM_TIMESTAMP'] = date_info['timestamp']
        
        print("✓ 日期环境变量已设置")
        
        return date_info
        
    except Exception as e:
        print(f"更新日期配置失败: {e}")
        return None

def display_date_info():
    """显示当前日期信息"""
    date_info = get_system_date()
    
    print("=== 系统当前日期信息 ===")
    print(f"当前日期: {date_info['formatted']} ({date_info['weekday_cn']})")
    print(f"ISO格式: {date_info['date']}")
    print(f"完整时间: {date_info['datetime']}")
    print(f"时间戳: {date_info['timestamp']}")
    print(f"年份: {date_info['year']}")
    print(f"月份: {date_info['month']}")
    print(f"日期: {date_info['day']}")
    print(f"星期: {date_info['weekday_cn']}")
    print("")
    print("⚠️ AI重要提醒:")
    print("- 在生成任何需要日期的内容时，请使用上述当前系统日期")
    print("- 不要使用AI训练数据中的历史日期或进行日期推测")
    print("- 可通过环境变量 SYSTEM_CURRENT_DATE_FORMATTED 获取格式化日期")
    print("- 可读取 tools/current_date.json 获取完整日期信息")
    print("=== 结束 ===")
    
    return date_info

def get_ai_date_instruction():
    """获取AI日期使用指令"""
    date_info = get_system_date()
    
    instruction = f"""=== AI日期使用指令 ===
当前系统日期: {date_info['formatted']} ({date_info['weekday_cn']})
ISO格式: {date_info['date']}
完整时间: {date_info['datetime']}

重要提醒:
1. 在生成任何需要日期的内容时，请使用上述当前系统日期
2. 不要使用AI训练数据中的历史日期或进行日期推测
3. 如需引用具体日期，请使用: {date_info['formatted']}
4. 环境变量 SYSTEM_CURRENT_DATE_FORMATTED 也包含此信息
5. 可读取 tools/current_date.json 获取完整日期信息

=== 结束 ==="""
    
    return instruction

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="系统当前日期获取工具")
    parser.add_argument("--display", action="store_true", help="显示当前日期信息")
    parser.add_argument("--update", action="store_true", help="更新日期配置文件")
    parser.add_argument("--instruction", action="store_true", help="显示AI日期使用指令")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--format", choices=['date', 'datetime', 'formatted', 'timestamp'], 
                       help="指定输出格式")
    
    args = parser.parse_args()
    
    if args.update:
        update_date_config()
    elif args.instruction:
        print(get_ai_date_instruction())
    elif args.json:
        date_info = get_system_date()
        print(json.dumps(date_info, ensure_ascii=False, indent=2))
    elif args.format:
        date_info = get_system_date()
        print(date_info[args.format])
    elif args.display:
        display_date_info()
    else:
        # 默认显示格式化日期
        date_info = get_system_date()
        print(date_info['formatted'])

if __name__ == "__main__":
    main()