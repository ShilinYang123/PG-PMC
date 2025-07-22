#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理核心模块
实现分项目管理架构，确保AI驱动程序能够准确识别和管理不同项目
避免数据混淆和张冠李戴问题
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger
from ..utils.validation import validate_project_name, validate_project_id

logger = get_logger(__name__)

@dataclass
class ProjectInfo:
    """项目信息数据类"""
    project_id: str
    project_name: str
    project_type: str
    description: str
    created_at: str
    updated_at: str
    status: str
    owner: str
    tags: List[str]
    metadata: Dict[str, Any]

class ProjectManager:
    """项目管理器 - 核心项目管理类"""
    
    def __init__(self, base_path: str = "S:\\PG-PMC\\AI调度表"):
        self.base_path = Path(base_path)
        self.projects_registry = self.base_path / "项目注册表.json"
        self.template_path = self.base_path / "项目模板"
        self.current_project_id = None  # 当前选中的项目ID
        self._ensure_directories()
        self._load_projects_registry()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.template_path.mkdir(parents=True, exist_ok=True)
        
        # 创建标准项目模板结构
        template_dirs = [
            "项目档案", "管理表", "结构化项目管理", 
            "实时数据更新", "历史记录"
        ]
        for dir_name in template_dirs:
            (self.template_path / dir_name).mkdir(exist_ok=True)
    
    def _load_projects_registry(self):
        """加载项目注册表"""
        if self.projects_registry.exists():
            try:
                with open(self.projects_registry, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
            except Exception as e:
                logger.error(f"加载项目注册表失败: {e}")
                self.registry = {}
        else:
            self.registry = {}
    
    def _save_projects_registry(self):
        """保存项目注册表"""
        try:
            with open(self.projects_registry, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存项目注册表失败: {e}")
            raise
    
    def create_project(self, project_name: str, project_type: str, 
                      description: str = "", owner: str = "", 
                      tags: List[str] = None) -> str:
        """创建新项目
        
        Args:
            project_name: 项目名称
            project_type: 项目类型
            description: 项目描述
            owner: 项目负责人
            tags: 项目标签
            
        Returns:
            str: 项目ID
        """
        # 验证项目名称
        if not validate_project_name(project_name):
            raise ValueError(f"无效的项目名称: {project_name}")
        
        # 生成项目ID
        project_id = str(uuid.uuid4())[:8]
        
        # 创建项目目录名称（项目ID_项目名称）
        project_dir_name = f"项目{project_id}_{project_name}"
        project_path = self.base_path / project_dir_name
        
        # 检查项目是否已存在
        if project_path.exists():
            raise ValueError(f"项目目录已存在: {project_dir_name}")
        
        # 创建项目信息
        now = datetime.now().isoformat()
        project_info = ProjectInfo(
            project_id=project_id,
            project_name=project_name,
            project_type=project_type,
            description=description,
            created_at=now,
            updated_at=now,
            status="active",
            owner=owner,
            tags=tags or [],
            metadata={}
        )
        
        try:
            # 创建项目目录结构
            self._create_project_structure(project_path)
            
            # 保存项目信息
            self._save_project_info(project_path, project_info)
            
            # 更新注册表
            self.registry[project_id] = {
                "project_name": project_name,
                "project_dir": project_dir_name,
                "created_at": now,
                "status": "active"
            }
            self._save_projects_registry()
            
            logger.info(f"项目创建成功: {project_dir_name} (ID: {project_id})")
            return project_id
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            # 清理可能创建的目录
            if project_path.exists():
                import shutil
                shutil.rmtree(project_path)
            raise
    
    def _create_project_structure(self, project_path: Path):
        """创建项目目录结构"""
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建标准子目录
        subdirs = [
            "项目档案", "管理表", "结构化项目管理", 
            "实时数据更新", "历史记录"
        ]
        
        for subdir in subdirs:
            (project_path / subdir).mkdir(exist_ok=True)
    
    def _save_project_info(self, project_path: Path, project_info: ProjectInfo):
        """保存项目信息到项目目录"""
        info_file = project_path / "项目档案" / "项目信息.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(project_info), f, ensure_ascii=False, indent=2)
    
    def get_project_by_id(self, project_id: str) -> Optional[ProjectInfo]:
        """根据项目ID获取项目信息"""
        if not validate_project_id(project_id):
            return None
            
        if project_id not in self.registry:
            return None
        
        project_dir = self.registry[project_id]["project_dir"]
        project_path = self.base_path / project_dir
        info_file = project_path / "项目档案" / "项目信息.json"
        
        if not info_file.exists():
            return None
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ProjectInfo(**data)
        except Exception as e:
            logger.error(f"读取项目信息失败: {e}")
            return None
    
    def get_project_by_name(self, project_name: str) -> Optional[ProjectInfo]:
        """根据项目名称获取项目信息"""
        for project_id, info in self.registry.items():
            if info["project_name"] == project_name:
                return self.get_project_by_id(project_id)
        return None
    
    def list_projects(self, status: str = None) -> List[ProjectInfo]:
        """列出所有项目"""
        projects = []
        for project_id in self.registry:
            project_info = self.get_project_by_id(project_id)
            if project_info and (status is None or project_info.status == status):
                projects.append(project_info)
        return projects
    
    def get_project_path(self, project_id: str) -> Optional[Path]:
        """获取项目路径"""
        if project_id not in self.registry:
            return None
        
        project_dir = self.registry[project_id]["project_dir"]
        return self.base_path / project_dir
    
    def update_project(self, project_id: str, **kwargs) -> bool:
        """更新项目信息"""
        project_info = self.get_project_by_id(project_id)
        if not project_info:
            return False
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(project_info, key):
                setattr(project_info, key, value)
        
        project_info.updated_at = datetime.now().isoformat()
        
        # 保存更新
        project_path = self.get_project_path(project_id)
        if project_path:
            self._save_project_info(project_path, project_info)
            return True
        
        return False
    
    def archive_project(self, project_id: str) -> bool:
        """归档项目"""
        return self.update_project(project_id, status="archived")
    
    def delete_project(self, project_id: str, force: bool = False) -> bool:
        """删除项目（需要force=True确认）"""
        if not force:
            raise ValueError("删除项目需要设置force=True确认")
        
        if project_id not in self.registry:
            return False
        
        project_path = self.get_project_path(project_id)
        if project_path and project_path.exists():
            import shutil
            shutil.rmtree(project_path)
        
        del self.registry[project_id]
        self._save_projects_registry()
        
        logger.info(f"项目已删除: {project_id}")
        return True
    
    def validate_project_context(self, project_id: str, operation: str) -> bool:
        """验证项目上下文，确保操作的项目正确性"""
        project_info = self.get_project_by_id(project_id)
        if not project_info:
            logger.warning(f"项目验证失败 - 项目不存在: {project_id}")
            return False
        
        if project_info.status != "active":
            logger.warning(f"项目验证失败 - 项目状态非活跃: {project_id}")
            return False
        
        logger.info(f"项目验证成功: {project_id} - {operation}")
        return True
    
    def get_current_project(self) -> Optional[str]:
        """获取当前选中的项目ID"""
        return self.current_project_id
    
    def set_current_project(self, project_id: str) -> bool:
        """设置当前项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 设置是否成功
        """
        if project_id and project_id in self.registry:
            self.current_project_id = project_id
            logger.info(f"当前项目已切换到: {project_id}")
            return True
        else:
            logger.warning(f"无法设置当前项目，项目不存在: {project_id}")
            return False
    
    def get_current_project_info(self) -> Optional[ProjectInfo]:
        """获取当前项目信息"""
        if self.current_project_id:
            return self.get_project_by_id(self.current_project_id)
        return None

# 全局项目管理器实例
_project_manager = None

def get_project_manager() -> ProjectManager:
    """获取全局项目管理器实例"""
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager