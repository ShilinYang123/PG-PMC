#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录扫描器模块

提供统一的目录扫描功能，确保update_structure.py和check_structure.py
使用完全相同的扫描逻辑和排除规则。

作者: 3AI工作室
创建时间: 2025-06-24
"""

import os
import sys
from pathlib import Path
from typing import Set, List
import logging

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from tools.config_loader import ConfigLoader


logger = logging.getLogger(__name__)


class DirectoryScanner:
    """统一的目录扫描器"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config_loader = config_loader
        self.config = config_loader.config
        self.project_root = config_loader.project_root
        
        # 从配置中获取排除规则
        structure_config = self.config.get('structure_check', {})
        self.excluded_dirs = set(structure_config.get('excluded_dirs', []))
        self.excluded_dirs_for_redundancy = set(structure_config.get('excluded_dirs_for_redundancy', []))
        
        # 系统目录（从配置文件读取，如果配置文件中没有则使用默认值）
        default_system_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            '.vscode', '.idea', 'dist', 'build', '.env'
        }
        self.system_dirs = set(structure_config.get('system_dirs', default_system_dirs))
        
        # 合并所有排除目录
        self.all_excluded_dirs = self.excluded_dirs | self.system_dirs
        
        # bak和logs目录的标准子目录（从配置文件读取）
        default_bak_subdirs = {
            'github_repo', '专项备份', '常规备份', '待清理资料', '迁移备份'
        }
        default_logs_subdirs = {
            'archive', '其他日志', '工作记录', '检查报告'
        }
        self.bak_standard_subdirs = set(structure_config.get('bak_standard_subdirs', default_bak_subdirs))
        self.logs_standard_subdirs = set(structure_config.get('logs_standard_subdirs', default_logs_subdirs))
        
        # 忽略的文件扩展名和文件名（从配置文件读取）
        self.ignore_file_extensions = set(structure_config.get('ignore_file_extensions', [
            '.tmp', '.bak', '.swp', '.log', '.pyc', '.pyo',
            '.db', '.sqlite', '.cache'
        ]))
        self.ignore_files = set(structure_config.get('ignore_files', [
            'Thumbs.db', '.DS_Store', 'Everything.db',
            'desktop.ini', '.gitkeep'
        ]))
    
    def should_ignore_directory(self, dir_name: str, parent_path: str = "") -> bool:
        """判断是否应该忽略某个目录"""
        # 检查是否在排除列表中
        if dir_name in self.all_excluded_dirs:
            return True
        
        # 检查隐藏目录
        if dir_name.startswith('.'):
            return True
        
        # 检查临时目录模式
        temp_patterns = ['temp', 'tmp', 'cache', 'backup']
        if any(pattern in dir_name.lower() for pattern in temp_patterns):
            return True
        
        return False
    
    def should_ignore_file(self, file_name: str, parent_path: str = "") -> bool:
        """判断是否应该忽略某个文件"""
        # 检查文件扩展名（从配置文件读取）
        file_ext = Path(file_name).suffix.lower()
        if file_ext in self.ignore_file_extensions:
            return True
        
        # 检查特殊文件名（从配置文件读取）
        if file_name in self.ignore_files:
            return True
        
        # 检查临时文件模式
        if file_name.startswith('~') or file_name.endswith('~'):
            return True
        
        return False
    
    def scan_directory_structure(self, for_standard_list: bool = True) -> Set[str]:
        """扫描目录结构
        
        Args:
            for_standard_list: 是否为生成标准清单（True）还是检查对比（False）
        
        Returns:
            包含所有路径的集合
        """
        paths = set()
        
        def scan_recursive(current_path: Path, relative_path: str = ""):
            try:
                for item in sorted(current_path.iterdir()):
                    item_relative = f"{relative_path}/{item.name}" if relative_path else item.name
                    
                    if item.is_dir():
                        # 检查是否应该忽略此目录
                        if self.should_ignore_directory(item.name, relative_path):
                            continue
                        
                        # 特殊处理bak和logs目录
                        if item.name == 'bak':
                            self._handle_bak_directory(item, item_relative, paths, for_standard_list)
                        elif item.name == 'logs':
                            self._handle_logs_directory(item, item_relative, paths, for_standard_list)
                        else:
                            # 普通目录处理
                            paths.add(f"{item_relative}/")
                            scan_recursive(item, item_relative)
                    
                    elif item.is_file():
                        # 检查是否应该忽略此文件
                        if self.should_ignore_file(item.name, relative_path):
                            continue
                        
                        # 特殊处理：如果父目录是bak或logs，根据规则决定是否包含
                        parent_parts = relative_path.split('/') if relative_path else []
                        if 'bak' in parent_parts or 'logs' in parent_parts:
                            # 对于bak和logs目录下的文件，只在非标准清单模式下才可能包含
                            if for_standard_list:
                                continue  # 标准清单模式下完全排除
                            else:
                                # 检查模式下也排除，保持一致
                                continue
                        
                        paths.add(item_relative)
            
            except PermissionError:
                logger.warning(f"无法访问目录: {current_path}")
            except Exception as e:
                logger.error(f"扫描目录时出错 {current_path}: {e}")
        
        # 从项目根目录开始扫描
        scan_recursive(self.project_root)
        
        return paths
    
    def _handle_bak_directory(self, bak_path: Path, relative_path: str, 
                            paths: Set[str], for_standard_list: bool):
        """处理bak目录的特殊逻辑"""
        paths.add(f"{relative_path}/")
        
        # 只添加标准子目录
        try:
            for item in sorted(bak_path.iterdir()):
                if item.is_dir() and item.name in self.bak_standard_subdirs:
                    subdir_relative = f"{relative_path}/{item.name}"
                    paths.add(f"{subdir_relative}/")
                    # 不递归扫描bak子目录的内容
        except PermissionError:
            logger.warning(f"无法访问bak目录: {bak_path}")
        except Exception as e:
            logger.error(f"处理bak目录时出错 {bak_path}: {e}")
    
    def _handle_logs_directory(self, logs_path: Path, relative_path: str,
                             paths: Set[str], for_standard_list: bool):
        """处理logs目录的特殊逻辑"""
        paths.add(f"{relative_path}/")
        
        # 只添加标准子目录
        try:
            for item in sorted(logs_path.iterdir()):
                if item.is_dir() and item.name in self.logs_standard_subdirs:
                    subdir_relative = f"{relative_path}/{item.name}"
                    paths.add(f"{subdir_relative}/")
                    # 不递归扫描logs子目录的内容
        except PermissionError:
            logger.warning(f"无法访问logs目录: {logs_path}")
        except Exception as e:
            logger.error(f"处理logs目录时出错 {logs_path}: {e}")
    
    def get_statistics(self, paths: Set[str]) -> dict:
        """获取路径统计信息"""
        directories = sum(1 for path in paths if path.endswith('/'))
        files = len(paths) - directories
        
        # 统计模板文件
        template_files = sum(1 for path in paths 
                           if not path.endswith('/') and 
                           ('模板' in path or 'template' in path.lower()))
        
        return {
            'directories': directories,
            'files': files,
            'template_files': template_files,
            'total': len(paths)
        }