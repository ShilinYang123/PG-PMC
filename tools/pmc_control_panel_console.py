#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC控制面板 - 控制台版本
适用于无图形界面的服务器环境
"""

import sys
import os
import subprocess
import time
import webbrowser
from datetime import datetime

class PMCControlPanelConsole:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print("="*60)
        print("PMC智能生产管理控制面板 - 控制台版本")
        print("BD300项目PMC控制系统")
        print("="*60)
        print(f"项目根目录: {self.project_root}")
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def log_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

    def run_command(self, command, description):
        self.log_message(f"开始{description}...")
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"错误输出: {result.stderr}")
            if result.returncode == 0:
                self.log_message(f"{description}完成。")
            else:
                self.log_message(f"{description}失败（代码: {result.returncode}）。")
            return result.returncode == 0
        except Exception as e:
            self.log_message(f"执行错误: {str(e)}")
            return False

    def show_menu(self):
        print("\n" + "="*50)
        print("PMC控制面板主菜单")
        print("="*50)
        print("🔍 系统状态")
        print("  1. 执行早上启动检查")
        print("  2. 查看详细状态")
        print()
        print("🎯 系统启动")
        print("  3. 启动PMC管理系统")
        print("  4. 启动PMC追踪系统")
        print()
        print("🔧 系统工具")
        print("  5. 执行结构检查")
        print("  6. 打开项目文档")
        print("  7. 快速操作手册")
        print()
        print("  0. 退出")
        print("="*50)

    def run_startup_check(self):
        cmd = ['python', os.path.join(self.project_root, 'tools', 'startup_check.py')]
        return self.run_command(cmd, "早上启动检查")

    def view_system_status(self):
        self.log_message("查看详细系统状态...")
        self.log_message("系统状态: 正常")
        self.log_message(f"Python版本: {sys.version}")
        self.log_message(f"工作目录: {os.getcwd()}")
        self.log_message(f"项目根目录: {self.project_root}")
        return True

    def launch_management_system(self):
        cmd = ['python', os.path.join(self.project_root, 'project', 'pmc_management_system.py')]
        return self.run_command(cmd, "PMC管理系统")

    def launch_tracking_system(self):
        cmd = ['python', os.path.join(self.project_root, 'project', 'pmc_tracking_system.py')]
        return self.run_command(cmd, "PMC追踪系统")

    def run_structure_check(self):
        cmd = ['python', os.path.join(self.project_root, 'tools', 'structure_check.py')]
        return self.run_command(cmd, "结构检查")

    def open_docs(self):
        docs_path = os.path.join(self.project_root, 'docs')
        if os.path.exists(docs_path):
            self.log_message(f"项目文档路径: {docs_path}")
            # 在控制台环境下，只显示路径
            print(f"请手动打开文档目录: {docs_path}")
        else:
            self.log_message("项目文档目录未找到。")
        return True

    def open_manual(self):
        manual_path = os.path.join(self.project_root, 'docs', '快速操作手册.md')
        if os.path.exists(manual_path):
            self.log_message(f"快速操作手册路径: {manual_path}")
            print(f"请手动打开手册文件: {manual_path}")
        else:
            self.log_message("快速操作手册未找到。")
        return True

    def safe_input(self, prompt):
        """安全的输入函数，处理EOF和其他异常"""
        try:
            if sys.stdin.isatty():  # 检查是否为交互式终端
                return input(prompt)
            else:
                # 非交互式环境，返回默认值或退出
                print(f"{prompt}[非交互式环境，自动选择退出]")
                return '0'
        except EOFError:
            print("\n检测到输入流结束，自动退出...")
            return '0'
        except KeyboardInterrupt:
            print("\n检测到Ctrl+C，正在退出...")
            return '0'
        except Exception as e:
            print(f"\n输入错误: {e}，自动退出...")
            return '0'

    def run(self):
        self.log_message("PMC控制面板控制台版本启动成功")
        
        # 检查是否为交互式环境
        if not sys.stdin.isatty():
            self.log_message("检测到非交互式环境，显示菜单后自动退出")
            self.show_menu()
            self.log_message("在交互式终端中运行以使用完整功能")
            return
        
        while True:
            try:
                self.show_menu()
                choice = self.safe_input("\n请选择操作 (0-7): ").strip()
                
                if choice == '0':
                    self.log_message("退出PMC控制面板")
                    break
                elif choice == '1':
                    self.run_startup_check()
                elif choice == '2':
                    self.view_system_status()
                elif choice == '3':
                    self.launch_management_system()
                elif choice == '4':
                    self.launch_tracking_system()
                elif choice == '5':
                    self.run_structure_check()
                elif choice == '6':
                    self.open_docs()
                elif choice == '7':
                    self.open_manual()
                else:
                    print("无效选择，请重新输入。")
                
                if choice != '0':
                    self.safe_input("\n按回车键继续...")
                    
            except KeyboardInterrupt:
                print("\n\n检测到Ctrl+C，正在退出...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                self.safe_input("按回车键继续...")

if __name__ == '__main__':
    print("=== PMC控制台版本启动调试 ===")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本路径: {__file__}")
    print("=== 开始初始化 ===")
    
    def safe_exit_input():
        """安全的退出输入"""
        try:
            if sys.stdin.isatty():
                input("按回车键退出...")
        except (EOFError, KeyboardInterrupt):
            pass
        except Exception:
            pass
    
    try:
        print("创建PMCControlPanelConsole实例...")
        console_panel = PMCControlPanelConsole()
        print("实例创建成功，开始运行...")
        console_panel.run()
        print("程序正常结束")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        safe_exit_input()
        sys.exit(1)