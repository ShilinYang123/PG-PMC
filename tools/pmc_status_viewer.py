#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统状态查看器
用于解析和展示BD300项目PMC控制系统状态信息
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

class PMCStatusViewer:
    """PMC系统状态查看器"""
    
    def __init__(self, status_file_path: str):
        self.status_file_path = status_file_path
        self.status_data = None
        
    def load_status(self) -> bool:
        """加载状态文件"""
        try:
            if not os.path.exists(self.status_file_path):
                print(f"[异常] 状态文件不存在: {self.status_file_path}")
                return False
                
            with open(self.status_file_path, 'r', encoding='utf-8') as f:
                self.status_data = json.load(f)
            return True
        except Exception as e:
            print(f"[异常] 加载状态文件失败: {e}")
            return False
    
    def display_system_overview(self):
        """显示系统概览"""
        if not self.status_data:
            return
            
        system = self.status_data.get('system_status', {})
        print("\n" + "="*60)
        print("[工厂] BD300项目PMC控制系统 - 状态概览")
        print("="*60)
        print(f"[清单] 项目ID: {system.get('project_id', 'N/A')}")
        print(f"[系统]  系统名称: {system.get('system_name', 'N/A')}")
        print(f"[运行] 运行状态: {system.get('status', 'N/A')}")
        print(f"[时间] 启动时间: {system.get('startup_time', 'N/A')}")
        print(f"[运行] 最后更新: {system.get('last_update', 'N/A')}")
        print(f"[版本] 版本: {system.get('version', 'N/A')}")
    
    def display_module_status(self):
        """显示模块状态"""
        if not self.status_data:
            return
            
        modules = self.status_data.get('module_status', {})
        print("\n" + "-"*60)
        print("[模块] 模块状态检查")
        print("-"*60)
        
        status_icons = {
            '激活': '[正常]',
            '正常': '[正常]', 
            '配置完成': '[正常]',
            '异常': '[异常]',
            '停止': '⏸️'
        }
        
        for module_name, module_info in modules.items():
            status = module_info.get('status', 'N/A')
            health = module_info.get('health', 'N/A')
            icon = status_icons.get(status, '[符号]')
            health_icon = status_icons.get(health, '[符号]')
            
            module_display_names = {
                'data_monitoring': '[数据] 数据监控',
                'alert_system': '[预警] 预警系统', 
                'reporting_system': '[清单] 报告系统',
                'data_sync': '[运行] 数据同步',
                'dashboard': '[仪表板] 仪表板'
            }
            
            display_name = module_display_names.get(module_name, module_name)
            print(f"{display_name}: {icon} {status} | 健康状态: {health_icon} {health}")
            
            if module_name == 'data_monitoring':
                print(f"   [数据源] 数据源: {module_info.get('data_sources_count', 0)}个")
                print(f"   [监控]  活跃监控: {module_info.get('active_monitors', 0)}个")
            elif module_name == 'alert_system':
                print(f"   [规则] 活跃规则: {module_info.get('active_rules', 0)}个")
                print(f"   [待处理] 待处理预警: {module_info.get('pending_alerts', 0)}个")
    
    def display_monitoring_points(self):
        """显示监控点状态"""
        if not self.status_data:
            return
            
        monitoring = self.status_data.get('active_monitoring_points', {})
        print("\n" + "-"*60)
        print("[监控]  活跃监控点")
        print("-"*60)
        
        control_names = {
            'material_control': '[版本] 物料控制',
            'production_control': '[工厂] 生产控制',
            'quality_control': '[检查] 质量控制', 
            'assembly_control': '[模块] 装配控制'
        }
        
        for control_type, points in monitoring.items():
            display_name = control_names.get(control_type, control_type)
            print(f"\n{display_name}:")
            for point_name, status in points.items():
                icon = '[正常]' if status == '激活' else '[异常]'
                print(f"  {icon} {point_name}: {status}")
    
    def display_team_status(self):
        """显示团队状态"""
        if not self.status_data:
            return
            
        team = self.status_data.get('team_coordination', {})
        members = team.get('team_members', {})
        
        print("\n" + "-"*60)
        print("[团队] 团队状态")
        print("-"*60)
        
        role_names = {
            'pmc_coordinator': '[重点] PMC协调员',
            'production_planner': '[清单] 生产计划员',
            'purchase_coordinator': '[符号] 采购跟催员',
            'quality_inspector': '[检查] 质量检验员'
        }
        
        for member_key, member_info in members.items():
            display_name = role_names.get(member_key, member_info.get('role', member_key))
            status = member_info.get('status', 'N/A')
            icon = '[在线]' if status == '在线' else '[离线]'
            print(f"{display_name}: {icon} {status}")
            print(f"   [时间] 最后活动: {member_info.get('last_activity', 'N/A')}")
    
    def display_data_files_status(self):
        """显示数据文件状态"""
        if not self.status_data:
            return
            
        files = self.status_data.get('data_files_status', {})
        print("\n" + "-"*60)
        print("[文件] 数据文件状态")
        print("-"*60)
        
        for filename, file_info in files.items():
            status = file_info.get('status', 'N/A')
            monitoring = file_info.get('monitoring', 'N/A')
            
            status_icon = '[正常]' if status == '已同步' else '[异常]' if status == '未同步' else '[清单]'
            monitor_icon = '[监控]' if monitoring == '激活' else '[休眠]'
            
            print(f"{status_icon} {filename}")
            print(f"   [位置] 位置: {file_info.get('location', 'N/A')}")
            print(f"   [日常] 修改时间: {file_info.get('last_modified', 'N/A')}")
            print(f"   {monitor_icon} 监控: {monitoring}")
            print()
    
    def display_next_tasks(self):
        """显示下一步任务"""
        if not self.status_data:
            return
            
        tasks = self.status_data.get('next_scheduled_tasks', {})
        print("\n" + "-"*60)
        print("[日常] 计划任务")
        print("-"*60)
        
        # 即时任务
        immediate = tasks.get('immediate_tasks', [])
        if immediate:
            print("\n[预警] 即时任务:")
            for task in immediate:
                status_icon = '[待处理]' if task.get('status') == '待执行' else '[正常]'
                print(f"  {status_icon} {task.get('task', 'N/A')}")
                print(f"     [时间] 计划时间: {task.get('scheduled_time', 'N/A')}")
                print(f"     [成员] 负责人: {task.get('responsible', 'N/A')}")
        
        # 日常任务
        daily = tasks.get('daily_tasks', [])
        if daily:
            print("\n[日常] 日常任务:")
            for task in daily:
                print(f"  [正常] {task.get('task', 'N/A')}")
                print(f"     [时间] 时间: {task.get('scheduled_time', 'N/A')}")
    
    def display_system_health(self):
        """显示系统健康状态"""
        if not self.status_data:
            return
            
        health = self.status_data.get('system_health', {})
        print("\n" + "-"*60)
        print("[健康] 系统健康状态")
        print("-"*60)
        
        overall = health.get('overall_status', 'N/A')
        icon = '[正常]' if overall == '健康' else '[异常]'
        print(f"[整体] 整体状态: {icon} {overall}")
        print(f"[CPU] CPU使用率: {health.get('cpu_usage', 'N/A')}")
        print(f"[内存] 内存使用率: {health.get('memory_usage', 'N/A')}")
        print(f"[磁盘] 磁盘空间: {health.get('disk_space', 'N/A')}")
        print(f"[网络] 网络连接: {health.get('network_connectivity', 'N/A')}")
        print(f"[时间] 最后检查: {health.get('last_health_check', 'N/A')}")
    
    def display_startup_checklist(self):
        """显示启动检查清单"""
        print("\n" + "="*60)
        print("[启动] 早上8:00 - 系统启动检查清单")
        print("="*60)
        
        if not self.status_data:
            print("[异常] 无法加载系统状态数据")
            return
            
        # 检查所有模块状态
        modules = self.status_data.get('module_status', {})
        all_normal = True
        
        print("\n[正常] 已完成: 打开PMC系统状态文件")
        
        print("\n[检查] 模块状态检查:")
        for module_name, module_info in modules.items():
            health = module_info.get('health', 'N/A')
            if health != '正常':
                all_normal = False
                print(f"  [异常] {module_name}: {health}")
            else:
                print(f"  [正常] {module_name}: {health}")
        
        if all_normal:
            print("\n[正常] 已确认: 所有模块状态正常")
        else:
            print("\n[异常] 注意: 发现异常模块，需要处理")
        
        # 检查预警信息
        alert_system = modules.get('alert_system', {})
        pending_alerts = alert_system.get('pending_alerts', 0)
        
        if pending_alerts == 0:
            print("[正常] 已确认: 无待处理预警信息")
        else:
            print(f"[注意]  注意: 有 {pending_alerts} 个待处理预警")
        
        print("\n[清单] 下一步: 制定今日重点关注计划")
        
        # 显示今日重点任务
        tasks = self.status_data.get('next_scheduled_tasks', {})
        immediate = tasks.get('immediate_tasks', [])
        daily = tasks.get('daily_tasks', [])
        
        print("\n[重点] 今日重点关注:")
        for task in immediate:
            if task.get('status') == '待执行':
                print(f"  [紧急] {task.get('task', 'N/A')} - {task.get('scheduled_time', 'N/A')}")
        
        for task in daily:
            print(f"  [日常] {task.get('task', 'N/A')} - {task.get('scheduled_time', 'N/A')}")
    
    def run_full_check(self):
        """运行完整检查"""
        if not self.load_status():
            return
            
        self.display_system_overview()
        self.display_module_status()
        self.display_monitoring_points()
        self.display_team_status()
        self.display_data_files_status()
        self.display_next_tasks()
        self.display_system_health()
        self.display_startup_checklist()
    
    def run_startup_check(self):
        """运行启动检查（简化版）"""
        if not self.load_status():
            return
            
        self.display_system_overview()
        self.display_module_status()
        self.display_startup_checklist()

def main():
    """主函数"""
    import sys
    
    # 默认状态文件路径
    default_path = r"s:\PG-PMC\AI调度表\项目BD300\实时数据更新\PMC系统状态.json"
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("PMC系统状态查看器")
            print("用法:")
            print("  python pmc_status_viewer.py [选项] [文件路径]")
            print("")
            print("选项:")
            print("  --startup, -s    运行启动检查（简化版）")
            print("  --full, -f       运行完整检查（默认）")
            print("  --help, -h       显示帮助信息")
            print("")
            print("示例:")
            print("  python pmc_status_viewer.py --startup")
            print("  python pmc_status_viewer.py --full /path/to/status.json")
            return
        
        status_file = sys.argv[-1] if not sys.argv[-1].startswith('--') else default_path
        startup_mode = '--startup' in sys.argv or '-s' in sys.argv
    else:
        status_file = default_path
        startup_mode = False
    
    # 创建查看器实例
    viewer = PMCStatusViewer(status_file)
    
    # 运行检查
    if startup_mode:
        print("[启动检查] 运行启动检查模式...")
        viewer.run_startup_check()
    else:
        print("[完整检查] 运行完整检查模式...")
        viewer.run_full_check()
    
    print("\n" + "="*60)
    print("[正常] 检查完成")
    print("="*60)

if __name__ == '__main__':
    main()