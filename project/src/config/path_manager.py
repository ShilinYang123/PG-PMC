#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理器
统一管理项目中的所有路径配置，提供路径标准化和验证功能
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class PathConfig:
    """路径配置类"""
    name: str
    path: Union[str, Path]
    description: str
    required: bool = True
    create_if_missing: bool = False
    check_permissions: List[str] = None  # ['read', 'write', 'execute']
    
    def __post_init__(self):
        if self.check_permissions is None:
            self.check_permissions = ['read']
        self.path = Path(self.path)


class PathManager:
    """路径管理器"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        self.project_root = Path(project_root or os.getenv('PG_PMC_ROOT', 's:/PG-PMC'))
        self._paths: Dict[str, PathConfig] = {}
        self._initialize_default_paths()
    
    def _initialize_default_paths(self):
        """初始化默认路径配置"""
        default_paths = [
            PathConfig(
                name='root',
                path=self.project_root,
                description='项目根目录',
                required=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='docs',
                path=self.project_root / 'docs',
                description='文档目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='docs_design',
                path=self.project_root / 'docs' / '01-设计',
                description='设计文档目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='docs_development',
                path=self.project_root / 'docs' / '02-开发',
                description='开发文档目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='docs_management',
                path=self.project_root / 'docs' / '03-管理',
                description='管理文档目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='logs',
                path=self.project_root / 'logs',
                description='日志目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='logs_work',
                path=self.project_root / 'logs' / '工作记录',
                description='工作记录日志目录',
                required=False,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='logs_reports',
                path=self.project_root / 'logs' / '检查报告',
                description='检查报告目录',
                required=False,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='backup',
                path=self.project_root / 'bak',
                description='备份目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='tools',
                path=self.project_root / 'tools',
                description='工具脚本目录',
                required=True,
                check_permissions=['read', 'execute']
            ),
            PathConfig(
                name='project',
                path=self.project_root / 'project',
                description='项目代码目录',
                required=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='project_frontend',
                path=self.project_root / 'project' / 'frontend',
                description='前端项目目录',
                required=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='project_backend',
                path=self.project_root / 'project' / 'backend',
                description='后端项目目录',
                required=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='project_src',
                path=self.project_root / 'project' / 'src',
                description='源代码目录',
                required=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='config',
                path=self.project_root / 'project' / 'src' / 'config',
                description='配置文件目录',
                required=True,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='uploads',
                path=self.project_root / 'uploads',
                description='文件上传目录',
                required=False,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='temp',
                path=self.project_root / 'temp',
                description='临时文件目录',
                required=False,
                create_if_missing=True,
                check_permissions=['read', 'write']
            ),
            PathConfig(
                name='cache',
                path=self.project_root / '.cache',
                description='缓存目录',
                required=False,
                create_if_missing=True,
                check_permissions=['read', 'write']
            )
        ]
        
        for path_config in default_paths:
            self._paths[path_config.name] = path_config
    
    def add_path(self, path_config: PathConfig) -> None:
        """添加路径配置"""
        self._paths[path_config.name] = path_config
    
    def get_path(self, name: str) -> Optional[Path]:
        """获取路径"""
        path_config = self._paths.get(name)
        if path_config:
            return path_config.path
        return None
    
    def get_path_config(self, name: str) -> Optional[PathConfig]:
        """获取路径配置"""
        return self._paths.get(name)
    
    def get_all_paths(self) -> Dict[str, Path]:
        """获取所有路径"""
        return {name: config.path for name, config in self._paths.items()}
    
    def get_all_path_configs(self) -> Dict[str, PathConfig]:
        """获取所有路径配置"""
        return self._paths.copy()
    
    def normalize_path(self, path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
        """标准化路径"""
        path = Path(path)
        
        # 如果是相对路径，转换为绝对路径
        if not path.is_absolute():
            if relative_to:
                base_path = self.get_path(relative_to)
                if base_path:
                    path = base_path / path
                else:
                    path = self.project_root / path
            else:
                path = self.project_root / path
        
        # 解析路径（处理 .. 和 . ）
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            # 如果路径不存在，使用绝对路径
            path = path.absolute()
        
        return path
    
    def validate_paths(self) -> Dict[str, List[str]]:
        """验证所有路径"""
        results = {
            'valid': [],
            'missing': [],
            'permission_errors': [],
            'created': []
        }
        
        for name, config in self._paths.items():
            path = config.path
            
            # 检查路径是否存在
            if not path.exists():
                if config.required:
                    if config.create_if_missing:
                        try:
                            path.mkdir(parents=True, exist_ok=True)
                            results['created'].append(f"{name}: {path}")
                        except Exception as e:
                            results['missing'].append(f"{name}: {path} (创建失败: {e})")
                            continue
                    else:
                        results['missing'].append(f"{name}: {path}")
                        continue
                else:
                    if config.create_if_missing:
                        try:
                            path.mkdir(parents=True, exist_ok=True)
                            results['created'].append(f"{name}: {path}")
                        except Exception:
                            pass  # 非必需路径创建失败不报错
                    continue
            
            # 检查权限
            permission_errors = self._check_permissions(path, config.check_permissions)
            if permission_errors:
                results['permission_errors'].extend([
                    f"{name}: {path} ({error})" for error in permission_errors
                ])
            else:
                results['valid'].append(f"{name}: {path}")
        
        return results
    
    def _check_permissions(self, path: Path, required_permissions: List[str]) -> List[str]:
        """检查路径权限"""
        errors = []
        
        if not path.exists():
            return ['路径不存在']
        
        for permission in required_permissions:
            if permission == 'read' and not os.access(path, os.R_OK):
                errors.append('无读取权限')
            elif permission == 'write' and not os.access(path, os.W_OK):
                errors.append('无写入权限')
            elif permission == 'execute' and not os.access(path, os.X_OK):
                errors.append('无执行权限')
        
        return errors
    
    def create_missing_directories(self) -> Dict[str, str]:
        """创建缺失的目录"""
        results = {
            'created': [],
            'failed': []
        }
        
        for name, config in self._paths.items():
            path = config.path
            
            if not path.exists() and config.create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    results['created'].append(f"{name}: {path}")
                except Exception as e:
                    results['failed'].append(f"{name}: {path} (错误: {e})")
        
        return results
    
    def get_relative_path(self, path: Union[str, Path], relative_to: str = 'root') -> Optional[Path]:
        """获取相对路径"""
        path = Path(path)
        base_path = self.get_path(relative_to)
        
        if not base_path:
            return None
        
        try:
            return path.relative_to(base_path)
        except ValueError:
            # 路径不在基础路径下
            return None
    
    def is_under_project(self, path: Union[str, Path]) -> bool:
        """检查路径是否在项目目录下"""
        path = Path(path).resolve()
        try:
            path.relative_to(self.project_root.resolve())
            return True
        except ValueError:
            return False
    
    def get_config_paths(self) -> Dict[str, str]:
        """获取配置格式的路径字典"""
        return {
            name: str(config.path) for name, config in self._paths.items()
        }
    
    def update_project_root(self, new_root: Union[str, Path]) -> None:
        """更新项目根目录"""
        old_root = self.project_root
        new_root = Path(new_root)
        
        # 更新项目根目录
        self.project_root = new_root
        
        # 更新所有相对于根目录的路径
        for name, config in self._paths.items():
            try:
                # 尝试获取相对于旧根目录的路径
                relative_path = config.path.relative_to(old_root)
                # 更新为新根目录下的路径
                config.path = new_root / relative_path
            except ValueError:
                # 如果路径不在旧根目录下，保持不变
                pass
    
    def export_env_vars(self) -> Dict[str, str]:
        """导出环境变量格式的路径"""
        env_vars = {}
        
        # 主要路径
        env_vars['PG_PMC_ROOT'] = str(self.project_root)
        env_vars['PG_PMC_DOCS'] = str(self.get_path('docs'))
        env_vars['PG_PMC_LOGS'] = str(self.get_path('logs'))
        env_vars['PG_PMC_TOOLS'] = str(self.get_path('tools'))
        env_vars['PG_PMC_PROJECT'] = str(self.get_path('project'))
        env_vars['PG_PMC_BACKUP'] = str(self.get_path('backup'))
        env_vars['PG_PMC_CONFIG'] = str(self.get_path('config'))
        
        # 项目子目录
        env_vars['PG_PMC_FRONTEND'] = str(self.get_path('project_frontend'))
        env_vars['PG_PMC_BACKEND'] = str(self.get_path('project_backend'))
        
        # 运行时目录
        env_vars['PG_PMC_UPLOADS'] = str(self.get_path('uploads'))
        env_vars['PG_PMC_TEMP'] = str(self.get_path('temp'))
        env_vars['PG_PMC_CACHE'] = str(self.get_path('cache'))
        
        return env_vars


# 全局路径管理器实例
path_manager = PathManager()


def get_path_manager() -> PathManager:
    """获取路径管理器实例"""
    return path_manager


def get_project_path(name: str) -> Optional[Path]:
    """获取项目路径"""
    return path_manager.get_path(name)


def normalize_project_path(path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
    """标准化项目路径"""
    return path_manager.normalize_path(path, relative_to)


def validate_project_paths() -> Dict[str, List[str]]:
    """验证项目路径"""
    return path_manager.validate_paths()


if __name__ == '__main__':
    # 测试路径管理器
    pm = PathManager()
    
    print("项目路径配置:")
    for name, path in pm.get_all_paths().items():
        print(f"  {name}: {path}")
    
    print("\n路径验证结果:")
    validation = pm.validate_paths()
    
    for category, paths in validation.items():
        if paths:
            print(f"\n{category}:")
            for path in paths:
                print(f"  - {path}")
    
    print("\n环境变量:")
    env_vars = pm.export_env_vars()
    for key, value in env_vars.items():
        print(f"  {key}={value}")