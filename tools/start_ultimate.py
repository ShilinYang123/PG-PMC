#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助理终极启动系统
完整监控功能 + 防卡顿机制
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
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class UltimateAIStartupChecker:
    """终极AI助理启动检查器"""
    
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
        
        # 监控进程
        self.monitoring_process = None
        self.monitoring_status = "未启动"
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        self.logs_dir.mkdir(exist_ok=True)
        
        log_file = self.logs_dir / f"ultimate_startup_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def print_progress(self, message: str, step: int = 0, total: int = 0):
        """显示进度信息"""
        if total > 0:
            progress = f"[{step}/{total}] "
        else:
            progress = ""
        
        print(f"🔄 {progress}{message}")
        self.logger.info(f"{progress}{message}")
        
    def safe_import_test(self, module_name: str, timeout: int = 5) -> Tuple[bool, str]:
        """安全测试模块导入"""
        def import_worker(result_container):
            try:
                if module_name == "watchdog":
                    import watchdog
                    from watchdog.observers import Observer
                    from watchdog.events import FileSystemEventHandler
                    result_container['success'] = True
                    result_container['message'] = f"watchdog {watchdog.__version__}"
                else:
                    __import__(module_name)
                    result_container['success'] = True
                    result_container['message'] = f"{module_name} 导入成功"
            except Exception as e:
                result_container['success'] = False
                result_container['message'] = str(e)
        
        result_container = {'success': False, 'message': ''}
        
        thread = threading.Thread(target=import_worker, args=(result_container,))
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            return False, f"{module_name} 导入超时"
        
        return result_container['success'], result_container['message']
        
    def check_prerequisites(self) -> Tuple[bool, str]:
        """检查前置条件"""
        self.print_progress("检查前置条件", 1, 7)
        
        # 检查项目结构
        required_dirs = ["docs", "tools", "logs"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                return False, f"必需目录不存在: {dir_path}"
                
        # 检查核心脚本
        compliance_monitor = self.tools_dir / "compliance_monitor.py"
        if not compliance_monitor.exists():
            return False, f"监控脚本不存在: {compliance_monitor}"
            
        return True, "前置条件检查通过"
        
    def test_dependencies(self) -> Tuple[bool, str]:
        """测试依赖库"""
        self.print_progress("测试依赖库", 2, 7)
        
        # 测试基础库
        basic_modules = ['json', 'yaml', 'logging', 'subprocess']
        for module in basic_modules:
            success, message = self.safe_import_test(module, timeout=3)
            if not success:
                return False, f"基础库 {module} 不可用: {message}"
                
        # 测试watchdog库
        success, message = self.safe_import_test('watchdog', timeout=10)
        if not success:
            self.logger.warning(f"watchdog库不可用: {message}")
            return False, f"watchdog库不可用: {message}"
            
        return True, "依赖库测试通过"
        
    def load_core_regulations_safe(self) -> Tuple[Dict[str, str], str]:
        """安全加载核心规范"""
        self.print_progress("加载核心规范", 3, 7)
        
        regulations = {}
        loaded_count = 0
        
        for doc_name, doc_path in self.core_docs.items():
            if doc_path.exists():
                try:
                    # 设置读取超时
                    def read_file():
                        if doc_path.suffix.lower() in ['.yaml', '.yml']:
                            with open(doc_path, 'r', encoding='utf-8') as f:
                                content = yaml.safe_load(f)
                                return json.dumps(content, ensure_ascii=False, indent=2)
                        else:
                            with open(doc_path, 'r', encoding='utf-8') as f:
                                return f.read()
                    
                    # 使用线程读取文件，避免阻塞
                    result_container = {'content': None, 'error': None}
                    
                    def file_reader():
                        try:
                            result_container['content'] = read_file()
                        except Exception as e:
                            result_container['error'] = str(e)
                    
                    thread = threading.Thread(target=file_reader)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=5)  # 5秒超时
                    
                    if thread.is_alive():
                        self.logger.warning(f"文档读取超时: {doc_name}")
                        continue
                        
                    if result_container['error']:
                        self.logger.error(f"文档读取失败 {doc_name}: {result_container['error']}")
                        continue
                        
                    regulations[doc_name] = result_container['content']
                    loaded_count += 1
                    print(f"   ✅ {doc_name}: 已加载")
                    
                except Exception as e:
                    self.logger.error(f"加载文档异常 {doc_name}: {e}")
                    
            else:
                self.logger.warning(f"文档不存在: {doc_name} - {doc_path}")
                
        status = f"已加载 {loaded_count}/{len(self.core_docs)} 个文档"
        return regulations, status
        
    def start_monitoring_async(self) -> Tuple[bool, str]:
        """异步启动监控系统"""
        self.print_progress("启动监控系统", 4, 7)
        
        compliance_monitor = self.tools_dir / "compliance_monitor.py"
        
        try:
            # 启动监控进程
            self.monitoring_process = subprocess.Popen(
                [sys.executable, str(compliance_monitor)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # 等待3秒检查启动状态
            time.sleep(3)
            
            if self.monitoring_process.poll() is None:
                self.monitoring_status = "✅ 运行中"
                print(f"   ✅ 监控进程启动成功 (PID: {self.monitoring_process.pid})")
                return True, "监控系统启动成功"
            else:
                stdout, stderr = self.monitoring_process.communicate()
                error_msg = stderr or stdout or "未知错误"
                self.monitoring_status = f"❌ 启动失败: {error_msg[:100]}"
                return False, f"监控进程启动失败: {error_msg}"
                
        except Exception as e:
            self.monitoring_status = f"❌ 异常: {str(e)[:100]}"
            return False, f"启动监控系统异常: {e}"
            
    def extract_key_constraints(self, regulations: Dict[str, str]) -> List[str]:
        """提取关键约束条件"""
        self.print_progress("提取约束条件", 5, 7)
        
        constraints = [
            "🚫 严禁在项目根目录创建任何临时文件或代码文件",
            "✅ 每次操作前必须执行路径合规性检查",
            "🔒 严格保护核心文档，禁止未经授权的修改",
            "📝 严格遵守UTF-8编码规范",
            "📁 严格遵守标准目录结构规范"
        ]
        
        # 根据加载的文档添加特定约束
        if "PMC工作流程详解" in regulations:
            constraints.append("🔄 必须遵循标准工作准备流程")
            constraints.append("🧹 严格遵守文件清理管理规定")
            
        if "项目配置" in regulations:
            constraints.append("⚙️ 严格遵守项目配置中的技术规范")
            
        if "开发任务书" in regulations:
            constraints.append("🎯 严格按照开发任务书的目标和范围执行")
            
        if "技术方案" in regulations:
            constraints.append("🏗️ 严格遵循技术方案的架构设计")
            
        return constraints
        
    def generate_startup_briefing(self, regulations: Dict[str, str], constraints: List[str], load_status: str) -> str:
        """生成启动简报"""
        self.print_progress("生成启动简报", 6, 7)
        
        briefing = f"""
# AI助理终极启动简报

**启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**项目根目录**: {self.project_root}
**启动模式**: 终极模式（完整功能 + 防卡顿）
**监控状态**: {self.monitoring_status}
**文档加载**: {load_status}

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

## 🚀 系统状态
- 监控系统: {self.monitoring_status}
- 文档系统: {load_status}
- 启动脚本: 终极版本 v1.0

## 🔧 故障排除
如果遇到问题，可以使用以下工具：
- `python tools/diagnose_startup.py` - 系统诊断
- `python tools/start_simple.py` - 简化启动
- `python tools/start_fixed.py` - 修复版启动

现在您已经完成终极启动检查，可以开始高效工作！
"""
        
        return briefing
        
    def save_startup_record(self, briefing: str):
        """保存启动记录"""
        self.print_progress("保存启动记录", 7, 7)
        
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
        # 保存启动简报
        briefing_file = self.logs_dir / f"ultimate_startup_briefing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(briefing_file, 'w', encoding='utf-8') as f:
            f.write(briefing)
            
        print(f"💾 启动简报已保存: {briefing_file}")
        self.logger.info(f"启动简报已保存: {briefing_file}")
        
    def perform_ultimate_startup(self) -> Tuple[bool, str]:
        """执行终极启动检查"""
        print("🚀 AI助理终极启动检查开始")
        print("=" * 60)
        
        try:
            # 1. 检查前置条件
            success, message = self.check_prerequisites()
            if not success:
                return False, message
                
            # 2. 测试依赖库
            success, message = self.test_dependencies()
            monitoring_available = success
            
            # 3. 加载核心规范
            regulations, load_status = self.load_core_regulations_safe()
            
            # 4. 启动监控系统（如果可用）
            if monitoring_available:
                success, message = self.start_monitoring_async()
                if not success:
                    self.logger.warning(f"监控启动失败，继续其他流程: {message}")
            else:
                self.monitoring_status = "❌ 依赖不可用"
                
            # 5. 提取约束条件
            constraints = self.extract_key_constraints(regulations)
            
            # 6. 生成启动简报
            briefing = self.generate_startup_briefing(regulations, constraints, load_status)
            
            # 7. 保存启动记录
            self.save_startup_record(briefing)
            
            # 8. 显示简报
            print("\n" + "=" * 60)
            print(briefing)
            print("=" * 60)
            
            success_msg = f"🎉 AI助理终极启动完成 - {load_status}"
            self.logger.info(success_msg)
                
            return True, success_msg
            
        except Exception as e:
            error_msg = f"❌ 终极启动失败: {e}"
            print(error_msg)
            self.logger.error(error_msg)
            
            # 清理监控进程
            self.cleanup_monitoring()
                    
            return False, error_msg
            
    def cleanup_monitoring(self):
        """清理监控进程"""
        if self.monitoring_process and self.monitoring_process.poll() is None:
            try:
                self.monitoring_process.terminate()
                self.monitoring_process.wait(timeout=5)
                print("🧹 监控进程已清理")
            except:
                try:
                    self.monitoring_process.kill()
                except:
                    pass
                    
    def show_work_reminders(self):
        """显示重要工作提醒"""
        reminders = [
            "🔔 重要提醒:",
            f"   - 监控系统状态: {self.monitoring_status}",
            "   - 请严格按照项目规范执行", 
            "   - 文件操作前请检查路径合规性",
            "   - 定期运行项目检查工具",
            "   - 保持代码质量和文档完整性",
            "   - 遇到问题可使用诊断工具"
        ]
        
        for reminder in reminders:
            print(reminder)
            self.logger.info(reminder)

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n🛑 收到中断信号，正在清理...")
    sys.exit(0)

def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    import argparse
    
    parser = argparse.ArgumentParser(description="AI助理终极启动检查系统")
    parser.add_argument("--check", action="store_true", help="执行终极启动检查")
    parser.add_argument("--timeout", type=int, default=30, help="总体超时时间（秒）")
    
    args = parser.parse_args()
    
    checker = UltimateAIStartupChecker()
    
    try:
        if args.check:
            success, message = checker.perform_ultimate_startup()
            print(f"\n{message}")
            if success:
                checker.show_work_reminders()
            if not success:
                exit(1)
        else:
            # 默认执行终极启动检查
            success, message = checker.perform_ultimate_startup()
            print(f"\n{message}")
            if success:
                checker.show_work_reminders()
                print("\n🚀 现在可以开始高效工作！")
                print("=" * 60)
            if not success:
                exit(1)
                
    except KeyboardInterrupt:
        print("\n🛑 用户中断启动过程")
        checker.cleanup_monitoring()
        exit(1)
    except Exception as e:
        print(f"\n❌ 启动过程异常: {e}")
        checker.cleanup_monitoring()
        exit(1)
        
if __name__ == "__main__":
    main()