#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC项目命令处理器
专门处理生产管理控制相关的命令，不包含CAD设计功能

作者: 3AI电器实业有限公司
版本: 1.0.0
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.project_manager import ProjectManager
from ..utils.logger import get_logger


class ProjectCommandProcessor:
    """PMC项目命令处理器
    
    专门处理生产管理控制相关的命令：
    - 项目管理
    - 生产计划
    - 进度跟踪
    - 质量控制
    - 资源调度
    """
    
    def __init__(self):
        """初始化命令处理器"""
        self.logger = get_logger(__name__)
        self.project_manager = ProjectManager()
        
        # 命令模式定义
        self.command_patterns = {
            # 项目管理命令
            'create_project': [
                r'创建新?项目[：:]?(.+)',
                r'新建项目[：:]?(.+)',
                r'create project[：:]?(.+)',
            ],
            'switch_project': [
                r'切换到?项目[：:]?(.+)',
                r'选择项目[：:]?(.+)',
                r'switch to project[：:]?(.+)',
            ],
            'list_projects': [
                r'列出所有项目',
                r'显示项目列表',
                r'list projects',
                r'show projects',
            ],
            'project_status': [
                r'查看?当前?项目状态',
                r'项目状态',
                r'project status',
                r'current project',
            ],
            'update_project': [
                r'更新项目信息[：:]?(.+)，状态为(.+)',
                r'修改项目[：:]?(.+)，状态[：:]?(.+)',
            ],
            
            # 生产管理命令
            'production_plan': [
                r'制定生产计划',
                r'创建生产计划',
                r'生产计划',
                r'production plan',
            ],
            'production_progress': [
                r'查看生产进度',
                r'生产进度',
                r'进度跟踪',
                r'production progress',
            ],
            'quality_control': [
                r'质量控制',
                r'质量检查',
                r'添加质量检查记录',
                r'quality control',
            ],
            'device_status': [
                r'查看设备状态',
                r'设备状态',
                r'device status',
            ],
            'production_report': [
                r'生成生产报告',
                r'生产报告',
                r'production report',
            ],
        }
        
        self.logger.info("PMC项目命令处理器初始化完成")
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            Dict: 处理结果
        """
        try:
            user_input = user_input.strip()
            
            if not user_input:
                return {
                    'success': False,
                    'message': '请输入有效的命令',
                    'input_type': 'invalid'
                }
            
            # 识别命令类型
            command_type, matches = self._identify_command(user_input)
            
            if command_type:
                return self._execute_command(command_type, matches, user_input)
            else:
                return {
                    'success': False,
                    'message': f'无法识别的命令: {user_input}。请输入 help 查看可用命令。',
                    'input_type': 'unknown'
                }
                
        except Exception as e:
            self.logger.error(f"处理用户输入时出错: {e}")
            return {
                'success': False,
                'message': f'处理命令时出错: {str(e)}',
                'input_type': 'error'
            }
    
    def _identify_command(self, user_input: str) -> tuple[Optional[str], Optional[List[str]]]:
        """识别命令类型
        
        Args:
            user_input: 用户输入
            
        Returns:
            tuple: (命令类型, 匹配的参数)
        """
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    return command_type, match.groups()
        
        return None, None
    
    def _execute_command(self, command_type: str, matches: List[str], original_input: str) -> Dict[str, Any]:
        """执行命令
        
        Args:
            command_type: 命令类型
            matches: 正则匹配的参数
            original_input: 原始输入
            
        Returns:
            Dict: 执行结果
        """
        try:
            if command_type == 'create_project':
                return self._handle_create_project(matches[0] if matches else '')
            elif command_type == 'switch_project':
                return self._handle_switch_project(matches[0] if matches else '')
            elif command_type == 'list_projects':
                return self._handle_list_projects()
            elif command_type == 'project_status':
                return self._handle_project_status()
            elif command_type == 'update_project':
                return self._handle_update_project(matches[0] if matches else '', matches[1] if len(matches) > 1 else '')
            elif command_type == 'production_plan':
                return self._handle_production_plan()
            elif command_type == 'production_progress':
                return self._handle_production_progress()
            elif command_type == 'quality_control':
                return self._handle_quality_control()
            elif command_type == 'device_status':
                return self._handle_device_status()
            elif command_type == 'production_report':
                return self._handle_production_report()
            else:
                return {
                    'success': False,
                    'message': f'未实现的命令类型: {command_type}',
                    'input_type': 'unimplemented'
                }
                
        except Exception as e:
            self.logger.error(f"执行命令 {command_type} 时出错: {e}")
            return {
                'success': False,
                'message': f'执行命令时出错: {str(e)}',
                'input_type': 'error'
            }
    
    def _handle_create_project(self, project_name: str) -> Dict[str, Any]:
        """处理创建项目命令"""
        if not project_name:
            return {
                'success': False,
                'message': '请指定项目名称',
                'input_type': 'project_management'
            }
        
        try:
            result = self.project_manager.create_project(
                name=project_name.strip(),
                description=f"PMC生产管理项目: {project_name.strip()}"
            )
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'成功创建项目: {project_name}',
                    'input_type': 'project_management',
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'message': result['message'],
                    'input_type': 'project_management'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'创建项目失败: {str(e)}',
                'input_type': 'project_management'
            }
    
    def _handle_switch_project(self, project_name: str) -> Dict[str, Any]:
        """处理切换项目命令"""
        if not project_name:
            return {
                'success': False,
                'message': '请指定要切换的项目名称',
                'input_type': 'project_management'
            }
        
        try:
            result = self.project_manager.switch_project(project_name.strip())
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'已切换到项目: {project_name}',
                    'input_type': 'project_management',
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'message': result['message'],
                    'input_type': 'project_management'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'切换项目失败: {str(e)}',
                'input_type': 'project_management'
            }
    
    def _handle_list_projects(self) -> Dict[str, Any]:
        """处理列出项目命令"""
        try:
            projects = self.project_manager.list_projects()
            
            if not projects:
                return {
                    'success': True,
                    'message': '当前没有任何项目',
                    'input_type': 'project_management'
                }
            
            project_list = []
            for project in projects:
                status = project.get('status', '未知')
                project_list.append(f"  - {project['name']} (ID: {project['id']}, 状态: {status})")
            
            message = f"共有 {len(projects)} 个项目:\n" + "\n".join(project_list)
            
            return {
                'success': True,
                'message': message,
                'input_type': 'project_management',
                'data': projects
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取项目列表失败: {str(e)}',
                'input_type': 'project_management'
            }
    
    def _handle_project_status(self) -> Dict[str, Any]:
        """处理查看项目状态命令"""
        try:
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                return {
                    'success': True,
                    'message': '当前没有选择任何项目',
                    'input_type': 'project_management'
                }
            
            status_info = [
                f"项目名称: {current_project['name']}",
                f"项目ID: {current_project['id']}",
                f"状态: {current_project.get('status', '未知')}",
                f"描述: {current_project.get('description', '无描述')}",
                f"创建时间: {current_project.get('created_at', '未知')}"
            ]
            
            message = "\n".join(status_info)
            
            return {
                'success': True,
                'message': message,
                'input_type': 'project_management',
                'data': current_project
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取项目状态失败: {str(e)}',
                'input_type': 'project_management'
            }
    
    def _handle_update_project(self, project_name: str, status: str) -> Dict[str, Any]:
        """处理更新项目命令"""
        if not project_name or not status:
            return {
                'success': False,
                'message': '请指定项目名称和状态',
                'input_type': 'project_management'
            }
        
        try:
            # 这里可以添加更新项目状态的逻辑
            return {
                'success': True,
                'message': f'项目 {project_name} 的状态已更新为: {status}',
                'input_type': 'project_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'更新项目失败: {str(e)}',
                'input_type': 'project_management'
            }
    
    def _handle_production_plan(self) -> Dict[str, Any]:
        """处理生产计划命令"""
        try:
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                return {
                    'success': False,
                    'message': '请先选择一个项目',
                    'input_type': 'production_management'
                }
            
            # 模拟生产计划制定
            plan_info = [
                f"为项目 '{current_project['name']}' 制定生产计划:",
                "1. 原材料采购计划 - 预计3天",
                "2. 生产准备阶段 - 预计2天",
                "3. 批量生产阶段 - 预计10天",
                "4. 质量检测阶段 - 预计2天",
                "5. 包装出货阶段 - 预计1天",
                "总计预计工期: 18天"
            ]
            
            return {
                'success': True,
                'message': "\n".join(plan_info),
                'input_type': 'production_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'制定生产计划失败: {str(e)}',
                'input_type': 'production_management'
            }
    
    def _handle_production_progress(self) -> Dict[str, Any]:
        """处理生产进度命令"""
        try:
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                return {
                    'success': False,
                    'message': '请先选择一个项目',
                    'input_type': 'production_management'
                }
            
            # 模拟生产进度查看
            progress_info = [
                f"项目 '{current_project['name']}' 生产进度:",
                "✅ 原材料采购 - 已完成 (100%)",
                "✅ 生产准备 - 已完成 (100%)",
                "🔄 批量生产 - 进行中 (60%)",
                "⏳ 质量检测 - 待开始 (0%)",
                "⏳ 包装出货 - 待开始 (0%)",
                "总体进度: 52%"
            ]
            
            return {
                'success': True,
                'message': "\n".join(progress_info),
                'input_type': 'production_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'查看生产进度失败: {str(e)}',
                'input_type': 'production_management'
            }
    
    def _handle_quality_control(self) -> Dict[str, Any]:
        """处理质量控制命令"""
        try:
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                return {
                    'success': False,
                    'message': '请先选择一个项目',
                    'input_type': 'quality_management'
                }
            
            # 模拟质量控制记录
            quality_info = [
                f"项目 '{current_project['name']}' 质量控制记录:",
                f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "检查项目:",
                "  ✅ 外观质量检查 - 合格",
                "  ✅ 尺寸精度检查 - 合格",
                "  ✅ 功能性测试 - 合格",
                "  ⚠️  包装完整性 - 需要改进",
                "总体评价: 良好，需要改进包装工艺"
            ]
            
            return {
                'success': True,
                'message': "\n".join(quality_info),
                'input_type': 'quality_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'质量控制检查失败: {str(e)}',
                'input_type': 'quality_management'
            }
    
    def _handle_device_status(self) -> Dict[str, Any]:
        """处理设备状态命令"""
        try:
            # 模拟设备状态查看
            device_info = [
                "生产设备状态报告:",
                "🟢 注塑机A - 运行正常 (效率: 95%)",
                "🟢 注塑机B - 运行正常 (效率: 92%)",
                "🟡 包装机 - 运行缓慢 (效率: 78%)",
                "🔴 质检设备 - 维护中 (效率: 0%)",
                "🟢 输送带系统 - 运行正常 (效率: 98%)",
                "总体设备效率: 85%"
            ]
            
            return {
                'success': True,
                'message': "\n".join(device_info),
                'input_type': 'device_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'查看设备状态失败: {str(e)}',
                'input_type': 'device_management'
            }
    
    def _handle_production_report(self) -> Dict[str, Any]:
        """处理生产报告命令"""
        try:
            current_project = self.project_manager.get_current_project()
            
            if not current_project:
                return {
                    'success': False,
                    'message': '请先选择一个项目',
                    'input_type': 'report_management'
                }
            
            # 模拟生产报告生成
            report_info = [
                f"项目 '{current_project['name']}' 生产报告:",
                f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "📊 生产统计:",
                "  - 计划产量: 1000件",
                "  - 实际产量: 620件",
                "  - 完成率: 62%",
                "  - 合格率: 98.5%",
                "",
                "⏱️ 时间统计:",
                "  - 计划工期: 18天",
                "  - 已用工期: 11天",
                "  - 预计剩余: 7天",
                "",
                "💰 成本统计:",
                "  - 预算成本: ¥50,000",
                "  - 实际成本: ¥31,200",
                "  - 成本控制: 良好"
            ]
            
            return {
                'success': True,
                'message': "\n".join(report_info),
                'input_type': 'report_management'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'生成生产报告失败: {str(e)}',
                'input_type': 'report_management'
            }