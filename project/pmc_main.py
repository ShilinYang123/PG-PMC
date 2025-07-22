#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC智能追踪系统 - PMC管理专用启动程序
专注于生产管理控制，不包含CAD设计功能

作者: 3AI电器实业有限公司
版本: 1.0.0
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.utils.logger import setup_logging, get_logger
from src.core.project_manager import ProjectManager
from src.ai.project_command_processor import ProjectCommandProcessor


class PMCManagementSystem:
    """PMC生产管理系统
    
    专注于生产管理控制功能：
    - 项目管理
    - 生产计划
    - 进度跟踪
    - 质量控制
    - 资源调度
    """
    
    def __init__(self, dev_mode: bool = False):
        """初始化PMC管理系统
        
        Args:
            dev_mode: 是否为开发模式
        """
        self.dev_mode = dev_mode
        setup_logging(level="INFO")
        self.logger = get_logger("pmc_management_system")
        
        # 核心组件
        self.project_manager = ProjectManager()
        self.command_processor = ProjectCommandProcessor()
        
        self.logger.info("PMC生产管理系统初始化完成")
    
    def start_interactive_mode(self):
        """启动交互模式"""
        self.logger.info("🚀 启动PMC生产管理系统 - 交互模式")
        print("\n" + "="*60)
        print("    PG-PMC 智能生产管理控制系统")
        print("    专注于生产管理，不包含CAD设计功能")
        print("="*60)
        print("\n可用命令:")
        print("  - 创建项目: 创建新项目：[项目名称]")
        print("  - 切换项目: 切换到项目：[项目名称]")
        print("  - 列出项目: 列出所有项目")
        print("  - 项目状态: 查看当前项目状态")
        print("  - 生产计划: 制定生产计划")
        print("  - 进度跟踪: 查看生产进度")
        print("  - 质量控制: 质量检查记录")
        print("  - 帮助: help 或 ?")
        print("  - 退出: exit 或 quit")
        print()
        
        try:
            while True:
                try:
                    # 显示当前项目信息
                    current_project = self.project_manager.get_current_project()
                    if current_project:
                        prompt = f"PMC[{current_project['name']}]> "
                    else:
                        prompt = "PMC> "
                    
                    user_input = input(prompt).strip()
                    
                    if not user_input:
                        continue
                    
                    # 处理退出命令
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        print("\n👋 感谢使用PMC生产管理系统！")
                        break
                    
                    # 处理帮助命令
                    if user_input.lower() in ['help', '?', '帮助']:
                        self._show_help()
                        continue
                    
                    # 处理用户输入
                    result = self.command_processor.process_input(user_input)
                    
                    if result['success']:
                        if result['message']:
                            print(f"✅ {result['message']}")
                        
                        # 显示项目相关信息
                        if result['input_type'] == 'project_management':
                            self._display_project_info()
                    else:
                        print(f"❌ {result['message']}")
                        
                except KeyboardInterrupt:
                    print("\n\n👋 用户中断，正在退出...")
                    break
                except Exception as e:
                    self.logger.error(f"处理用户输入时出错: {e}")
                    print(f"❌ 处理命令时出错: {e}")
                    
        except Exception as e:
            self.logger.error(f"交互模式运行出错: {e}")
            print(f"❌ 系统运行出错: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n📖 PMC生产管理系统帮助")
        print("-" * 40)
        print("项目管理命令:")
        print("  创建新项目：智能咖啡机开发")
        print("  切换到项目：智能咖啡机开发")
        print("  列出所有项目")
        print("  查看当前项目状态")
        print("  更新项目信息：[项目名]，状态为[状态]")
        print()
        print("生产管理命令:")
        print("  制定生产计划")
        print("  查看生产进度")
        print("  添加质量检查记录")
        print("  查看设备状态")
        print("  生成生产报告")
        print()
        print("系统命令:")
        print("  help, ? - 显示帮助")
        print("  exit, quit - 退出系统")
        print()
    
    def _display_project_info(self):
        """显示当前项目信息"""
        current_project = self.project_manager.get_current_project()
        if current_project:
            print(f"\n📋 当前项目: {current_project['name']} (ID: {current_project['id']})")
            print(f"   状态: {current_project.get('status', '未知')}")
            print(f"   描述: {current_project.get('description', '无描述')}")
        else:
            print("\n📋 当前没有选择项目")
    
    def run_command(self, command: str) -> bool:
        """运行单个命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            bool: 命令执行是否成功
        """
        try:
            result = self.command_processor.process_input(command)
            
            if result['success']:
                if result['message']:
                    print(f"✅ {result['message']}")
                return True
            else:
                print(f"❌ {result['message']}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            print(f"❌ 执行命令失败: {e}")
            return False


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="PG-PMC智能生产管理控制系统"
    )
    parser.add_argument("--dev", action="store_true", help="开发模式运行")
    parser.add_argument(
        "--command", type=str, help="执行单个命令后退出"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    try:
        # 创建PMC管理系统实例
        pmc_system = PMCManagementSystem(dev_mode=args.dev)
        
        if args.command:
            # 执行单个命令模式
            success = pmc_system.run_command(args.command)
            return 0 if success else 1
        else:
            # 交互模式
            pmc_system.start_interactive_mode()
            return 0
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在退出...")
        return 0
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        if args.dev:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())