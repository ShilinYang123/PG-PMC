#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析多余文件和目录，区分核心内容和临时文件
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple

def analyze_extra_items() -> Dict[str, List[str]]:
    """
    分析多余项目，分类为：保留、清除、需要确认
    """
    
    # 从检查报告中提取的多余项目列表
    extra_items = [
        "docs/02-开发/Git提交前检查系统使用说明.md",
        "project/.gitignore",
        "project/backups",
        "project/config",
        "project/config/README.md",
        "project/config/default.yaml",
        "project/config/settings.yaml",
        "project/config/user_settings.yaml",
        "project/data",
        "project/data/knowledge_base",
        "project/htmlcov",
        "project/logs",
        "project/logs/pingao_ai.log",
        "project/logs/pingao_ai_audit.log",
        "project/logs/pingao_ai_error.log",
        "project/logs/pingao_ai_performance.log",
        "project/logs/检查报告",
        "project/logs/检查报告/enhanced_check_debug_20250710_142559.log",
        "project/plugins",
        "project/scripts/check_config.py",
        "project/scripts/create_cylinder.py",
        "project/scripts/debug_config.py",
        "project/scripts/debug_env_override.py",
        "project/scripts/debug_merge.py",
        "project/scripts/init_config.py",
        "project/scripts/test_config.py",
        "project/scripts/test_creo_config.py",
        "project/scripts/test_env_vars.py",
        "project/scripts/test_settings_fromdict.py",
        "project/src/creo/api_wrapper.py",
        "project/src/creo/geometry_operations.py",
        "project/temp",
        "project/uploads",
        "tools/git_pre_commit_check.py"
    ]
    
    # 分类规则
    keep_items = []  # 项目核心内容，需要保留
    remove_items = []  # 临时文件，可以清除
    confirm_items = []  # 需要确认的项目
    
    for item in extra_items:
        if should_keep(item):
            keep_items.append(item)
        elif should_remove(item):
            remove_items.append(item)
        else:
            confirm_items.append(item)
    
    return {
        "keep": keep_items,
        "remove": remove_items,
        "confirm": confirm_items
    }

def should_keep(item: str) -> bool:
    """
    判断是否应该保留的项目核心内容
    """
    keep_patterns = [
        # 配置文件 - 项目核心
        "project/config",
        "project/.gitignore",
        
        # 源代码文件 - 项目核心
        "project/src/creo/api_wrapper.py",
        "project/src/creo/geometry_operations.py",
        
        # 重要脚本 - 项目核心
        "project/scripts/create_cylinder.py",
        "project/scripts/init_config.py",
        
        # 数据目录 - 项目核心
        "project/data",
        "project/data/knowledge_base",
        
        # 插件目录 - 项目核心
        "project/plugins",
        
        # 上传目录 - 项目核心
        "project/uploads",
        
        # 重要工具
        "tools/git_pre_commit_check.py",
        
        # 重要文档
        "docs/02-开发/Git提交前检查系统使用说明.md"
    ]
    
    return any(pattern in item for pattern in keep_patterns)

def should_remove(item: str) -> bool:
    """
    判断是否应该清除的临时文件
    """
    remove_patterns = [
        # 测试覆盖率文件 - 临时文件
        "project/htmlcov",
        
        # 临时目录
        "project/temp",
        
        # 备份目录
        "project/backups",
        
        # 调试和测试脚本 - 临时文件
        "project/scripts/debug_",
        "project/scripts/test_",
        "project/scripts/check_config.py",
        
        # 日志文件 - 临时文件
        "project/logs/pingao_ai",
        "project/logs/检查报告"
    ]
    
    return any(pattern in item for pattern in remove_patterns)

def get_file_size(filepath: str) -> str:
    """
    获取文件大小
    """
    try:
        full_path = Path("s:/PG-Dev") / filepath
        if full_path.exists():
            if full_path.is_file():
                size = full_path.stat().st_size
                if size < 1024:
                    return f"{size}B"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f}KB"
                else:
                    return f"{size/(1024*1024):.1f}MB"
            else:
                # 目录大小
                total_size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
                if total_size < 1024 * 1024:
                    return f"{total_size/1024:.1f}KB"
                else:
                    return f"{total_size/(1024*1024):.1f}MB"
        return "不存在"
    except Exception as e:
        return f"错误: {e}"

def main():
    """
    主函数
    """
    print("=" * 80)
    print("多余文件和目录分析报告")
    print("=" * 80)
    
    analysis = analyze_extra_items()
    
    print("\n🟢 建议保留的项目核心内容:")
    print("-" * 50)
    for item in analysis["keep"]:
        size = get_file_size(item)
        print(f"  ✓ {item} ({size})")
    
    print("\n🔴 建议清除的临时文件:")
    print("-" * 50)
    for item in analysis["remove"]:
        size = get_file_size(item)
        print(f"  ✗ {item} ({size})")
    
    print("\n🟡 需要确认的项目:")
    print("-" * 50)
    for item in analysis["confirm"]:
        size = get_file_size(item)
        print(f"  ? {item} ({size})")
    
    print("\n📊 统计信息:")
    print("-" * 50)
    print(f"  保留项目: {len(analysis['keep'])} 个")
    print(f"  清除项目: {len(analysis['remove'])} 个")
    print(f"  确认项目: {len(analysis['confirm'])} 个")
    print(f"  总计: {len(analysis['keep']) + len(analysis['remove']) + len(analysis['confirm'])} 个")
    
    # 保存分析结果
    output_file = "s:/PG-Dev/project/temp/file_analysis_result.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 分析结果已保存到: {output_file}")
    print("\n💡 建议:")
    print("  1. 首先清除临时文件以释放空间")
    print("  2. 确认需要确认的项目是否为项目必需")
    print("  3. 更新目录结构标准清单以包含保留的核心内容")

if __name__ == "__main__":
    main()