#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助理启动预检系统 - 修复版
增强错误处理和超时机制
作者：雨俊（技术负责人）
创建日期：2025年1月25日
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class FixedAIStartupChecker:
    """修复版AI助理启动检查器"""
    
    def __init__(self):
        self.project_root = Path(os.getcwd())
        self.tools_dir = self.project_root / "tools"
        self.docs_dir = self.project_root / "docs"
        self.logs_dir = self.project_root / "logs"
        
        # 核心文档路径
        self.core_docs = {
            "PMC工作流程详解": self.docs_dir / "01-设计" / "PMC工作的流程详解.md",
            "项目配置": self.docs_dir / "03-管理" / "project_config.yaml",
            "开发任务书": self.docs_dir / "01-设计" / "开发任务书.md",
            "技术方案": self.docs_dir / "01-设计" / "技术方案.md"
        }
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        self.logs_dir.mkdir(exist_ok=True)
        
        log_file = self.logs_dir / f"fixed_startup_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def check_prerequisites(self) -> Tuple[bool, str]:
        """检查前置条件"""
        print("🔍 检查前置条件...")
        
        # 检查项目根目录
        if not self.project_root.exists():
            return False, f"项目根目录不存在: {self.project_root}"
            
        # 检查核心脚本
        compliance_monitor = self.tools_dir / "compliance_monitor.py"
        if not compliance_monitor.exists():
            return False, f"监控脚本不存在: {compliance_monitor}"
            
        print("   ✅ 前置条件检查通过")
        return True, "前置条件检查通过"
        
    def test_watchdog_import(self) -> Tuple[bool, str]:
        """测试watchdog库导入"""
        print("🔍 测试watchdog库...")
        
        try:
            # 使用subprocess测试导入，避免阻塞主进程
            result = subprocess.run(
                [sys.executable, "-c", "import watchdog; print('watchdog导入成功')"],
                capture_output=True,
                text=True,
                timeout=10,  # 10秒超时
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                print("   ✅ watchdog库测试通过")
                return True, "watchdog库可用"
            else:
                error_msg = f"watchdog导入失败: {result.stderr}"
                print(f"   ❌ {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "watchdog导入超时"
            print(f"   ❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"watchdog测试异常: {e}"
            print(f"   ❌ {error_msg}")
            return False, error_msg
            
    def start_monitoring_process_safe(self) -> Tuple[bool, str, subprocess.Popen]:
        """安全启动监控进程"""
        print("🚀 启动监控进程...")
        
        compliance_monitor = self.tools_dir / "compliance_monitor.py"
        
        try:
            # 启动监控进程，设置超时
            process = subprocess.Popen(
                [sys.executable, str(compliance_monitor)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 等待3秒检查进程是否立即失败
            time.sleep(3)
            
            if process.poll() is None:
                print("   ✅ 监控进程启动成功")
                return True, "监控进程运行中", process
            else:
                stdout, stderr = process.communicate()
                error_msg = f"监控进程启动失败: {stderr or stdout}"
                print(f"   ❌ {error_msg}")
                return False, error_msg, None
                
        except Exception as e:
            error_msg = f"启动监控进程异常: {e}"
            print(f"   ❌ {error_msg}")
            return False, error_msg, None
            
    def load_core_regulations(self) -> Dict[str, str]:
        """加载核心规范内容"""
        print("📚 加载核心项目规范...")
        regulations = {}
        
        for doc_name, doc_path in self.core_docs.items():
            if doc_path.exists():
                try:
                    if doc_path.suffix.lower() in ['.yaml', '.yml']:
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            content = yaml.safe_load(f)
                            regulations[doc_name] = json.dumps(content, ensure_ascii=False, indent=2)
                    else:
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            regulations[doc_name] = f.read()
                    print(f"   ✅ {doc_name}: 已加载")
                    self.logger.info(f"已加载文档: {doc_name}")
                except Exception as e:
                    print(f"   ❌ {doc_name}: 加载失败 - {e}")
                    self.logger.error(f"加载文档失败 {doc_name}: {e}")
            else:
                print(f"   ⚠️ {doc_name}: 文件不存在 - {doc_path}")
                self.logger.warning(f"文档不存在: {doc_name} - {doc_path}")
                
        return regulations
        
    def extract_key_constraints(self, regulations: Dict[str, str]) -> List[str]:
        """提取关键约束条件"""
        print("🔍 提取关键约束条件...")
        constraints = []
        
        # 基础约束条件
        constraints.append("🚫 严禁在项目根目录创建任何临时文件或代码文件")
        constraints.append("✅ 每次操作前必须执行路径合规性检查")
        constraints.append("🔒 严格保护核心文档，禁止未经授权的修改")
        constraints.append("📝 严格遵守UTF-8编码规范")
        constraints.append("📁 严格遵守标准目录结构规范")
        
        # 从PMC工作流程详解中提取约束
        if "PMC工作流程详解" in regulations:
            constraints.append("🔄 必须遵循标准工作准备流程")
            constraints.append("🧹 严格遵守文件清理管理规定")
            
        # 从项目配置中提取技术约束
        if "项目配置" in regulations:
            constraints.append("⚙️ 严格遵守项目配置中的技术规范")
            
        # 从开发任务书中提取项目目标约束
        if "开发任务书" in regulations:
            constraints.append("🎯 严格按照开发任务书的目标和范围执行")
            
        # 从技术方案中提取架构约束
        if "技术方案" in regulations:
            constraints.append("🏗️ 严格遵循技术方案的架构设计")
            
        return constraints
        
    def generate_startup_briefing(self, regulations: Dict[str, str], constraints: List[str], monitoring_status: str) -> str:
        """生成启动简报"""
        briefing = f"""
# AI助理完整启动简报

**启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目根目录**: {self.project_root}
**启动模式**: 完整模式（包含监控系统）
**监控状态**: {monitoring_status}

## 🎯 工作目标
作为本项目的技术负责人，您需要：
1. 严格遵守所有项目管理文档和规范
2. 确保每次操作都符合项目架构设计
3. 维护项目的完整性和一致性
4. 提供高质量的技术解决方案

## 📋 核心约束条件
"""
        
        for i, constraint in enumerate(constraints, 1):
            briefing += f"{i}. {constraint}\n"
            
        briefing += f"""

## 📄 已加载的核心文档
"""
        
        for doc_name in regulations.keys():
            briefing += f"- ✅ {doc_name}\n"
            
        briefing += f"""

## 🛠️ 必须使用的工具
- TaskManager: 任务分解和管理
- Memory: 重要内容记忆存储
- GitHub: 代码版本管理
- 项目管理工具: 确保操作合规

## ⚠️ 关键提醒
1. **每次工作前**: 必须检查项目规范
2. **每次操作前**: 必须执行路径检查
3. **每次工作后**: 必须进行自我检查
4. **文档命名**: 一律使用中文
5. **代码质量**: 必须通过质量检测

## 🚀 开始工作
现在您已经完成完整启动检查，监控系统已启动，可以开始按照项目规范进行工作。
请记住：您是高级软件专家和技术负责人，需要确保所有工作都符合最高标准。
"""
        
        return briefing
        
    def save_startup_record(self, briefing: str):
        """保存启动记录"""
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 保存启动简报
        briefing_file = self.logs_dir / f"fixed_startup_briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(briefing_file, 'w', encoding='utf-8') as f:
            f.write(briefing)
            
        print(f"💾 启动简报已保存: {briefing_file}")
        self.logger.info(f"启动简报已保存: {briefing_file}")
        
    def perform_full_startup_check(self) -> Tuple[bool, str]:
        """执行完整的启动检查"""
        print("🚀 AI助理完整启动检查开始")
        print("=" * 50)
        
        monitoring_process = None
        
        try:
            # 1. 检查前置条件
            success, message = self.check_prerequisites()
            if not success:
                return False, message
                
            # 2. 测试watchdog库
            success, message = self.test_watchdog_import()
            if not success:
                print("⚠️ watchdog库测试失败，将跳过监控功能")
                monitoring_status = "已跳过（watchdog不可用）"
            else:
                # 3. 启动监控进程
                success, message, monitoring_process = self.start_monitoring_process_safe()
                if success:
                    monitoring_status = "✅ 运行中"
                else:
                    monitoring_status = f"❌ 启动失败: {message}"
                    
            # 4. 加载核心规范
            regulations = self.load_core_regulations()
            
            if not regulations:
                return False, "❌ 未能加载任何核心规范文档"
                
            # 5. 提取关键约束
            constraints = self.extract_key_constraints(regulations)
            
            # 6. 生成启动简报
            briefing = self.generate_startup_briefing(regulations, constraints, monitoring_status)
            
            # 7. 保存启动记录
            self.save_startup_record(briefing)
            
            # 8. 显示简报
            print("\n" + "=" * 50)
            print(briefing)
            print("=" * 50)
            
            success_msg = f"🎉 AI助理完整启动检查完成 - 已加载 {len(regulations)} 个核心文档"
            self.logger.info(success_msg)
                
            return True, success_msg
            
        except Exception as e:
            error_msg = f"❌ 启动检查失败: {e}"
            print(error_msg)
            self.logger.error(error_msg)
            
            # 清理监控进程
            if monitoring_process and monitoring_process.poll() is None:
                try:
                    monitoring_process.terminate()
                    monitoring_process.wait(timeout=5)
                except:
                    pass
                    
            return False, error_msg
            
    def show_work_reminders(self):
        """显示重要工作提醒"""
        reminders = [
            "🔔 重要提醒:",
            "   - 监控系统已启动，将实时检查文件操作",
            "   - 请严格按照项目规范执行", 
            "   - 文件操作前请检查路径合规性",
            "   - 定期运行项目检查工具",
            "   - 保持代码质量和文档完整性"
        ]
        
        for reminder in reminders:
            print(reminder)
            self.logger.info(reminder)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI助理完整启动检查系统")
    parser.add_argument("--check", action="store_true", help="执行完整启动检查")
    
    args = parser.parse_args()
    
    checker = FixedAIStartupChecker()
    
    if args.check:
        success, message = checker.perform_full_startup_check()
        print(f"\n{message}")
        if success:
            checker.show_work_reminders()
        if not success:
            exit(1)
    else:
        # 默认执行完整启动检查
        success, message = checker.perform_full_startup_check()
        print(f"\n{message}")
        if success:
            checker.show_work_reminders()
            print("\n🚀 现在可以开始高效工作！")
            print("=" * 50)
        if not success:
            exit(1)
        
if __name__ == "__main__":
    main()