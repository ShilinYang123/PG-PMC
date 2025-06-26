#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误路径检测器
用于检测和清理项目中的错误文件路径
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


def run_error_detection(
    project_root: Path,
    cleanup_dir: Path,
    move_files: bool = True,
    logger=None
) -> Tuple[bool, Optional[str]]:
    """
    运行错误路径检测

    Args:
        project_root: 项目根目录
        cleanup_dir: 清理目录
        move_files: 是否移动文件
        logger: 日志记录器

    Returns:
        (success, report_file): 成功状态和报告文件路径
    """
    try:
        if logger:
            logger.info("开始错误路径检测...")

        # 确保清理目录存在
        cleanup_dir.mkdir(parents=True, exist_ok=True)

        # 生成报告文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = cleanup_dir / f"error_detection_report_{timestamp}.md"

        # 检测错误路径
        error_files = []
        temp_files = []
        duplicate_files = []
        
        # 检测常见的错误文件模式
        error_patterns = [
            '*.tmp', '*.temp', '*.bak', '*.backup',
            '*.log', '*.cache', '*.swp', '*.swo',
            '*~', '*.orig', '*.rej', '.DS_Store',
            'Thumbs.db', '*.pyc', '__pycache__',
            'node_modules/.cache', '.pytest_cache'
        ]
        
        if logger:
            logger.info("扫描错误文件模式...")
            
        for pattern in error_patterns:
            for file_path in project_root.rglob(pattern):
                if file_path.is_file():
                    temp_files.append(file_path)
                elif file_path.is_dir() and pattern in ['__pycache__', 'node_modules/.cache', '.pytest_cache']:
                    temp_files.append(file_path)
        
        # 检测重复文件（基于文件名模式）
        duplicate_patterns = ['*_copy*', '*_副本*', '*(1)*', '*(2)*', '*_backup*']
        for pattern in duplicate_patterns:
            for file_path in project_root.rglob(pattern):
                if file_path.is_file():
                    duplicate_files.append(file_path)
        
        # 检测空目录
        empty_dirs = []
        for dir_path in project_root.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                # 跳过一些应该保留的空目录
                if dir_path.name not in ['.git', 'logs', 'temp', 'cache']:
                    empty_dirs.append(dir_path)
        
        # 移动或记录错误文件
        moved_files = []
        if move_files and (temp_files or duplicate_files):
            error_backup_dir = cleanup_dir / "error_files" / timestamp
            error_backup_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in temp_files + duplicate_files:
                try:
                    relative_path = file_path.relative_to(project_root)
                    target_path = error_backup_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if file_path.is_file():
                        shutil.move(str(file_path), str(target_path))
                    elif file_path.is_dir():
                        shutil.move(str(file_path), str(target_path))
                    
                    moved_files.append((file_path, target_path))
                    if logger:
                        logger.info(f"移动错误文件: {file_path} -> {target_path}")
                except Exception as e:
                    if logger:
                        logger.warning(f"移动文件失败 {file_path}: {e}")
        
        # 生成报告内容
        total_issues = len(temp_files) + len(duplicate_files) + len(empty_dirs)
        
        report_content = f"""# 错误路径检测报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**项目根目录**: {project_root}
**清理目录**: {cleanup_dir}
**移动文件**: {'是' if move_files else '否'}

## 检测结果

### 临时文件 ({len(temp_files)} 个)
"""
        
        if temp_files:
            for file_path in temp_files[:10]:  # 只显示前10个
                report_content += f"- {file_path.relative_to(project_root)}\n"
            if len(temp_files) > 10:
                report_content += f"- ... 还有 {len(temp_files) - 10} 个文件\n"
        else:
            report_content += "- 无临时文件\n"
        
        report_content += f"\n### 重复文件 ({len(duplicate_files)} 个)\n"
        if duplicate_files:
            for file_path in duplicate_files[:10]:
                report_content += f"- {file_path.relative_to(project_root)}\n"
            if len(duplicate_files) > 10:
                report_content += f"- ... 还有 {len(duplicate_files) - 10} 个文件\n"
        else:
            report_content += "- 无重复文件\n"
        
        report_content += f"\n### 空目录 ({len(empty_dirs)} 个)\n"
        if empty_dirs:
            for dir_path in empty_dirs[:10]:
                report_content += f"- {dir_path.relative_to(project_root)}\n"
            if len(empty_dirs) > 10:
                report_content += f"- ... 还有 {len(empty_dirs) - 10} 个目录\n"
        else:
            report_content += "- 无空目录\n"
        
        if moved_files:
            report_content += f"\n### 已移动文件 ({len(moved_files)} 个)\n"
            for original, target in moved_files[:10]:
                report_content += f"- {original.relative_to(project_root)} -> {target}\n"
            if len(moved_files) > 10:
                report_content += f"- ... 还有 {len(moved_files) - 10} 个文件\n"
        
        report_content += f"\n## 总结\n\n"
        if total_issues == 0:
            report_content += "✅ 项目目录结构符合规范，无需额外清理操作。\n"
        else:
            report_content += f"⚠️ 发现 {total_issues} 个问题项目。\n"
            if move_files and moved_files:
                report_content += f"✅ 已移动 {len(moved_files)} 个问题文件到备份目录。\n"
            elif not move_files:
                report_content += "ℹ️ 未启用文件移动，仅生成检测报告。\n"

        # 写入报告文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        if logger:
            logger.info(f"错误路径检测完成，报告已生成: {report_file}")

        return True, str(report_file)

    except Exception as e:
        if logger:
            logger.error(f"错误路径检测失败: {e}")
        return False, None


if __name__ == "__main__":
    # 测试代码
    from pathlib import Path
    import yaml

    # 从配置文件读取项目根目录
    config_path = Path(__file__).parent.parent / "docs" / \
        "03-管理" / "project_config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        project_root = Path(config['paths']['root'])
    except Exception:
        # 备用方案
        project_root = Path(__file__).parent.parent

    cleanup_dir = project_root / "logs" / "error_detection"

    success, report = run_error_detection(project_root, cleanup_dir)
    print(f"检测结果: {success}")
    if report:
        print(f"报告文件: {report}")
