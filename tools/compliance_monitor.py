#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目合规性自动化监控系统（升级版）

功能：实时监控项目目录和文件操作，自动检测违规行为并采取相应措施
新增：日期一致性检查、更完善的监控机制
作者：雨俊（技术负责人）
创建日期：2025年1月13日
升级日期：2025年1月13日
"""

import os
import sys
import time
import json
import yaml
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, DirCreatedEvent

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))
from pre_operation_check import ProjectComplianceChecker


class ComplianceViolation:
    """合规性违规记录（升级版）"""
    
    def __init__(self, violation_type: str, file_path: str, description: str, severity: str = "warning"):
        self.violation_type = violation_type
        self.file_path = file_path
        self.description = description
        self.severity = severity  # error, warning, info
        self.timestamp = datetime.now()
        self.resolved = False
        self.resolution_action = None
        self.date_issues = []  # 新增：日期相关问题
        self.suggested_fixes = []  # 新增：修复建议
    
    def to_dict(self) -> Dict:
        return {
            "violation_type": self.violation_type,
            "file_path": self.file_path,
            "description": self.description,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_action": self.resolution_action
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.violation_type}: {self.description} ({self.file_path})"


class DateConsistencyChecker:
    """日期一致性检查器"""
    
    def __init__(self):
        self.forbidden_dates = [
            "2024年", "2023年", "2022年", "2021年", "2020年", "2019年", "2018年", "2017年", 
            "2016年", "2015年", "2014年", "2013年", "2012年", "2011年", "2010年", "2009年", 
            "2008年", "2007年", "2006年", "2019-", "2018-", "2017-", "2016-", "2015-", 
            "2014-", "2013-", "2012-", "2011-", "2010-", "2009-", "2008-", "2007-", 
            "2006-", "2020/", "2019/", "2018/", "2017/", "2016/", "2015/", "2014/", 
            "2013/", "2012/", "2011/", "2010/", "2009/", "2008/", "2007/", "2006/"
        ]
        self.date_patterns = [
            r'创建日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'修改日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'更新日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'升级日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'完成日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'创建日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
            r'修改日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
            r'更新日期[：:]\s*(\d{4}-\d{1,2}-\d{1,2})',
            r'创建日期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})',
            r'修改日期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})',
            r'更新日期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})'
        ]
    
    def check_file_dates(self, file_path: Path) -> List[str]:
        """检查文件中的日期一致性"""
        issues = []
        
        if not file_path.exists() or file_path.suffix.lower() not in ['.py', '.md', '.txt']:
            return issues
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查禁止的历史日期
            for forbidden_date in self.forbidden_dates:
                if forbidden_date in content:
                    issues.append(f"发现禁止的历史日期: {forbidden_date}")
            
            # 检查日期格式和合理性
            for pattern in self.date_patterns:
                matches = re.findall(pattern, content)
                for date_str in matches:
                    date_issues = self._validate_date(date_str)
                    issues.extend(date_issues)
            
        except Exception as e:
            issues.append(f"日期检查失败: {str(e)}")
        
        return issues
    
    def _validate_date(self, date_str: str) -> List[str]:
        """验证日期格式和合理性"""
        issues = []
        
        try:
            # 解析日期
            date_match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if date_match:
                year, month, day = map(int, date_match.groups())
                file_date = datetime(year, month, day)
                
                # 检查日期是否合理（不能是未来日期）
                if file_date > datetime.now():
                    issues.append(f"发现未来日期: {date_str}")
                
                # 检查日期是否过于久远（超过2年）
                if (datetime.now() - file_date).days > 730:
                    issues.append(f"发现较旧日期: {date_str}，建议更新")
                    
        except ValueError:
            issues.append(f"日期格式错误: {date_str}")
        
        return issues
    
    def suggest_date_fix(self, file_path: Path) -> List[str]:
        """建议日期修复方案"""
        suggestions = []
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        suggestions.append(f"建议将日期更新为: {current_date}")
        suggestions.append("可使用自动修复功能批量更新日期")
        
        return suggestions


class ComplianceFileSystemHandler(FileSystemEventHandler):
    """文件系统事件处理器（升级版）"""
    
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.checker = monitor.checker
        self.date_checker = DateConsistencyChecker()  # 新增日期检查器
        
    def on_created(self, event):
        """文件/目录创建事件"""
        if event.is_directory:
            self._handle_directory_created(event)
        else:
            self._handle_file_created(event)
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self._handle_file_modified(event)
    
    def on_deleted(self, event):
        """文件/目录删除事件"""
        self._handle_file_deleted(event)
    
    def _handle_file_created(self, event: FileCreatedEvent):
        """处理文件创建事件（升级版）"""
        file_path = event.src_path
        
        # 忽略临时文件和缓存文件
        if self._should_ignore_file(file_path):
            return
        
        # 检查文件操作合规性
        passed, messages = self.checker.check_file_operation(file_path, "create")
        
        # 新增：日期一致性检查
        date_issues = self.date_checker.check_file_dates(Path(file_path))
        if date_issues:
            messages.extend([f"日期问题: {issue}" for issue in date_issues])
            passed = False
        
        if not passed:
            violation = ComplianceViolation(
                violation_type="unauthorized_file_creation",
                file_path=file_path,
                description=f"未经授权的文件创建: {'; '.join(messages)}",
                severity="error"
            )
            
            # 添加日期相关问题和修复建议
            violation.date_issues = date_issues
            if date_issues:
                violation.suggested_fixes = self.date_checker.suggest_date_fix(Path(file_path))
            
            self.monitor.record_violation(violation)
            
            # 如果启用了阻止操作，尝试移动文件
            if self.monitor.config.get("compliance", {}).get("violation_handling", {}).get("block_operation", False):
                self._auto_resolve_file_violation(file_path, violation)
    
    def _handle_directory_created(self, event: DirCreatedEvent):
        """处理目录创建事件"""
        dir_path = event.src_path
        
        # 检查目录是否符合标准结构
        if not self._is_valid_directory(dir_path):
            violation = ComplianceViolation(
                violation_type="directory_structure_violation",
                file_path=dir_path,
                description=f"创建了非标准目录结构: {dir_path}",
                severity="warning"
            )
            self.monitor.record_violation(violation)
    
    def _handle_file_modified(self, event: FileModifiedEvent):
        """处理文件修改事件（升级版）"""
        file_path = event.src_path
        
        # 检查是否为受保护文件
        if self._is_protected_file(file_path):
            violation = ComplianceViolation(
                violation_type="protected_file_modification",
                file_path=file_path,
                description=f"尝试修改受保护文件: {file_path}",
                severity="error"
            )
            self.monitor.record_violation(violation)
        
        # 新增：对修改的文件进行日期一致性检查
        if not self._should_ignore_file(file_path):
            date_issues = self.date_checker.check_file_dates(Path(file_path))
            if date_issues:
                violation = ComplianceViolation(
                    violation_type="date_consistency_violation",
                    file_path=file_path,
                    description=f"文件修改后发现日期一致性问题: {'; '.join(date_issues)}",
                    severity="warning"
                )
                violation.date_issues = date_issues
                violation.suggested_fixes = self.date_checker.suggest_date_fix(Path(file_path))
                self.monitor.record_violation(violation)
    
    def _handle_file_deleted(self, event):
        """处理文件删除事件"""
        file_path = event.src_path
        
        # 检查是否为重要文件
        if self._is_important_file(file_path):
            violation = ComplianceViolation(
                violation_type="important_file_deletion",
                file_path=file_path,
                description=f"删除了重要文件: {file_path}",
                severity="error"
            )
            self.monitor.record_violation(violation)
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """判断是否应该忽略文件"""
        ignore_patterns = [
            ".cache", ".tmp", ".temp", "~$", ".swp", ".swo",
            "__pycache__", ".pyc", ".pyo", ".DS_Store", "Thumbs.db"
        ]
        
        file_path_lower = file_path.lower()
        return any(pattern in file_path_lower for pattern in ignore_patterns)
    
    def _is_valid_directory(self, dir_path: str) -> bool:
        """检查目录是否有效"""
        try:
            rel_path = Path(dir_path).relative_to(self.monitor.project_root)
            if len(rel_path.parts) > 0:
                top_dir = rel_path.parts[0]
                standard_dirs = self.monitor.config.get("directory_structure", {}).get("standard_directories", {})
                return top_dir in standard_dirs or top_dir.startswith('.')
        except ValueError:
            return False
        return True
    
    def _is_protected_file(self, file_path: str) -> bool:
        """检查是否为受保护文件"""
        try:
            rel_path = str(Path(file_path).relative_to(self.monitor.project_root)).replace('\\', '/')
            protected_files = self.monitor.config.get("permissions", {}).get("protected_files", [])
            return rel_path in protected_files
        except ValueError:
            return False
    
    def _is_important_file(self, file_path: str) -> bool:
        """检查是否为重要文件"""
        important_patterns = [
            "docs/01-设计/", "docs/03-管理/", "tools/", "project/src/"
        ]
        
        try:
            rel_path = str(Path(file_path).relative_to(self.monitor.project_root)).replace('\\', '/')
            return any(pattern in rel_path for pattern in important_patterns)
        except ValueError:
            return False
    
    def _auto_resolve_file_violation(self, file_path: str, violation: ComplianceViolation):
        """自动解决文件违规问题"""
        try:
            # 尝试将文件移动到合适的位置
            suggested_dir = self._suggest_correct_location(file_path)
            if suggested_dir:
                target_path = suggested_dir / Path(file_path).name
                
                # 确保目标目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                Path(file_path).rename(target_path)
                
                violation.resolved = True
                violation.resolution_action = f"文件已自动移动到: {target_path}"
                
                self.monitor.logger.info(f"自动解决违规: {file_path} -> {target_path}")
        
        except Exception as e:
            self.monitor.logger.error(f"自动解决违规失败: {e}")
    
    def _suggest_correct_location(self, file_path: str) -> Optional[Path]:
        """建议正确的文件位置"""
        file_ext = Path(file_path).suffix.lower()
        
        suggestions = {
            ".txt": self.monitor.project_root / "bak" / "待清理资料",
            ".log": self.monitor.project_root / "logs" / "其他日志",
            ".tmp": self.monitor.project_root / "bak" / "待清理资料",
            ".temp": self.monitor.project_root / "bak" / "待清理资料",
            ".bak": self.monitor.project_root / "bak" / "常规备份",
            ".pro": self.monitor.project_root / "AI助理生产成果",
            ".prt": self.monitor.project_root / "AI助理生产成果",
            ".asm": self.monitor.project_root / "AI助理生产成果",
            ".drw": self.monitor.project_root / "AI助理生产成果",
        }
        
        return suggestions.get(file_ext)


class ComplianceMonitor:
    """合规性监控器"""
    
    def __init__(self, project_root: str = "s:/PG-Dev"):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "docs" / "03-管理" / "project_config.yaml"
        self.violations_file = self.project_root / "logs" / "合规性报告" / "violations.json"
        
        # 确保日志目录存在
        self.violations_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化检查器
        self.checker = ProjectComplianceChecker(str(self.project_root))
        
        # 初始化日志
        self._setup_logging()
        
        # 违规记录
        self.violations: List[ComplianceViolation] = []
        self._load_violations()
        
        # 文件系统监控
        self.observer = None
        self.handler = ComplianceFileSystemHandler(self)
        
        # 统计信息
        self.stats = {
            "total_violations": 0,
            "resolved_violations": 0,
            "auto_resolved": 0,
            "manual_resolved": 0,
            "start_time": datetime.now()
        }
    
    def _load_config(self) -> Dict:
        """加载项目配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"警告: 无法加载配置文件 {self.config_file}: {e}")
            return {}
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "logs" / "系统日志"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"compliance_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ComplianceMonitor')
    
    def _load_violations(self):
        """加载历史违规记录"""
        if self.violations_file.exists():
            try:
                with open(self.violations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        violation = ComplianceViolation(
                            violation_type=item["violation_type"],
                            file_path=item["file_path"],
                            description=item["description"],
                            severity=item["severity"]
                        )
                        violation.timestamp = datetime.fromisoformat(item["timestamp"])
                        violation.resolved = item["resolved"]
                        violation.resolution_action = item.get("resolution_action")
                        self.violations.append(violation)
            except Exception as e:
                self.logger.error(f"加载违规记录失败: {e}")
    
    def _save_violations(self):
        """保存违规记录"""
        try:
            data = [violation.to_dict() for violation in self.violations]
            with open(self.violations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存违规记录失败: {e}")
    
    def record_violation(self, violation: ComplianceViolation):
        """记录违规行为"""
        self.violations.append(violation)
        self.stats["total_violations"] += 1
        
        # 记录日志
        self.logger.warning(str(violation))
        
        # 保存到文件
        self._save_violations()
        
        # 发送通知
        self._send_notification(violation)
    
    def _send_notification(self, violation: ComplianceViolation):
        """发送违规通知"""
        notification_config = self.config.get("notifications", {}).get("violations", {})
        
        if not notification_config.get("enabled", True):
            return
        
        methods = notification_config.get("methods", ["log", "console"])
        
        if "console" in methods:
            print(f"\n[WARNING] 合规性违规警告")
            print(f"类型: {violation.violation_type}")
            print(f"文件: {violation.file_path}")
            print(f"描述: {violation.description}")
            print(f"严重程度: {violation.severity}")
            print(f"时间: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.config.get("compliance", {}).get("monitoring", {}).get("enabled", True):
            self.logger.info("监控已禁用")
            return
        
        self.logger.info(f"开始监控项目目录: {self.project_root}")
        
        # 设置文件系统监控
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        try:
            # 定期检查
            check_interval = self.config.get("compliance", {}).get("monitoring", {}).get("check_interval", 300)
            
            while True:
                time.sleep(check_interval)
                self._periodic_check()
                
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，正在关闭监控...")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.logger.info("监控已停止")
        self._generate_summary_report()
    
    def _periodic_check(self):
        """定期检查"""
        self.logger.info("执行定期合规性检查...")
        
        # 检查项目结构
        structure_violations = self._check_project_structure()
        for violation in structure_violations:
            self.record_violation(violation)
        
        # 检查文件命名
        naming_violations = self._check_naming_conventions()
        for violation in naming_violations:
            self.record_violation(violation)
        
        # 新增：检查日期一致性
        date_violations = self._check_date_consistency()
        for violation in date_violations:
            self.record_violation(violation)
        
        # 清理旧的违规记录
        self._cleanup_old_violations()
        
        self.logger.info(f"定期检查完成，发现 {len(structure_violations + naming_violations + date_violations)} 个新违规")
    
    def _check_project_structure(self) -> List[ComplianceViolation]:
        """检查项目结构"""
        violations = []
        
        # 检查根目录文件
        for item in self.project_root.iterdir():
            if item.is_file():
                passed, messages = self.checker.check_file_operation(str(item), "create")
                if not passed:
                    violation = ComplianceViolation(
                        violation_type="directory_structure_violation",
                        file_path=str(item),
                        description=f"根目录存在不当文件: {'; '.join(messages)}",
                        severity="warning"
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_naming_conventions(self) -> List[ComplianceViolation]:
        """检查文件命名规范"""
        violations = []
        
        # 遍历项目文件
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self.handler._should_ignore_file(str(file_path)):
                messages = []
                passed = self.checker._check_naming_convention(file_path, messages)
                if not passed:
                    violation = ComplianceViolation(
                        violation_type="naming_convention_violation",
                        file_path=str(file_path),
                        description=f"文件命名不符合规范: {'; '.join(messages)}",
                        severity="info"
                    )
                    violations.append(violation)
        
        return violations
    
    def _check_date_consistency(self) -> List[ComplianceViolation]:
        """检查日期一致性"""
        violations = []
        
        # 遍历项目文件进行日期检查
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self.handler._should_ignore_file(str(file_path)):
                date_issues = self.handler.date_checker.check_file_dates(file_path)
                if date_issues:
                    violation = ComplianceViolation(
                        violation_type="date_consistency_violation",
                        file_path=str(file_path),
                        description=f"日期一致性问题: {'; '.join(date_issues)}",
                        severity="warning"
                    )
                    violation.date_issues = date_issues
                    violation.suggested_fixes = self.handler.date_checker.suggest_date_fix(file_path)
                    violations.append(violation)
        
        return violations
    
    def _cleanup_old_violations(self):
        """清理旧的违规记录"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        old_count = len(self.violations)
        self.violations = [v for v in self.violations if v.timestamp > cutoff_date or not v.resolved]
        new_count = len(self.violations)
        
        if old_count != new_count:
            self.logger.info(f"清理了 {old_count - new_count} 条旧违规记录")
            self._save_violations()
    
    def _generate_summary_report(self):
        """生成汇总报告（升级版）"""
        report_file = self.project_root / "logs" / "合规性报告" / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 统计信息
        total_violations = len(self.violations)
        resolved_violations = len([v for v in self.violations if v.resolved])
        unresolved_violations = total_violations - resolved_violations
        date_violations = len([v for v in self.violations if v.violation_type == "date_consistency_violation"])
        
        # 按类型分组
        violations_by_type = {}
        for violation in self.violations:
            if violation.violation_type not in violations_by_type:
                violations_by_type[violation.violation_type] = []
            violations_by_type[violation.violation_type].append(violation)
        
        # 生成报告
        report_content = f"""# 项目合规性监控汇总报告（升级版）

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**监控开始时间**: {self.stats['start_time'].strftime('%Y年%m月%d日 %H:%M:%S')}
**监控持续时间**: {datetime.now() - self.stats['start_time']}

## 统计概览

- **总违规数**: {total_violations}
- **已解决**: {resolved_violations}
- **未解决**: {unresolved_violations}
- **日期一致性问题**: {date_violations}
- **解决率**: {(resolved_violations/total_violations*100) if total_violations > 0 else 0:.1f}%

## 违规类型分布

"""
        
        for violation_type, violations in violations_by_type.items():
            type_name = {
                "date_consistency_violation": "日期一致性违规",
                "file_naming_violation": "文件命名违规", 
                "unauthorized_file_creation": "未授权文件创建",
                "protected_file_modification": "受保护文件修改",
                "directory_structure_violation": "目录结构违规",
                "naming_convention_violation": "命名规范违规",
                "important_file_deletion": "重要文件删除"
            }.get(violation_type, violation_type)
            
            report_content += f"### {type_name} ({violation_type})\n"
            report_content += f"- 总数: {len(violations)}\n"
            report_content += f"- 已解决: {len([v for v in violations if v.resolved])}\n"
            report_content += f"- 未解决: {len([v for v in violations if not v.resolved])}\n\n"
        
        # 未解决的违规详情
        unresolved = [v for v in self.violations if not v.resolved]
        if unresolved:
            report_content += "## 未解决的违规问题\n\n"
            for violation in unresolved[-10:]:  # 最近10个
                report_content += f"- **{violation.violation_type}**: {violation.description}\n"
                report_content += f"  - 文件: `{violation.file_path}`\n"
                report_content += f"  - 时间: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                report_content += f"  - 严重程度: {violation.severity}\n"
                if hasattr(violation, 'date_issues') and violation.date_issues:
                    report_content += f"  - 日期问题: {', '.join(violation.date_issues)}\n"
                if hasattr(violation, 'suggested_fixes') and violation.suggested_fixes:
                    report_content += f"  - 修复建议: {', '.join(violation.suggested_fixes)}\n"
                report_content += "\n"
        
        # 建议
        report_content += """## 改进建议

1. **定期运行前置检查脚本**，在创建文件前验证合规性
2. **遵循项目架构设计文档**，将文件放置在正确的目录中
3. **使用标准的文件命名规范**，避免使用非法字符
4. **及时清理临时文件**，保持项目目录整洁
5. **定期查看合规性报告**，及时发现和解决问题
6. **统一日期格式**，避免使用历史日期，确保日期一致性
7. **使用自动修复功能**，批量处理日期一致性问题

## 相关文档

- [项目架构设计](../docs/01-设计/项目架构设计.md)
- [规范与流程](../docs/03-管理/规范与流程.md)
- [项目配置文件](../docs/03-管理/project_config.yaml)
- [日期规范指南](../docs/03-管理/日期规范指南.md)
"""
        
        # 保存报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"汇总报告已生成: {report_file}")
        except Exception as e:
            self.logger.error(f"生成汇总报告失败: {e}")
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        total_violations = len(self.violations)
        resolved_violations = len([v for v in self.violations if v.resolved])
        
        return {
            "monitoring_active": self.observer is not None and self.observer.is_alive(),
            "project_root": str(self.project_root),
            "total_violations": total_violations,
            "resolved_violations": resolved_violations,
            "unresolved_violations": total_violations - resolved_violations,
            "last_check": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.stats["start_time"])
        }


def main():
    """主函数（升级版）"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目合规性监控系统（升级版）")
    parser.add_argument("--start", action="store_true", help="启动监控")
    parser.add_argument("--check", action="store_true", help="执行一次性检查")
    parser.add_argument("--status", action="store_true", help="显示监控状态")
    parser.add_argument("--report", action="store_true", help="生成汇总报告")
    parser.add_argument("--date-check", action="store_true", help="执行日期一致性检查")
    parser.add_argument("--file", help="指定要检查的文件（用于date-check）")
    parser.add_argument("--fix", action="store_true", help="自动修复日期问题")
    parser.add_argument("--project-root", default="s:/PG-Dev", help="项目根目录")
    
    args = parser.parse_args()
    
    monitor = ComplianceMonitor(args.project_root)
    
    if args.start:
        print("启动项目合规性监控系统（升级版）...")
        monitor.start_monitoring()
    
    elif args.check:
        print("执行一次性合规性检查（包含日期一致性）...")
        monitor._periodic_check()
        print("检查完成")
    
    elif args.status:
        status = monitor.get_status()
        print("\n项目合规性监控状态:")
        print(f"监控状态: {'运行中' if status['monitoring_active'] else '已停止'}")
        print(f"项目根目录: {status['project_root']}")
        print(f"总违规数: {status['total_violations']}")
        print(f"已解决: {status['resolved_violations']}")
        print(f"未解决: {status['unresolved_violations']}")
        print(f"运行时间: {status['uptime']}")
    
    elif args.report:
        print("生成汇总报告（升级版）...")
        monitor._generate_summary_report()
        print("报告生成完成")
    
    elif args.date_check:
        print("[日期检查] 执行日期一致性检查...")
        if args.file:
            # 检查指定文件
            file_path = Path(args.file)
            if file_path.exists():
                date_issues = monitor.handler.date_checker.check_file_dates(file_path)
                if date_issues:
                    print(f"[错误] 发现日期问题: {'; '.join(date_issues)}")
                    if args.fix:
                        fixes = monitor.handler.date_checker.suggest_date_fix(file_path)
                        print(f"[修复] 修复建议: {'; '.join(fixes)}")
                else:
                    print("[成功] 未发现日期问题")
            else:
                print(f"[错误] 文件不存在: {args.file}")
        else:
            # 检查整个项目
            violations = monitor._check_date_consistency()
            if violations:
                print(f"[错误] 发现 {len(violations)} 个日期一致性问题")
                for v in violations[:5]:  # 显示前5个
                    print(f"  - {v.file_path}: {v.description}")
            else:
                print("[成功] 未发现日期一致性问题")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()