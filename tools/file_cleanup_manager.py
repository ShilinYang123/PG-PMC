#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 文件清理管理工具

这是一个通用的文件清理管理工具，用于：
1. 分析多余文件和目录
2. 自动移动临时文件到待清理目录
3. 生成清理报告
4. 支持批量操作和回滚

作者：雨俊
创建时间：2025-01-10
"""

import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in os.sys.path:
    os.sys.path.insert(0, str(project_root))

from tools.logging_config import get_logger
from tools.exceptions import FileSystemError

class FileCleanupManager:
    """文件清理管理器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化清理管理器
        
        Args:
            project_root: 项目根目录，默认为当前脚本的上级目录
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.backup_dir = self.project_root / "bak" / "待清理资料"
        self.logger = get_logger("file_cleanup")
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_extra_files(self, extra_items: List[str]) -> Dict[str, List[str]]:
        """分析多余文件，分类为保留、清除、需要确认
        
        Args:
            extra_items: 多余项目列表
            
        Returns:
            分类结果字典
        """
        result = {
            "keep": [],      # 保留的文件
            "remove": [],    # 建议清除的临时文件
            "confirm": []    # 需要确认的文件
        }
        
        for item in extra_items:
            if self._should_keep(item):
                result["keep"].append(item)
            elif self._should_remove(item):
                result["remove"].append(item)
            else:
                result["confirm"].append(item)
        
        return result
    
    def _should_keep(self, item: str) -> bool:
        """判断是否应该保留文件"""
        keep_patterns = [
            # 核心配置文件
            "project/config/",
            "project/.gitignore",
            "project/requirements.txt",
            "project/setup.cfg",
            "project/package.json",
            
            # 重要的源代码
            "project/src/",
            
            # 重要的文档
            "docs/01-设计/",
            "docs/03-管理/",
            
            # 数据目录（可能包含重要数据）
            "project/data/knowledge_base",
            
            # 插件目录
            "project/plugins/",
        ]
        
        return any(pattern in item for pattern in keep_patterns)
    
    def _should_remove(self, item: str) -> bool:
        """判断是否应该清除文件"""
        remove_patterns = [
            # 测试覆盖率文件
            ".coverage",
            "htmlcov/",
            
            # 调试和测试脚本
            "debug_",
            "test_",
            "simple_test.py",
            "test_duplicate.py",
            
            # 临时日志文件
            "enhanced_check_debug_",
            
            # 临时目录
            "project/temp/",
            "project/backups/",
            
            # 缓存文件
            "__pycache__/",
            ".pytest_cache/",
        ]
        
        return any(pattern in item for pattern in remove_patterns)
    
    def move_files(self, files_to_move: List[str], 
                   operation_name: str = "临时文件清理") -> Tuple[List[str], List[str]]:
        """移动文件到待清理目录
        
        Args:
            files_to_move: 要移动的文件列表
            operation_name: 操作名称，用于创建目录
            
        Returns:
            (成功移动的文件列表, 失败的文件列表)
        """
        # 创建带时间戳的目标目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = self.backup_dir / f"{operation_name}_{timestamp}"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        moved_files = []
        failed_files = []
        
        self.logger.info(f"开始移动 {len(files_to_move)} 个文件到 {target_dir}")
        
        for item in files_to_move:
            try:
                source_path = self.project_root / item
                
                if not source_path.exists():
                    self.logger.warning(f"源文件不存在: {item}")
                    failed_files.append(f"{item} (不存在)")
                    continue
                
                # 计算目标路径，保持相对路径结构
                relative_path = Path(item)
                target_path = target_dir / relative_path
                
                # 确保目标目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件或目录
                if source_path.is_file():
                    shutil.move(str(source_path), str(target_path))
                    self.logger.info(f"✓ 移动文件: {item}")
                elif source_path.is_dir():
                    shutil.move(str(source_path), str(target_path))
                    self.logger.info(f"✓ 移动目录: {item}")
                
                moved_files.append(item)
                
            except Exception as e:
                error_msg = f"{item} (错误: {str(e)})"
                self.logger.error(f"移动失败: {error_msg}")
                failed_files.append(error_msg)
        
        # 生成移动报告
        self._generate_move_report(target_dir, moved_files, failed_files, operation_name)
        
        return moved_files, failed_files
    
    def _generate_move_report(self, target_dir: Path, moved_files: List[str], 
                             failed_files: List[str], operation_name: str):
        """生成移动操作报告"""
        report_content = f"""# {operation_name}报告

## 操作信息
- 操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 目标目录: {target_dir}
- 成功移动: {len(moved_files)} 个项目
- 失败项目: {len(failed_files)} 个项目

## 成功移动的文件
"""
        
        for file in moved_files:
            report_content += f"- ✓ {file}\n"
        
        if failed_files:
            report_content += "\n## 失败的文件\n"
            for file in failed_files:
                report_content += f"- ❌ {file}\n"
        
        report_content += f"\n## 恢复说明\n如需恢复文件，请从 {target_dir} 目录中复制回原位置。\n"
        
        # 保存报告
        report_path = target_dir / "移动报告.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"移动报告已保存: {report_path}")
    
    def cleanup_by_analysis(self, extra_items: List[str], 
                           auto_confirm: bool = False) -> Dict[str, any]:
        """根据分析结果执行清理
        
        Args:
            extra_items: 多余项目列表
            auto_confirm: 是否自动确认清理需要确认的文件
            
        Returns:
            清理结果统计
        """
        # 分析文件
        analysis = self.analyze_extra_files(extra_items)
        
        self.logger.info(f"分析结果: 保留 {len(analysis['keep'])} 个, "
                        f"清除 {len(analysis['remove'])} 个, "
                        f"需确认 {len(analysis['confirm'])} 个")
        
        # 移动建议清除的文件
        moved_files, failed_files = [], []
        if analysis['remove']:
            moved_files, failed_files = self.move_files(analysis['remove'])
        
        # 处理需要确认的文件
        confirmed_files = []
        if analysis['confirm'] and auto_confirm:
            confirmed_moved, confirmed_failed = self.move_files(
                analysis['confirm'], "需确认文件清理"
            )
            confirmed_files = confirmed_moved
            failed_files.extend(confirmed_failed)
        
        return {
            "analysis": analysis,
            "moved_files": moved_files,
            "confirmed_files": confirmed_files,
            "failed_files": failed_files,
            "total_cleaned": len(moved_files) + len(confirmed_files)
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文件清理管理工具")
    parser.add_argument("--files", nargs="+", help="要处理的文件列表")
    parser.add_argument("--auto-confirm", action="store_true", 
                       help="自动确认清理需要确认的文件")
    parser.add_argument("--analyze-only", action="store_true", 
                       help="仅分析，不执行清理")
    parser.add_argument("--from-check-result", action="store_true", 
                       help="从最新的检查报告中获取多余文件列表")
    
    args = parser.parse_args()
    
    # 创建清理管理器
    manager = FileCleanupManager()
    
    # 获取要处理的文件列表
    if args.from_check_result:
        # 从最新的检查报告中获取多余文件
        # 这里可以添加读取检查报告的逻辑
        print("从检查报告获取多余文件功能待实现")
        return
    elif args.files:
        extra_items = args.files
    else:
        # 默认的测试文件列表
        extra_items = [
            ".coverage",
            "enhanced_check_debug_20250710_172104.log",
            "simple_test.py",
            "test_duplicate.py"
        ]
    
    if args.analyze_only:
        # 仅分析
        analysis = manager.analyze_extra_files(extra_items)
        print("\n=== 文件分析结果 ===")
        print(f"保留文件 ({len(analysis['keep'])}):", analysis['keep'])
        print(f"建议清除 ({len(analysis['remove'])}):", analysis['remove'])
        print(f"需要确认 ({len(analysis['confirm'])}):", analysis['confirm'])
    else:
        # 执行清理
        result = manager.cleanup_by_analysis(extra_items, args.auto_confirm)
        print("\n=== 清理完成 ===")
        print(f"总共清理了 {result['total_cleaned']} 个项目")
        print(f"成功移动: {len(result['moved_files'])} 个")
        print(f"确认移动: {len(result['confirmed_files'])} 个")
        print(f"失败项目: {len(result['failed_files'])} 个")

if __name__ == "__main__":
    main()