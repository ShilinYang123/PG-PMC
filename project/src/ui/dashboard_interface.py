#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC智能追踪系统 - 仪表板界面
"""

from typing import Optional
from src.utils.logger import get_logger


class DashboardInterface:
    """仪表板界面类
    
    提供系统的主要用户界面
    """
    
    def __init__(self, scheduler=None, language_processor=None, iot_manager=None, project_api=None, dev_mode=False):
        """初始化仪表板界面
        
        Args:
            scheduler: 智能调度器
            language_processor: 语言处理器
            iot_manager: IoT设备管理器
            project_api: 项目API
            dev_mode: 开发模式
        """
        self.scheduler = scheduler
        self.language_processor = language_processor
        self.iot_manager = iot_manager
        self.project_api = project_api
        self.dev_mode = dev_mode
        self.logger = get_logger(self.__class__.__name__)
        
        self.is_running = False
        
    def start(self):
        """启动仪表板界面"""
        try:
            self.logger.info("启动仪表板界面")
            self.is_running = True
            
            # 显示欢迎信息
            print("\n" + "="*50)
            print("    PG-PMC智能追踪系统已启动")
            print("="*50)
            print("系统组件状态:")
            print(f"  智能调度器: {'✓' if self.scheduler else '✗'}")
            print(f"  语言处理器: {'✓' if self.language_processor else '✗'}")
            print(f"  IoT设备管理器: {'✓' if self.iot_manager else '✗'}")
            print(f"  项目管理API: {'✓' if self.project_api else '✗'}")
            print(f"  开发模式: {'是' if self.dev_mode else '否'}")
            print("="*50)
            
            # 主循环
            self._main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("用户中断操作")
        except Exception as e:
            self.logger.error(f"仪表板界面错误: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止仪表板界面"""
        try:
            self.is_running = False
            print("\n仪表板界面已关闭")
            self.logger.info("仪表板界面已停止")
        except Exception as e:
            self.logger.error(f"停止仪表板界面失败: {e}")
    
    def _main_loop(self):
        """主循环"""
        while self.is_running:
            try:
                print("\n可用操作:")
                print("1. 项目管理")
                print("2. 智能调度")
                print("3. 系统状态")
                print("4. 退出系统")
                
                choice = input("\n请选择操作 (1-4): ").strip()
                
                if choice == "1":
                    self._handle_project_management()
                elif choice == "2":
                    self._handle_intelligent_scheduling()
                elif choice == "3":
                    self._show_system_status()
                elif choice == "4":
                    self.is_running = False
                    print("正在退出系统...")
                else:
                    print("无效选择，请重试")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                print(f"操作错误: {e}")
    
    def _handle_project_management(self):
        """处理项目管理"""
        if not self.project_api:
            print("项目管理API未初始化")
            return
            
        print("\n项目管理功能:")
        print("1. 创建项目")
        print("2. 列出项目")
        print("3. 切换项目")
        print("4. 返回主菜单")
        
        choice = input("请选择操作 (1-4): ").strip()
        
        try:
            if choice == "1":
                name = input("项目名称: ").strip()
                description = input("项目描述: ").strip()
                project_type = input("项目类型 (默认: 小家电): ").strip() or "小家电"
                
                result = self.project_api.create_project(name, description, project_type)
                if result["success"]:
                    print(f"✓ 项目创建成功: {result['project_id']}")
                else:
                    print(f"✗ 项目创建失败: {result['error']}")
                    
            elif choice == "2":
                result = self.project_api.list_projects()
                if result["success"]:
                    projects = result["projects"]
                    if projects:
                        print("\n项目列表:")
                        for project in projects:
                            print(f"  {project['id']}: {project['name']} ({project['status']})")
                    else:
                        print("暂无项目")
                else:
                    print(f"✗ 获取项目列表失败: {result['error']}")
                    
            elif choice == "3":
                project_id = input("项目ID: ").strip()
                result = self.project_api.switch_project(project_id)
                if result["success"]:
                    print(f"✓ 已切换到项目: {project_id}")
                else:
                    print(f"✗ 切换项目失败: {result['error']}")
                    
        except Exception as e:
            self.logger.error(f"项目管理操作失败: {e}")
            print(f"操作失败: {e}")
    
    def _handle_intelligent_scheduling(self):
        """处理智能调度"""
        if not self.scheduler:
            print("智能调度器未初始化")
            return
            
        print("\n智能调度功能:")
        print("请输入自然语言指令 (输入 'quit' 返回主菜单):")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    break
                    
                if not user_input:
                    continue
                    
                # 处理用户输入
                result = self.scheduler.process_user_input(user_input)
                
                if result["success"]:
                    print(f"\n处理结果: {result['message']}")
                    if "suggestions" in result:
                        print(f"建议: {result['suggestions']}")
                else:
                    print(f"\n处理失败: {result['error']}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"智能调度处理失败: {e}")
                print(f"处理失败: {e}")
    
    def _show_system_status(self):
        """显示系统状态"""
        print("\n系统状态:")
        print("="*30)
        
        # 基本状态
        print(f"仪表板状态: {'运行中' if self.is_running else '已停止'}")
        print(f"开发模式: {'是' if self.dev_mode else '否'}")
        
        # 组件状态
        print("\n组件状态:")
        print(f"  智能调度器: {'✓ 已加载' if self.scheduler else '✗ 未加载'}")
        print(f"  语言处理器: {'✓ 已加载' if self.language_processor else '✗ 未加载'}")
        print(f"  IoT设备管理器: {'✓ 已加载' if self.iot_manager else '✗ 未加载'}")
        print(f"  项目管理API: {'✓ 已加载' if self.project_api else '✗ 未加载'}")
        
        # 项目信息
        if self.project_api:
            try:
                current_project = self.project_api.get_current_project()
                if current_project["success"]:
                    project = current_project["project"]
                    print(f"\n当前项目: {project['name']} (ID: {project['id']})")
                else:
                    print("\n当前项目: 未选择")
            except Exception as e:
                print(f"\n当前项目: 获取失败 ({e})")
        
        print("="*30)