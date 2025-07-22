#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI项目识别器
基于自然语言处理和上下文分析，准确识别用户输入中的项目信息
防止项目数据混淆和张冠李戴问题
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

from ..core.project_manager import get_project_manager, ProjectInfo
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProjectContext:
    """项目上下文信息"""
    project_id: str
    project_name: str
    confidence: float  # 识别置信度 0-1
    matched_keywords: List[str]
    context_source: str  # 识别来源：name, id, keyword, context

class ProjectIdentifier:
    """AI项目识别器"""
    
    def __init__(self):
        self.project_manager = get_project_manager()
        self.keyword_patterns = self._load_keyword_patterns()
        self.context_history = []  # 上下文历史
        self.current_project = None  # 当前活跃项目
    
    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """加载项目关键词模式"""
        return {
            "小家电产品开发": [
                "小家电", "产品开发", "新品", "设计", "研发", 
                "电器", "家电", "产品", "开发", "设计方案"
            ],
            "生产线优化": [
                "生产线", "优化", "改进", "效率", "产能", 
                "流水线", "生产", "制造", "工艺", "自动化"
            ],
            "供应链改进": [
                "供应链", "供应商", "采购", "物流", "库存", 
                "供货", "配送", "仓储", "材料", "零部件"
            ],
            "质量管理": [
                "质量", "品质", "检测", "检验", "标准", 
                "合格率", "缺陷", "改善", "控制", "管理"
            ],
            "成本控制": [
                "成本", "费用", "预算", "控制", "节约", 
                "降本", "支出", "开支", "财务", "经济"
            ]
        }
    
    def identify_project_from_text(self, text: str, 
                                  context_project_id: str = None) -> Optional[ProjectContext]:
        """从文本中识别项目信息
        
        Args:
            text: 输入文本
            context_project_id: 上下文项目ID（如果有的话）
            
        Returns:
            ProjectContext: 识别到的项目上下文，如果没有识别到返回None
        """
        if not text:
            return None
        
        # 1. 直接项目ID匹配（最高优先级）
        project_context = self._match_by_project_id(text)
        if project_context and project_context.confidence > 0.9:
            return project_context
        
        # 2. 项目名称匹配（高优先级）
        project_context = self._match_by_project_name(text)
        if project_context and project_context.confidence > 0.8:
            return project_context
        
        # 3. 关键词匹配（中等优先级）
        project_context = self._match_by_keywords(text)
        if project_context and project_context.confidence > 0.6:
            return project_context
        
        # 4. 上下文推断（低优先级）
        if context_project_id:
            project_context = self._match_by_context(text, context_project_id)
            if project_context:
                return project_context
        
        # 5. 历史上下文推断（最低优先级）
        project_context = self._match_by_history(text)
        if project_context:
            return project_context
        
        return None
    
    def _match_by_project_id(self, text: str) -> Optional[ProjectContext]:
        """通过项目ID匹配"""
        # 查找8位字母数字组合
        pattern = r'\b[a-zA-Z0-9]{8}\b'
        matches = re.findall(pattern, text)
        
        for match in matches:
            project_info = self.project_manager.get_project_by_id(match)
            if project_info:
                return ProjectContext(
                    project_id=project_info.project_id,
                    project_name=project_info.project_name,
                    confidence=0.95,
                    matched_keywords=[match],
                    context_source="id"
                )
        
        return None
    
    def _match_by_project_name(self, text: str) -> Optional[ProjectContext]:
        """通过项目名称匹配"""
        projects = self.project_manager.list_projects(status="active")
        
        best_match = None
        best_confidence = 0
        
        for project in projects:
            # 完全匹配
            if project.project_name in text:
                confidence = 0.9
                if confidence > best_confidence:
                    best_match = ProjectContext(
                        project_id=project.project_id,
                        project_name=project.project_name,
                        confidence=confidence,
                        matched_keywords=[project.project_name],
                        context_source="name"
                    )
                    best_confidence = confidence
            
            # 部分匹配
            name_words = project.project_name.split()
            matched_words = [word for word in name_words if word in text]
            if matched_words:
                confidence = len(matched_words) / len(name_words) * 0.8
                if confidence > best_confidence and confidence > 0.5:
                    best_match = ProjectContext(
                        project_id=project.project_id,
                        project_name=project.project_name,
                        confidence=confidence,
                        matched_keywords=matched_words,
                        context_source="name"
                    )
                    best_confidence = confidence
        
        return best_match
    
    def _match_by_keywords(self, text: str) -> Optional[ProjectContext]:
        """通过关键词匹配"""
        projects = self.project_manager.list_projects(status="active")
        
        best_match = None
        best_confidence = 0
        
        for project in projects:
            project_type = project.project_type
            if project_type in self.keyword_patterns:
                keywords = self.keyword_patterns[project_type]
                matched_keywords = [kw for kw in keywords if kw in text]
                
                if matched_keywords:
                    confidence = len(matched_keywords) / len(keywords) * 0.7
                    if confidence > best_confidence and confidence > 0.3:
                        best_match = ProjectContext(
                            project_id=project.project_id,
                            project_name=project.project_name,
                            confidence=confidence,
                            matched_keywords=matched_keywords,
                            context_source="keyword"
                        )
                        best_confidence = confidence
        
        return best_match
    
    def _match_by_context(self, text: str, context_project_id: str) -> Optional[ProjectContext]:
        """通过上下文匹配"""
        project_info = self.project_manager.get_project_by_id(context_project_id)
        if not project_info:
            return None
        
        # 如果文本中没有明确的其他项目指示，使用上下文项目
        other_projects = self.project_manager.list_projects(status="active")
        for other_project in other_projects:
            if other_project.project_id != context_project_id:
                if other_project.project_name in text:
                    return None  # 文本中提到了其他项目
        
        return ProjectContext(
            project_id=project_info.project_id,
            project_name=project_info.project_name,
            confidence=0.5,
            matched_keywords=[],
            context_source="context"
        )
    
    def _match_by_history(self, text: str) -> Optional[ProjectContext]:
        """通过历史上下文匹配"""
        if not self.context_history:
            return None
        
        # 使用最近的项目上下文
        recent_context = self.context_history[-1]
        return self._match_by_context(text, recent_context.project_id)
    
    def set_current_project(self, project_id: str):
        """设置当前活跃项目"""
        project_info = self.project_manager.get_project_by_id(project_id)
        if project_info:
            self.current_project = project_id
            logger.info(f"设置当前项目: {project_info.project_name} ({project_id})")
    
    def add_context_history(self, project_context: ProjectContext):
        """添加上下文历史"""
        self.context_history.append(project_context)
        # 保持历史记录在合理范围内
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
    
    def get_project_suggestions(self, text: str, limit: int = 3) -> List[ProjectContext]:
        """获取项目建议列表"""
        suggestions = []
        
        # 收集所有可能的匹配
        matches = []
        
        # ID匹配
        id_match = self._match_by_project_id(text)
        if id_match:
            matches.append(id_match)
        
        # 名称匹配
        name_match = self._match_by_project_name(text)
        if name_match:
            matches.append(name_match)
        
        # 关键词匹配
        keyword_match = self._match_by_keywords(text)
        if keyword_match:
            matches.append(keyword_match)
        
        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # 去重并限制数量
        seen_projects = set()
        for match in matches:
            if match.project_id not in seen_projects:
                suggestions.append(match)
                seen_projects.add(match.project_id)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def validate_project_operation(self, project_id: str, operation: str, 
                                 user_input: str) -> Tuple[bool, str]:
        """验证项目操作的合法性
        
        Args:
            project_id: 项目ID
            operation: 操作类型
            user_input: 用户输入
            
        Returns:
            Tuple[bool, str]: (是否合法, 错误信息)
        """
        # 验证项目存在性
        if not self.project_manager.validate_project_context(project_id, operation):
            return False, f"项目验证失败: {project_id}"
        
        # 验证操作与项目的一致性
        identified_context = self.identify_project_from_text(user_input)
        if identified_context and identified_context.project_id != project_id:
            if identified_context.confidence > 0.8:
                return False, f"操作项目不一致: 期望 {project_id}, 识别到 {identified_context.project_id}"
        
        return True, ""
    
    def get_disambiguation_prompt(self, suggestions: List[ProjectContext]) -> str:
        """生成项目消歧提示"""
        if not suggestions:
            return "未找到匹配的项目，请明确指定项目名称或ID。"
        
        if len(suggestions) == 1:
            return f"识别到项目: {suggestions[0].project_name} ({suggestions[0].project_id})"
        
        prompt = "检测到多个可能的项目，请确认:\n"
        for i, suggestion in enumerate(suggestions, 1):
            prompt += f"{i}. {suggestion.project_name} ({suggestion.project_id}) - 置信度: {suggestion.confidence:.2f}\n"
        
        return prompt

# 全局项目识别器实例
_project_identifier = None

def get_project_identifier() -> ProjectIdentifier:
    """获取全局项目识别器实例"""
    global _project_identifier
    if _project_identifier is None:
        _project_identifier = ProjectIdentifier()
    return _project_identifier