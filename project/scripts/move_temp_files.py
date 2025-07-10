#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动暂时无用的文件到待清理资料目录
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import json

def move_temp_files():
    """
    移动暂时无用的文件到待清理资料目录
    """
    
    # 获取当前日期戳
    date_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 目标目录
    target_dir = Path(f"s:/PG-Dev/bak/待清理资料/临时文件清理_{date_stamp}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 从分析结果中获取需要移动的文件
    analysis_file = "s:/PG-Dev/project/temp/file_analysis_result.json"
    
    if not os.path.exists(analysis_file):
        print("❌ 分析结果文件不存在，请先运行 analyze_extra_files.py")
        return
    
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
    
    # 需要移动的文件（建议清除的临时文件）
    files_to_move = analysis.get('remove', [])
    
    moved_files = []
    failed_files = []
    
    print(f"📁 创建目标目录: {target_dir}")
    print(f"🚚 开始移动 {len(files_to_move)} 个临时文件...")
    print("=" * 60)
    
    for item in files_to_move:
        source_path = Path(f"s:/PG-Dev/{item}")
        
        if not source_path.exists():
            print(f"⚠️  源文件不存在: {item}")
            failed_files.append(f"{item} (不存在)")
            continue
        
        # 计算相对路径并创建目标路径
        relative_path = Path(item)
        target_path = target_dir / relative_path
        
        try:
            # 确保目标目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件或目录
            if source_path.is_file():
                shutil.move(str(source_path), str(target_path))
                print(f"✅ 移动文件: {item}")
            elif source_path.is_dir():
                shutil.move(str(source_path), str(target_path))
                print(f"✅ 移动目录: {item}")
            
            moved_files.append(item)
            
        except Exception as e:
            print(f"❌ 移动失败: {item} - {e}")
            failed_files.append(f"{item} ({e})")
    
    print("=" * 60)
    print(f"📊 移动完成统计:")
    print(f"  ✅ 成功移动: {len(moved_files)} 个")
    print(f"  ❌ 移动失败: {len(failed_files)} 个")
    
    # 生成移动报告
    report_content = f"""# 临时文件移动报告

**移动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**目标目录**: {target_dir}

## 移动统计

- 总计文件: {len(files_to_move)} 个
- 成功移动: {len(moved_files)} 个
- 移动失败: {len(failed_files)} 个

## 成功移动的文件

"""
    
    for file in moved_files:
        report_content += f"- ✅ {file}\n"
    
    if failed_files:
        report_content += "\n## 移动失败的文件\n\n"
        for file in failed_files:
            report_content += f"- ❌ {file}\n"
    
    # 保存报告
    report_path = target_dir / "移动报告.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n📄 移动报告已保存: {report_path}")
    
    return moved_files, failed_files, str(target_dir)

def main():
    """
    主函数
    """
    print("=" * 80)
    print("临时文件移动工具")
    print("=" * 80)
    
    moved_files, failed_files, target_dir = move_temp_files()
    
    print("\n💡 提示:")
    print("  1. 移动的文件已保存到待清理资料目录")
    print("  2. 如需恢复文件，可从目标目录复制回原位置")
    print("  3. 确认无用后可定期清理待清理资料目录")
    print(f"  4. 目标目录: {target_dir}")

if __name__ == "__main__":
    main()