#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理API接口
为AI系统提供统一的项目操作接口，确保项目数据的一致性和安全性
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from .project_manager import get_project_manager, ProjectInfo
from ..ai.project_identifier import get_project_identifier, ProjectContext
from ..utils.logger import get_logger
from ..utils.validation import validate_project_name, validate_project_type

logger = get_logger(__name__)

class ProjectAPI:
    """项目管理API - 为AI系统提供安全的项目操作接口"""
    
    def __init__(self):
        self.project_manager = get_project_manager()
        self.project_identifier = get_project_identifier()
    
    def create_project_from_text(self, user_input: str, 
                               default_owner: str = "") -> Dict[str, Any]:
        """从用户输入文本创建项目
        
        Args:
            user_input: 用户输入文本
            default_owner: 默认项目负责人
            
        Returns:
            Dict: 创建结果
        """
        try:
            # 解析用户输入
            project_info = self._parse_project_creation_request(user_input)
            if not project_info:
                return {
                    "success": False,
                    "error": "无法从输入中解析项目信息",
                    "suggestions": "请提供项目名称和类型，例如：'创建小家电产品开发项目：智能咖啡机'"
                }
            
            # 验证项目信息
            validation_result = self._validate_project_creation(project_info)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "suggestions": validation_result.get("suggestions", "")
                }
            
            # 创建项目
            project_id = self.project_manager.create_project(
                project_name=project_info["name"],
                project_type=project_info["type"],
                description=project_info.get("description", ""),
                owner=project_info.get("owner", default_owner),
                tags=project_info.get("tags", [])
            )
            
            # 设置为当前项目
            self.project_identifier.set_current_project(project_id)
            
            return {
                "success": True,
                "project_id": project_id,
                "project_name": project_info["name"],
                "message": f"项目创建成功: {project_info['name']} (ID: {project_id})"
            }
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            return {
                "success": False,
                "error": f"创建项目时发生错误: {str(e)}"
            }
    
    def identify_project_from_text(self, user_input: str, 
                                 context_project_id: str = None) -> Dict[str, Any]:
        """从用户输入识别项目
        
        Args:
            user_input: 用户输入文本
            context_project_id: 上下文项目ID
            
        Returns:
            Dict: 识别结果
        """
        try:
            project_context = self.project_identifier.identify_project_from_text(
                user_input, context_project_id
            )
            
            if project_context:
                # 添加到上下文历史
                self.project_identifier.add_context_history(project_context)
                
                return {
                    "success": True,
                    "project_id": project_context.project_id,
                    "project_name": project_context.project_name,
                    "confidence": project_context.confidence,
                    "source": project_context.context_source,
                    "matched_keywords": project_context.matched_keywords
                }
            else:
                # 获取建议
                suggestions = self.project_identifier.get_project_suggestions(user_input)
                return {
                    "success": False,
                    "error": "未能识别项目",
                    "suggestions": suggestions,
                    "disambiguation_prompt": self.project_identifier.get_disambiguation_prompt(suggestions)
                }
                
        except Exception as e:
            logger.error(f"项目识别失败: {e}")
            return {
                "success": False,
                "error": f"项目识别时发生错误: {str(e)}"
            }
    
    def get_project_info(self, project_identifier: str) -> Dict[str, Any]:
        """获取项目信息
        
        Args:
            project_identifier: 项目ID或项目名称
            
        Returns:
            Dict: 项目信息
        """
        try:
            # 尝试按ID获取
            project_info = self.project_manager.get_project_by_id(project_identifier)
            
            # 如果按ID没找到，尝试按名称获取
            if not project_info:
                project_info = self.project_manager.get_project_by_name(project_identifier)
            
            if project_info:
                return {
                    "success": True,
                    "project": {
                        "id": project_info.project_id,
                        "name": project_info.project_name,
                        "type": project_info.project_type,
                        "description": project_info.description,
                        "status": project_info.status,
                        "owner": project_info.owner,
                        "created_at": project_info.created_at,
                        "updated_at": project_info.updated_at,
                        "tags": project_info.tags
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"未找到项目: {project_identifier}"
                }
                
        except Exception as e:
            logger.error(f"获取项目信息失败: {e}")
            return {
                "success": False,
                "error": f"获取项目信息时发生错误: {str(e)}"
            }
    
    def list_projects(self, status: str = None, project_type: str = None) -> Dict[str, Any]:
        """列出项目
        
        Args:
            status: 项目状态过滤
            project_type: 项目类型过滤
            
        Returns:
            Dict: 项目列表
        """
        try:
            projects = self.project_manager.list_projects(status=status)
            
            # 按类型过滤
            if project_type:
                projects = [p for p in projects if p.project_type == project_type]
            
            project_list = []
            for project in projects:
                project_list.append({
                    "id": project.project_id,
                    "name": project.project_name,
                    "type": project.project_type,
                    "status": project.status,
                    "owner": project.owner,
                    "created_at": project.created_at,
                    "description": project.description[:100] + "..." if len(project.description) > 100 else project.description
                })
            
            return {
                "success": True,
                "projects": project_list,
                "count": len(project_list)
            }
            
        except Exception as e:
            logger.error(f"列出项目失败: {e}")
            return {
                "success": False,
                "error": f"列出项目时发生错误: {str(e)}"
            }
    
    def update_project_from_text(self, project_id: str, user_input: str) -> Dict[str, Any]:
        """从用户输入更新项目信息
        
        Args:
            project_id: 项目ID
            user_input: 用户输入文本
            
        Returns:
            Dict: 更新结果
        """
        try:
            # 验证项目操作
            is_valid, error_msg = self.project_identifier.validate_project_operation(
                project_id, "update", user_input
            )
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # 解析更新信息
            update_info = self._parse_project_update_request(user_input)
            if not update_info:
                return {
                    "success": False,
                    "error": "无法从输入中解析更新信息"
                }
            
            # 执行更新
            success = self.project_manager.update_project(project_id, **update_info)
            if success:
                return {
                    "success": True,
                    "message": f"项目更新成功: {project_id}",
                    "updated_fields": list(update_info.keys())
                }
            else:
                return {
                    "success": False,
                    "error": "项目更新失败"
                }
                
        except Exception as e:
            logger.error(f"更新项目失败: {e}")
            return {
                "success": False,
                "error": f"更新项目时发生错误: {str(e)}"
            }
    
    def get_project_path(self, project_id: str) -> Dict[str, Any]:
        """获取项目路径
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 路径信息
        """
        try:
            project_path = self.project_manager.get_project_path(project_id)
            if project_path:
                return {
                    "success": True,
                    "project_path": str(project_path),
                    "exists": project_path.exists()
                }
            else:
                return {
                    "success": False,
                    "error": f"未找到项目路径: {project_id}"
                }
                
        except Exception as e:
            logger.error(f"获取项目路径失败: {e}")
            return {
                "success": False,
                "error": f"获取项目路径时发生错误: {str(e)}"
            }
    
    def _parse_project_creation_request(self, user_input: str) -> Optional[Dict[str, Any]]:
        """解析项目创建请求"""
        # 简单的关键词匹配解析
        # 在实际应用中，这里可以使用更复杂的NLP技术
        
        project_types = {
            "小家电": "小家电产品开发",
            "产品开发": "小家电产品开发",
            "生产线": "生产线优化",
            "优化": "生产线优化",
            "供应链": "供应链改进",
            "质量": "质量管理",
            "成本": "成本控制"
        }
        
        # 提取项目类型
        project_type = None
        for keyword, ptype in project_types.items():
            if keyword in user_input:
                project_type = ptype
                break
        
        if not project_type:
            project_type = "其他"
        
        # 提取项目名称（简单实现）
        # 查找冒号后的内容作为项目名称
        if "：" in user_input:
            parts = user_input.split("：")
            if len(parts) > 1:
                project_name = parts[1].strip()
            else:
                return None
        elif ":" in user_input:
            parts = user_input.split(":")
            if len(parts) > 1:
                project_name = parts[1].strip()
            else:
                return None
        else:
            # 尝试从文本中提取项目名称
            import re
            # 查找引号中的内容
            quoted_match = re.search(r'[""'']([^""'']+)[""'']', user_input)
            if quoted_match:
                project_name = quoted_match.group(1)
            else:
                return None
        
        if not project_name:
            return None
        
        return {
            "name": project_name,
            "type": project_type,
            "description": f"通过AI助手创建的{project_type}项目"
        }
    
    def _parse_project_update_request(self, user_input: str) -> Optional[Dict[str, Any]]:
        """解析项目更新请求"""
        update_info = {}
        
        # 简单的更新解析
        if "描述" in user_input or "说明" in user_input:
            # 提取描述信息
            import re
            desc_match = re.search(r'(?:描述|说明)[：:]\s*(.+)', user_input)
            if desc_match:
                update_info["description"] = desc_match.group(1).strip()
        
        if "负责人" in user_input or "owner" in user_input.lower():
            # 提取负责人信息
            import re
            owner_match = re.search(r'(?:负责人|owner)[：:]\s*(.+)', user_input)
            if owner_match:
                update_info["owner"] = owner_match.group(1).strip()
        
        return update_info if update_info else None
    
    def _validate_project_creation(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证项目创建信息"""
        # 验证项目名称
        if not validate_project_name(project_info["name"]):
            return {
                "valid": False,
                "error": "项目名称不符合规范",
                "suggestions": "项目名称应为2-50个字符，只能包含中文、英文、数字、下划线、短横线"
            }
        
        # 验证项目类型
        if not validate_project_type(project_info["type"]):
            return {
                "valid": False,
                "error": "项目类型不支持",
                "suggestions": "支持的项目类型：小家电产品开发、生产线优化、供应链改进、质量管理、成本控制、技术改进、其他"
            }
        
        # 检查项目名称是否已存在
        existing_project = self.project_manager.get_project_by_name(project_info["name"])
        if existing_project:
            return {
                "valid": False,
                "error": "项目名称已存在",
                "suggestions": "请使用不同的项目名称"
            }
        
        return {"valid": True}

# 全局项目API实例
_project_api = None

def get_project_api() -> ProjectAPI:
    """获取全局项目API实例"""
    global _project_api
    if _project_api is None:
        _project_api = ProjectAPI()
    return _project_api