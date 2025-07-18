#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目规范强制遵守启用脚本

功能：一键启用项目规范强制遵守机制，确保所有操作都符合项目架构设计
作者：雨俊（技术负责人）
创建日期：2025年1月13日
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ComplianceEnabler:
    """合规性启用器"""
    
    def __init__(self, project_root: str = "s:/PG-Dev"):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "docs" / "03-管理" / "project_config.yaml"
        self.tools_dir = self.project_root / "tools"
        
        # 核心脚本路径
        self.pre_check_script = self.tools_dir / "pre_operation_check.py"
        self.monitor_script = self.tools_dir / "compliance_monitor.py"
        self.enable_script = self.tools_dir / "enable_compliance.py"
        
        # 状态文件
        self.status_file = self.project_root / ".cache" / "compliance_status.json"
        
        # 确保必要目录存在
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
    
    def check_prerequisites(self) -> List[str]:
        """检查前置条件"""
        issues = []
        
        # 检查项目根目录
        if not self.project_root.exists():
            issues.append(f"项目根目录不存在: {self.project_root}")
        
        # 检查配置文件
        if not self.config_file.exists():
            issues.append(f"项目配置文件不存在: {self.config_file}")
        
        # 检查核心脚本
        if not self.pre_check_script.exists():
            issues.append(f"前置检查脚本不存在: {self.pre_check_script}")
        
        if not self.monitor_script.exists():
            issues.append(f"监控脚本不存在: {self.monitor_script}")
        
        # 检查Python依赖
        try:
            import yaml
            import watchdog
        except ImportError as e:
            issues.append(f"缺少Python依赖: {e}")
        
        # 检查核心文档
        core_docs = [
            "docs/01-设计/开发任务书.md",
            "docs/01-设计/技术方案.md",
            "docs/01-设计/项目架构设计.md",
            "docs/03-管理/规范与流程.md"
        ]
        
        for doc in core_docs:
            doc_path = self.project_root / doc
            if not doc_path.exists():
                issues.append(f"核心文档不存在: {doc}")
        
        return issues
    
    def load_config(self) -> Dict:
        """加载项目配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"警告: 无法加载配置文件: {e}")
            return {}
    
    def update_config(self, updates: Dict):
        """更新项目配置"""
        try:
            config = self.load_config()
            
            # 深度合并配置
            def deep_merge(base: Dict, updates: Dict) -> Dict:
                for key, value in updates.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
                return base
            
            config = deep_merge(config, updates)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, indent=2)
            
            print(f"[成功] 配置已更新: {self.config_file}")
            
        except Exception as e:
            print(f"[错误] 更新配置失败: {e}")
    
    def create_wrapper_scripts(self):
        """创建包装脚本"""
        # 创建文件操作包装脚本
        file_wrapper = self.tools_dir / "safe_file_operation.py"
        file_wrapper_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全文件操作包装器
自动调用前置检查，确保文件操作符合规范
"""

import sys
import subprocess
from pathlib import Path

def check_and_execute(operation_type, file_path, *args):
    """检查并执行文件操作"""
    # 调用前置检查
    check_cmd = [
        sys.executable,
        "{self.pre_check_script}",
        "--check-file", file_path,
        "--operation", operation_type
    ]
    
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[阻止] 操作被阻止: {{file_path}}")
        print(result.stdout)
        return False
    
    print(f"[通过] 检查通过: {{file_path}}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python safe_file_operation.py <operation> <file_path> [args...]")
        sys.exit(1)
    
    operation = sys.argv[1]
    file_path = sys.argv[2]
    args = sys.argv[3:]
    
    if check_and_execute(operation, file_path, *args):
        print("操作已通过合规性检查")
    else:
        print("操作被合规性检查阻止")
        sys.exit(1)
'''
        
        try:
            with open(file_wrapper, 'w', encoding='utf-8') as f:
                f.write(file_wrapper_content)
            print(f"[成功] 创建文件操作包装器: {file_wrapper}")
        except Exception as e:
            print(f"[错误] 创建文件操作包装器失败: {e}")
        
        # 创建开发任务检查脚本
        task_checker = self.tools_dir / "check_development_task.py"
        task_checker_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发任务合规性检查器
确保开发任务符合项目规范
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))
from pre_operation_check import ProjectComplianceChecker

def main():
    if len(sys.argv) < 3:
        print("用法: python check_development_task.py <task_description> <module_name>")
        sys.exit(1)
    
    task_description = sys.argv[1]
    module_name = sys.argv[2]
    
    checker = ProjectComplianceChecker()
    passed, messages = checker.check_development_task(task_description, module_name)
    
    print(f"\\n{{'='*60}}")
    print(f"开发任务检查结果: {{'通过' if passed else '未通过'}}")
    print(f"{{'='*60}}")
    for message in messages:
        print(message)
    print(f"{{'='*60}}\\n")
    
    if not passed:
        print("[错误] 开发任务不符合项目规范，请调整后重试")
        sys.exit(1)
    else:
        print("[成功] 开发任务符合项目规范，可以开始开发")

if __name__ == "__main__":
    main()
'''
        
        try:
            with open(task_checker, 'w', encoding='utf-8') as f:
                f.write(task_checker_content)
            print(f"[成功] 创建开发任务检查器: {task_checker}")
        except Exception as e:
            print(f"[错误] 创建开发任务检查器失败: {e}")
    
    def install_dependencies(self):
        """安装必要的Python依赖"""
        dependencies = [
            "pyyaml",
            "watchdog"
        ]
        
        for dep in dependencies:
            try:
                __import__(dep.replace('-', '_'))
                print(f"[已存在] 依赖已存在: {dep}")
            except ImportError:
                print(f"[安装] 安装依赖: {dep}")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    print(f"[成功] 依赖安装成功: {dep}")
                except subprocess.CalledProcessError as e:
                    print(f"[错误] 依赖安装失败: {dep} - {e}")
    
    def create_startup_script(self):
        """创建启动脚本"""
        startup_script = self.tools_dir / "start_compliance_monitoring.bat"
        startup_content = f'''@echo off
echo 启动项目合规性监控系统...
cd /d "{self.project_root}"
python "{self.monitor_script}" --start
pause
'''
        
        try:
            with open(startup_script, 'w', encoding='utf-8') as f:
                f.write(startup_content)
            print(f"[成功] 创建启动脚本: {startup_script}")
        except Exception as e:
            print(f"[错误] 创建启动脚本失败: {e}")
        
        # 创建PowerShell启动脚本
        ps_startup_script = self.tools_dir / "start_compliance_monitoring.ps1"
        ps_startup_content = f'''# 项目合规性监控启动脚本
Write-Host "启动项目合规性监控系统..." -ForegroundColor Green
Set-Location "{self.project_root}"
python "{self.monitor_script}" --start
Read-Host "按任意键退出"
'''
        
        try:
            with open(ps_startup_script, 'w', encoding='utf-8') as f:
                f.write(ps_startup_content)
            print(f"[成功] 创建PowerShell启动脚本: {ps_startup_script}")
        except Exception as e:
            print(f"[错误] 创建PowerShell启动脚本失败: {e}")
    
    def save_status(self, status: Dict):
        """保存启用状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[错误] 保存状态失败: {e}")
    
    def load_status(self) -> Dict:
        """加载启用状态"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"警告: 加载状态失败: {e}")
        return {}
    
    def enable_compliance(self) -> bool:
        """启用合规性机制"""
        print("\n[工具] 启用项目规范强制遵守机制...\n")
        
        # 1. 检查前置条件
        print("[1/5] 检查前置条件...")
        issues = self.check_prerequisites()
        if issues:
            print("[错误] 发现以下问题:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        print("[成功] 前置条件检查通过")
        
        # 2. 安装依赖
        print("\n[2/5] 检查并安装依赖...")
        self.install_dependencies()
        
        # 3. 更新配置
        print("\n[3/5] 更新项目配置...")
        compliance_config = {
            "compliance": {
                "enforce_checks": True,
                "pre_operation_check": {
                    "enabled": True,
                    "script_path": "tools/pre_operation_check.py"
                },
                "monitoring": {
                    "enabled": True,
                    "check_interval": 300,
                    "log_violations": True
                },
                "violation_handling": {
                    "block_operation": True,
                    "require_approval": True,
                    "log_level": "ERROR"
                }
            }
        }
        self.update_config(compliance_config)
        
        # 4. 创建包装脚本
        print("\n[4/5] 创建辅助脚本...")
        self.create_wrapper_scripts()
        
        # 5. 创建启动脚本
        print("\n[5/5] 创建启动脚本...")
        self.create_startup_script()
        
        # 6. 保存状态
        status = {
            "enabled": True,
            "enabled_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "pre_operation_check": True,
                "compliance_monitor": True,
                "wrapper_scripts": True,
                "startup_scripts": True
            }
        }
        self.save_status(status)
        
        print("\n[成功] 项目规范强制遵守机制启用成功!")
        print("\n[说明] 使用说明:")
        print(f"   - 前置检查: python {self.pre_check_script} --check-file <文件路径>")
        print(f"   - 开始监控: python {self.monitor_script} --start")
        print(f"   - 检查状态: python {self.monitor_script} --status")
        print(f"   - 任务检查: python {self.tools_dir}/check_development_task.py <任务描述> <模块名>")
        print(f"   - 快速启动: {self.tools_dir}/start_compliance_monitoring.bat")
        
        print("\n[提醒] 重要提醒:")
        print("   - 所有文件操作前请先运行前置检查")
        print("   - 开发任务前请先进行任务合规性检查")
        print("   - 建议启动实时监控以自动检测违规行为")
        print("   - 定期查看合规性报告以了解项目状态")
        
        return True
    
    def disable_compliance(self) -> bool:
        """禁用合规性机制"""
        print("\n[工具] 禁用项目规范强制遵守机制...\n")
        
        # 更新配置
        compliance_config = {
            "compliance": {
                "enforce_checks": False,
                "pre_operation_check": {
                    "enabled": False
                },
                "monitoring": {
                    "enabled": False
                },
                "violation_handling": {
                    "block_operation": False
                }
            }
        }
        self.update_config(compliance_config)
        
        # 更新状态
        status = self.load_status()
        status["enabled"] = False
        status["disabled_at"] = datetime.now().isoformat()
        self.save_status(status)
        
        print("[成功] 项目规范强制遵守机制已禁用")
        print("[注意] 注意: 脚本文件仍然保留，可以手动调用")
        
        return True
    
    def get_status(self) -> Dict:
        """获取启用状态"""
        status = self.load_status()
        config = self.load_config()
        
        compliance_config = config.get("compliance", {})
        
        return {
            "enabled": status.get("enabled", False),
            "config_enabled": compliance_config.get("enforce_checks", False),
            "pre_check_enabled": compliance_config.get("pre_operation_check", {}).get("enabled", False),
            "monitoring_enabled": compliance_config.get("monitoring", {}).get("enabled", False),
            "block_operations": compliance_config.get("violation_handling", {}).get("block_operation", False),
            "enabled_at": status.get("enabled_at"),
            "version": status.get("version"),
            "components": status.get("components", {})
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="项目规范强制遵守启用工具")
    parser.add_argument("--enable", action="store_true", help="启用合规性机制")
    parser.add_argument("--disable", action="store_true", help="禁用合规性机制")
    parser.add_argument("--status", action="store_true", help="显示启用状态")
    parser.add_argument("--project-root", default="s:/PG-Dev", help="项目根目录")
    
    args = parser.parse_args()
    
    enabler = ComplianceEnabler(args.project_root)
    
    if args.enable:
        success = enabler.enable_compliance()
        sys.exit(0 if success else 1)
    
    elif args.disable:
        success = enabler.disable_compliance()
        sys.exit(0 if success else 1)
    
    elif args.status:
        status = enabler.get_status()
        print("\n[状态] 项目规范强制遵守状态:")
        print(f"   总体状态: {'[已启用]' if status['enabled'] else '[已禁用]'}")
        print(f"   配置启用: {'[是]' if status['config_enabled'] else '[否]'}")
        print(f"   前置检查: {'[是]' if status['pre_check_enabled'] else '[否]'}")
        print(f"   实时监控: {'[是]' if status['monitoring_enabled'] else '[否]'}")
        print(f"   阻止违规: {'[是]' if status['block_operations'] else '[否]'}")
        
        if status['enabled_at']:
            print(f"   启用时间: {status['enabled_at']}")
        
        if status['version']:
            print(f"   版本: {status['version']}")
        
        components = status.get('components', {})
        if components:
            print("   组件状态:")
            for component, enabled in components.items():
                print(f"     - {component}: {'[是]' if enabled else '[否]'}")
    
    else:
        parser.print_help()
        print("\n[提示] 快速启用: python enable_compliance.py --enable")
        print("[提示] 查看状态: python enable_compliance.py --status")


if __name__ == "__main__":
    main()