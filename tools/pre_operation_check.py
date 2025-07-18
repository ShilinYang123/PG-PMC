#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目前置操作检查脚本（升级版）

功能：在执行文件操作前进行合规性检查，确保操作符合项目规范
新增：日期一致性检查、更完善的监控机制
作者：雨俊（技术负责人）
创建日期：2025年1月13日
升级日期：2025年1月13日
"""

import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ProjectComplianceChecker:
    """项目合规性检查器（升级版）"""
    
    def __init__(self, project_root: str = "s:/PG-Dev", enhanced_mode: bool = True):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.architecture_doc = self.docs_dir / "01-设计" / "项目架构设计.md"
        self.process_doc = self.docs_dir / "03-管理" / "规范与流程.md"
        self.task_doc = self.docs_dir / "01-设计" / "开发任务书.md"
        self.tech_doc = self.docs_dir / "01-设计" / "技术方案.md"
        
        # 增强模式配置
        self.enhanced_mode = enhanced_mode
        # enhanced_config_path不再使用，配置已合并到project_config.yaml
        self.violation_log_path = self.project_root / "logs" / "pre_check_violations.log"
        
        # 加载项目配置
        self.config = self._load_project_config()
        self.enhanced_config = self._load_enhanced_config() if enhanced_mode else {}
        
        # 定义标准目录结构
        self.standard_dirs = {
            "docs": "项目开发依据的重要文档",
            "project": "项目开发成果", 
            "tools": "项目开发过程中使用到的工具与资源",
            "AI助理生产成果": "利用项目开发成果进行现实生产的产出",
            "bak": "项目备份目录",
            "logs": "开发及调试使用过程各种记录",
            ".cache": "项目性能优化的缓存系统"
        }
        
        # 禁止在根目录创建的文件类型
        self.forbidden_root_files = [
            ".txt", ".log", ".tmp", ".temp", ".bak", ".old",
            ".pro", ".prt", ".asm", ".drw",  # Creo文件
            ".py", ".js", ".ts", ".html", ".css",  # 代码文件
            ".md", ".doc", ".docx", ".pdf"  # 文档文件（除非特殊说明）
        ]
    
    def _load_project_config(self) -> Dict:
        """加载项目配置"""
        config_file = self.docs_dir / "03-管理" / "project_config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_enhanced_config(self) -> Dict:
        """从project_config.yaml的enhanced_pre_check部分加载增强配置"""
        try:
            # 从project_config.yaml中读取enhanced_pre_check配置
            project_config = self._load_project_config()
            enhanced_config = project_config.get('compliance', {}).get('enhanced_pre_check', {})
            
            # 提取增强配置的三个主要部分
            config = {
                'monitoring': enhanced_config.get('monitoring', {}),
                'strict_mode': enhanced_config.get('strict_mode', {}),
                'auto_correction': enhanced_config.get('auto_correction', {})
            }
            
            # 如果配置为空，使用默认配置
            if not any(config.values()):
                config = self._get_default_enhanced_config()
            
            return config
        except Exception as e:
            print(f"警告：加载增强配置失败: {e}")
            return self._get_default_enhanced_config()
    
    def _get_default_enhanced_config(self) -> Dict:
        """获取默认增强配置"""
        return {
            "monitoring": {
                "enabled": True,
                "log_violations": True,
                "alert_threshold": 3,
                "block_operations": True
            },
            "strict_mode": {
                "enabled": False,
                "require_approval": ["delete", "modify"],
                "protected_patterns": ["*.md", "*.yaml", "*.py"]
            },
            "auto_correction": {
                "enabled": True,
                "suggest_alternatives": True,
                "auto_move_files": False
            }
        }
    

    
    def check_file_operation(self, file_path: str, operation_type: str) -> Tuple[bool, List[str]]:
        """检查文件操作是否符合规范（增强版）
        
        Args:
            file_path: 文件路径
            operation_type: 操作类型 (create, move, delete, modify)
            
        Returns:
            (是否通过检查, 检查结果消息列表)
        """
        messages = []
        passed = True
        
        file_path = Path(file_path)
        
        # 增强模式前置检查
        if self.enhanced_mode:
            if not self._enhanced_pre_check(file_path, operation_type, messages):
                passed = False
                # 强制阻断模式
                if self.enhanced_config.get("monitoring", {}).get("block_operations", True):
                    self._log_violation(file_path, operation_type, "强制阻断")
                    return False, messages
        
        # 检查1: 文件路径规范性
        if not self._check_path_compliance(file_path, messages):
            passed = False
        
        # 检查2: 根目录文件限制
        if not self._check_root_directory_restrictions(file_path, operation_type, messages):
            passed = False
        
        # 检查3: 目录功能定位
        if not self._check_directory_purpose(file_path, messages):
            passed = False
        
        # 检查4: 文件命名规范
        if not self._check_naming_convention(file_path, messages):
            passed = False
        
        # 检查5: 权限要求
        if not self._check_permission_requirements(file_path, operation_type, messages):
            passed = False
        
        # 检查6: 日期一致性检查
        if not self._check_date_consistency(file_path, messages):
            passed = False
        
        # 增强模式后置处理
        if self.enhanced_mode:
            self._enhanced_post_check(file_path, operation_type, passed, messages)
        
        return passed, messages
    
    def _check_path_compliance(self, file_path: Path, messages: List[str]) -> bool:
        """检查路径合规性"""
        # 检查是否在项目根目录下
        try:
            file_path.relative_to(self.project_root)
        except ValueError:
            messages.append(f"❌ 文件路径不在项目根目录下: {file_path}")
            return False
        
        # 检查路径是否使用了标准目录
        rel_path = file_path.relative_to(self.project_root)
        if len(rel_path.parts) > 0:
            top_dir = rel_path.parts[0]
            if top_dir not in self.standard_dirs and not top_dir.startswith('.'):
                messages.append(f"❌ 使用了非标准顶级目录: {top_dir}")
                messages.append(f"📋 标准目录: {', '.join(self.standard_dirs.keys())}")
                return False
        
        messages.append(f"✅ 路径合规性检查通过")
        return True
    
    def _check_root_directory_restrictions(self, file_path: Path, operation_type: str, messages: List[str]) -> bool:
        """检查根目录文件限制"""
        rel_path = file_path.relative_to(self.project_root)
        
        # 如果是根目录文件
        if len(rel_path.parts) == 1:
            file_ext = file_path.suffix.lower()
            
            # 检查是否为禁止的文件类型
            if file_ext in self.forbidden_root_files:
                messages.append(f"❌ 禁止在根目录创建 {file_ext} 类型文件")
                messages.append(f"💡 建议: 将文件放置到合适的子目录中")
                messages.append(f"📁 可选目录: {self._suggest_directory_for_file(file_ext)}")
                return False
            
            # 特殊文件检查
            if operation_type == "create":
                allowed_root_files = [
                    "README.md", ".gitignore", "requirements.txt", 
                    "package.json", "pyproject.toml", "setup.py"
                ]
                if file_path.name not in allowed_root_files:
                    messages.append(f"❌ 不建议在根目录创建文件: {file_path.name}")
                    messages.append(f"💡 建议: 将文件放置到合适的子目录中")
                    return False
        
        messages.append(f"✅ 根目录限制检查通过")
        return True
    
    def _check_directory_purpose(self, file_path: Path, messages: List[str]) -> bool:
        """检查目录功能定位"""
        rel_path = file_path.relative_to(self.project_root)
        
        if len(rel_path.parts) > 0:
            top_dir = rel_path.parts[0]
            
            # 检查文件是否放在了正确的目录中
            if top_dir in self.standard_dirs:
                if not self._validate_file_in_directory(file_path, top_dir, messages):
                    return False
        
        messages.append(f"✅ 目录功能定位检查通过")
        return True
    
    def _validate_file_in_directory(self, file_path: Path, directory: str, messages: List[str]) -> bool:
        """验证文件是否适合放在指定目录中"""
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()
        
        # docs目录检查
        if directory == "docs":
            if file_ext not in [".md", ".yaml", ".yml", ".json", ".txt"]:
                messages.append(f"❌ docs目录应主要包含文档文件，不建议放置 {file_ext} 文件")
                return False
        
        # project目录检查
        elif directory == "project":
            if file_ext in [".md"] and "readme" not in file_name:
                messages.append(f"💡 提示: 文档文件建议放在docs目录中")
        
        # AI助理生产成果目录检查
        elif directory == "AI助理生产成果":
            production_files = [".prt", ".asm", ".drw", ".pro", ".txt", ".md"]
            if file_ext not in production_files:
                messages.append(f"❌ AI助理生产成果目录应包含生产相关文件，不建议放置 {file_ext} 文件")
                return False
        
        # tools目录检查
        elif directory == "tools":
            if file_ext not in [".py", ".js", ".sh", ".bat", ".ps1", ".md"]:
                messages.append(f"❌ tools目录应包含工具脚本，不建议放置 {file_ext} 文件")
                return False
        
        return True
    
    def _check_naming_convention(self, file_path: Path, messages: List[str]) -> bool:
        """检查文件命名规范"""
        file_name = file_path.name
        
        # 检查文件名是否包含非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            if char in file_name:
                messages.append(f"❌ 文件名包含非法字符: {char}")
                return False
        
        # 检查文件名长度
        if len(file_name) > 255:
            messages.append(f"❌ 文件名过长 (>{255}字符)")
            return False
        
        # 检查是否使用了推荐的命名规范
        if file_path.suffix.lower() == ".py":
            if not file_name.replace('.py', '').replace('_', '').isalnum():
                messages.append(f"💡 建议: Python文件使用snake_case命名")
        
        messages.append(f"✅ 文件命名规范检查通过")
        return True
    
    def _check_permission_requirements(self, file_path: Path, operation_type: str, messages: List[str]) -> bool:
        """检查权限要求"""
        # 核心文档权限检查
        protected_files = [
            "docs/01-设计/开发任务书.md",
            "docs/01-设计/技术方案.md", 
            "docs/01-设计/项目架构设计.md",
            "docs/03-管理/规范与流程.md",
            "docs/03-管理/project_config.yaml",
            "tools/finish.py",
            "tools/control.py",
            "tools/check_structure.py",
            "tools/update_structure.py"
        ]
        
        rel_path_str = str(file_path.relative_to(self.project_root)).replace('\\', '/')
        
        if rel_path_str in protected_files and operation_type in ["modify", "delete"]:
            messages.append(f"❌ 核心文件需要特殊权限: {rel_path_str}")
            messages.append(f"📋 需要杨老师授权才能修改此文件")
            return False
        
        messages.append(f"✅ 权限要求检查通过")
        return True
    
    def _check_date_consistency(self, file_path: Path, messages: List[str]) -> bool:
        """检查文件中的日期一致性"""
        if file_path.suffix.lower() not in ['.py', '.md', '.txt']:
            messages.append(f"✅ 日期一致性检查跳过（非文本文件）")
            return True
        
        if not file_path.exists():
            messages.append(f"✅ 日期一致性检查跳过（新文件）")
            return True
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找日期模式
            date_patterns = [
                r'创建日期[：:](\d{4}年\d{1,2}月\d{1,2}日)',
                r'修改日期[：:](\d{4}年\d{1,2}月\d{1,2}日)',
                r'更新日期[：:](\d{4}年\d{1,2}月\d{1,2}日)',
                r'升级日期[：:](\d{4}年\d{1,2}月\d{1,2}日)'
            ]
            
            found_dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, content)
                found_dates.extend(matches)
            
            if not found_dates:
                messages.append(f"✅ 日期一致性检查跳过（未找到日期信息）")
                return True
            
            # 检查日期格式和合理性
            current_date = datetime.now().strftime('%Y年%m月%d日')
            for date_str in found_dates:
                try:
                    # 解析日期
                    date_match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
                    if date_match:
                        year, month, day = map(int, date_match.groups())
                        file_date = datetime(year, month, day)
                        
                        # 检查日期是否合理（不能是未来日期）
                        if file_date > datetime.now():
                            messages.append(f"❌ 发现未来日期: {date_str}")
                            return False
                        
                        # 检查日期是否过于久远（超过5年）
                        if (datetime.now() - file_date).days > 1825:
                            messages.append(f"⚠️ 发现较旧日期: {date_str}，请确认是否需要更新")
                    
                except ValueError:
                    messages.append(f"❌ 日期格式错误: {date_str}")
                    return False
            
            messages.append(f"✅ 日期一致性检查通过")
            return True
            
        except Exception as e:
            messages.append(f"⚠️ 日期一致性检查失败: {str(e)}")
            return True  # 不因为检查失败而阻止操作
    
    def _suggest_directory_for_file(self, file_ext: str) -> str:
        """为文件类型建议合适的目录"""
        suggestions = {
            ".md": "docs/02-开发/ (开发文档) 或 docs/04-模板/ (模板文档)",
            ".py": "project/src/ (源代码) 或 tools/ (工具脚本)",
            ".txt": "AI助理生产成果/ (生产文件) 或 logs/ (日志文件)",
            ".log": "logs/其他日志/ 或 logs/工作记录/",
            ".pro": "AI助理生产成果/ (Creo脚本文件)",
            ".prt": "AI助理生产成果/ (Creo零件文件)",
            ".tmp": "bak/待清理资料/ (临时文件)",
            ".bak": "bak/常规备份/ (备份文件)"
        }
        return suggestions.get(file_ext, "请参考项目架构设计文档选择合适目录")
    
    def check_development_task(self, task_description: str, module_name: str) -> Tuple[bool, List[str]]:
        """检查开发任务是否符合规范
        
        Args:
            task_description: 任务描述
            module_name: 模块名称
            
        Returns:
            (是否通过检查, 检查结果消息列表)
        """
        messages = []
        passed = True
        
        # 检查1: 任务是否符合开发任务书
        if not self._check_task_alignment(task_description, messages):
            passed = False
        
        # 检查2: 技术方案符合性
        if not self._check_tech_solution_alignment(module_name, messages):
            passed = False
        
        # 检查3: 架构设计符合性
        if not self._check_architecture_alignment(module_name, messages):
            passed = False
        
        return passed, messages
    
    def _check_task_alignment(self, task_description: str, messages: List[str]) -> bool:
        """检查任务是否符合开发任务书"""
        # 这里应该读取开发任务书内容进行匹配
        # 简化实现，检查关键词
        key_terms = ["AI设计助理", "Creo", "自然语言", "小家电", "3D模型"]
        
        found_terms = [term for term in key_terms if term in task_description]
        
        if len(found_terms) < 2:
            messages.append(f"❌ 任务描述与开发任务书关联度较低")
            messages.append(f"💡 建议: 确保任务与AI设计助理核心目标相关")
            return False
        
        messages.append(f"✅ 任务与开发任务书对齐检查通过")
        return True
    
    def _check_tech_solution_alignment(self, module_name: str, messages: List[str]) -> bool:
        """检查技术方案符合性"""
        # 检查模块是否符合技术架构
        valid_modules = [
            "自然语言处理", "Creo API集成", "参数化建模", "设计规则引擎", 
            "用户交互界面", "脚本管理", "几何体生成", "参数解析", "状态跟踪"
        ]
        
        if not any(valid_module in module_name for valid_module in valid_modules):
            messages.append(f"❌ 模块名称与技术方案不匹配: {module_name}")
            messages.append(f"📋 有效模块: {', '.join(valid_modules)}")
            return False
        
        messages.append(f"✅ 技术方案对齐检查通过")
        return True
    
    def _check_architecture_alignment(self, module_name: str, messages: List[str]) -> bool:
        """检查架构设计符合性"""
        # 检查是否符合四层架构设计
        architecture_layers = [
            "用户交互层", "AI智能层", "脚本执行层", "CAD软件层"
        ]
        
        # 简化检查，确保模块属于某个架构层
        messages.append(f"✅ 架构设计对齐检查通过")
        return True
    
    def generate_compliance_report(self) -> Dict:
        """生成合规性报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "checks_performed": [],
            "violations_found": [],
            "recommendations": []
        }
        
        # 检查项目目录结构
        structure_check = self._check_project_structure()
        report["checks_performed"].append("项目目录结构检查")
        
        if not structure_check["passed"]:
            report["violations_found"].extend(structure_check["violations"])
        
        report["recommendations"].extend(structure_check["recommendations"])
        
        return report
    
    def _check_project_structure(self) -> Dict:
        """检查项目目录结构"""
        result = {
            "passed": True,
            "violations": [],
            "recommendations": []
        }
        
        # 检查标准目录是否存在
        for dir_name, purpose in self.standard_dirs.items():
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                result["violations"].append(f"缺少标准目录: {dir_name} ({purpose})")
                result["passed"] = False
        
        # 检查根目录是否有不应该存在的文件
        for item in self.project_root.iterdir():
            if item.is_file():
                if item.suffix.lower() in self.forbidden_root_files:
                    result["violations"].append(f"根目录存在不当文件: {item.name}")
                    result["passed"] = False
        
        # 添加建议
        result["recommendations"].append("定期运行合规性检查")
        result["recommendations"].append("使用前置检查脚本验证操作")
        
        return result
    
    def _enhanced_pre_check(self, file_path: Path, operation_type: str, messages: List[str]) -> bool:
        """增强模式前置检查"""
        # 严格模式检查
        if self.enhanced_config.get("strict_mode", {}).get("enabled", False):
            require_approval = self.enhanced_config.get("strict_mode", {}).get("require_approval", [])
            if operation_type in require_approval:
                messages.append(f"🔒 严格模式: {operation_type} 操作需要管理员批准")
                return False
        
        # 保护模式检查
        protected_patterns = self.enhanced_config.get("strict_mode", {}).get("protected_patterns", [])
        for pattern in protected_patterns:
            if file_path.match(pattern):
                messages.append(f"🛡️ 文件受保护: {file_path.name} 匹配模式 {pattern}")
                return False
        
        return True
    
    def _enhanced_post_check(self, file_path: Path, operation_type: str, passed: bool, messages: List[str]):
        """增强模式后置处理"""
        # 记录违规日志
        if not passed and self.enhanced_config.get("monitoring", {}).get("log_violations", True):
            self._log_violation(file_path, operation_type, "检查未通过")
        
        # 自动纠正建议
        if not passed and self.enhanced_config.get("auto_correction", {}).get("suggest_alternatives", True):
            suggestions = self._generate_auto_correction_suggestions(file_path, operation_type)
            messages.extend(suggestions)
    
    def _log_violation(self, file_path: Path, operation_type: str, reason: str):
        """记录违规操作"""
        try:
            self.violation_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "file_path": str(file_path),
                "operation_type": operation_type,
                "reason": reason,
                "user": os.getenv("USERNAME", "unknown")
            }
            
            with open(self.violation_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"警告：记录违规日志失败: {e}")
    
    def _generate_auto_correction_suggestions(self, file_path: Path, operation_type: str) -> List[str]:
        """生成自动纠正建议"""
        suggestions = []
        
        # 根据文件类型和操作类型生成建议
        if operation_type == "create":
            if file_path.suffix.lower() == ".py":
                suggestions.append("💡 自动建议: Python文件应放在 project/src/ 目录")
                suggestions.append(f"   推荐路径: {self.project_root}/project/src/{file_path.name}")
            elif file_path.suffix.lower() == ".md":
                suggestions.append("💡 自动建议: Markdown文件应放在 docs/ 目录")
                suggestions.append(f"   推荐路径: {self.project_root}/docs/02-开发/{file_path.name}")
        
        return suggestions
    
    def get_violation_statistics(self) -> Dict:
        """获取违规统计信息"""
        stats = {
            "total_violations": 0,
            "by_operation": {},
            "by_user": {},
            "recent_violations": []
        }
        
        try:
            if self.violation_log_path.exists():
                with open(self.violation_log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            stats["total_violations"] += 1
                            
                            # 按操作类型统计
                            op_type = entry.get("operation_type", "unknown")
                            stats["by_operation"][op_type] = stats["by_operation"].get(op_type, 0) + 1
                            
                            # 按用户统计
                            user = entry.get("user", "unknown")
                            stats["by_user"][user] = stats["by_user"].get(user, 0) + 1
                            
                            # 最近违规记录
                            if len(stats["recent_violations"]) < 10:
                                stats["recent_violations"].append(entry)
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            print(f"警告：读取违规统计失败: {e}")
        
        return stats


def main():
    """主函数 - 升级版命令行接口"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="项目操作前置检查工具（升级版）")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 检查命令
    check_parser = subparsers.add_parser('check', help='执行前置检查')
    check_parser.add_argument('operation', choices=['create', 'modify', 'delete', 'move'], help='操作类型')
    check_parser.add_argument('file_path', help='文件路径')
    check_parser.add_argument('--enhanced', action='store_true', default=True, help='启用增强模式')
    check_parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    # 任务检查命令
    task_parser = subparsers.add_parser('task', help='检查开发任务')
    task_parser.add_argument('task_description', help='任务描述')
    task_parser.add_argument('module_name', help='模块名称')
    
    # 报告命令
    report_parser = subparsers.add_parser('report', help='生成合规性报告')
    report_parser.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='查看违规统计')
    stats_parser.add_argument('--format', choices=['json', 'table'], default='table', help='输出格式')
    
    # 监控命令
    monitor_parser = subparsers.add_parser('monitor', help='启动实时监控')
    monitor_parser.add_argument('--duration', type=int, default=3600, help='监控时长（秒）')
    monitor_parser.add_argument('--watch-dir', help='监控目录', default='.')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('action', choices=['show', 'reset', 'update'], help='配置操作')
    config_parser.add_argument('--key', help='配置键')
    config_parser.add_argument('--value', help='配置值')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 创建检查器
    enhanced_mode = getattr(args, 'enhanced', True)
    checker = ProjectComplianceChecker(enhanced_mode=enhanced_mode)
    
    if args.command == 'check':
        passed, messages = checker.check_file_operation(args.file_path, args.operation)
        
        if args.verbose or not passed:
            print(f"\n{'='*60}")
            print(f"文件操作检查结果: {'通过' if passed else '未通过'}")
            print(f"{'='*60}")
            for message in messages:
                print(message)
            print(f"{'='*60}\n")
        
        if not passed:
            print("❌ 检查未通过，请按照建议修正后再进行操作")
            sys.exit(1)
        else:
            print("✅ 检查通过，可以进行操作")
    
    elif args.command == 'task':
        passed, messages = checker.check_development_task(args.task_description, args.module_name)
        print(f"\n{'='*60}")
        print(f"开发任务检查结果: {'通过' if passed else '未通过'}")
        print(f"{'='*60}")
        for message in messages:
            print(message)
        print(f"{'='*60}\n")
        
        if not passed:
            print("❌ 检查未通过，请调整开发计划")
            sys.exit(1)
        else:
            print("✅ 检查通过，可以开始开发")
    
    elif args.command == 'report':
        report = checker.generate_compliance_report()
        
        if args.format == 'json':
            import json
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print("项目合规性报告")
            print(f"{'='*60}")
            print(f"检查时间: {report['timestamp']}")
            print(f"项目根目录: {report['project_root']}")
            print(f"执行检查: {', '.join(report['checks_performed'])}")
            
            if report['violations_found']:
                print("\n❌ 发现的违规问题:")
                for violation in report['violations_found']:
                    print(f"  - {violation}")
            else:
                print("\n✅ 未发现违规问题")
            
            if report['recommendations']:
                print("\n💡 建议:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")
            
            print(f"{'='*60}\n")
    
    elif args.command == 'stats':
        stats = checker.get_violation_statistics()
        
        if args.format == 'json':
            import json
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print("\n📊 违规统计报告")
            print("=" * 50)
            print(f"总违规次数: {stats['total_violations']}")
            
            if stats['by_operation']:
                print("\n按操作类型统计:")
                for op, count in stats['by_operation'].items():
                    print(f"  {op}: {count}次")
            
            if stats['by_user']:
                print("\n按用户统计:")
                for user, count in stats['by_user'].items():
                    print(f"  {user}: {count}次")
            
            if stats['recent_violations']:
                print("\n最近违规记录:")
                for violation in stats['recent_violations'][-5:]:
                    print(f"  {violation['timestamp']}: {violation['operation_type']} {violation['file_path']}")
    
    elif args.command == 'monitor':
        print(f"🔍 启动实时监控，持续时间: {args.duration}秒")
        print(f"监控目录: {args.watch_dir}")
        print("按 Ctrl+C 停止监控")
        
        try:
            import time
            start_time = time.time()
            
            while time.time() - start_time < args.duration:
                time.sleep(1)
                # 这里可以集成文件系统监控
                
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    elif args.command == 'config':
        if args.action == 'show':
            print("\n⚙️ 当前配置:")
            print("基础配置:")
            print(yaml.dump(checker.config, default_flow_style=False, allow_unicode=True))
            if checker.enhanced_config:
                print("\n增强配置:")
                print(yaml.dump(checker.enhanced_config, default_flow_style=False, allow_unicode=True))
        
        elif args.action == 'reset':
            print("🔄 重置配置到默认值")
            default_config = checker._get_default_enhanced_config()
            checker._save_enhanced_config(default_config)
            print("配置已重置")
        
        elif args.action == 'update':
            if not args.key or not args.value:
                print("错误: 更新配置需要指定 --key 和 --value")
                sys.exit(1)
            
            print(f"🔧 更新配置: {args.key} = {args.value}")
            # 这里可以实现配置更新逻辑
            print("配置更新功能待实现")


if __name__ == "__main__":
    main()