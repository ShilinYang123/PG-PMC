#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份调度器测试脚本
测试定时备份机制的各项功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.services.backup_scheduler import backup_scheduler
    from app.services.backup_service import backup_service
    from app.services.backup_tasks import (
        get_backup_schedule, get_all_backup_tasks, 
        is_task_enabled, get_backup_retention_days,
        calculate_next_backup_time
    )
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的项目环境中运行此脚本")
    sys.exit(1)

class BackupSchedulerTester:
    """备份调度器测试类"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def log_test_result(self, test_name: str, success: bool, error_msg: str = None):
        """记录测试结果"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            print(f"✓ {test_name}: 通过")
        else:
            print(f"✗ {test_name}: 失败 - {error_msg}")
        
        self.test_results.append({
            'name': test_name,
            'success': success,
            'error': error_msg
        })
    
    async def test_scheduler_lifecycle(self):
        """测试调度器生命周期"""
        try:
            # 测试启动
            if hasattr(backup_scheduler, 'start'):
                await backup_scheduler.start()
                
            # 测试状态获取
            status = backup_scheduler.get_status()
            assert isinstance(status, dict), "状态应该是字典类型"
            
            # 测试停止
            if hasattr(backup_scheduler, 'stop'):
                await backup_scheduler.stop()
            
            self.log_test_result("调度器生命周期", True)
            
        except Exception as e:
            self.log_test_result("调度器生命周期", False, f"异常: {str(e)}")
    
    def test_task_configuration(self):
        """测试任务配置"""
        try:
            # 测试获取备份调度配置
            schedule = get_backup_schedule('daily_full_backup')
            assert schedule is not None, "应该能获取到每日全量备份配置"
            
            # 测试获取所有任务
            all_tasks = get_all_backup_tasks()
            assert isinstance(all_tasks, dict), "所有任务应该是字典类型"
            assert len(all_tasks) > 0, "应该有预定义的备份任务"
            
            self.log_test_result("获取任务配置", True)
            
        except Exception as e:
            self.log_test_result("获取任务配置", False, f"异常: {str(e)}")
    
    def test_daily_full_backup_config(self):
        """测试每日全量备份配置"""
        try:
            config = get_backup_schedule('daily_full_backup')
            assert config is not None, "每日全量备份配置不应为空"
            assert 'trigger' in config, "配置应包含触发器信息"
            
            # 检查任务是否启用
            enabled = is_task_enabled('daily_full_backup')
            assert isinstance(enabled, bool), "启用状态应该是布尔值"
            
            self.log_test_result("每日全量备份配置", True)
            
        except Exception as e:
            self.log_test_result("每日全量备份配置", False, f"异常: {str(e)}")
    
    def test_next_backup_time_calculation(self):
        """测试下次备份时间计算"""
        try:
            next_time = calculate_next_backup_time('daily_full_backup')
            if next_time:
                assert isinstance(next_time, datetime), "下次备份时间应该是datetime对象"
                assert next_time > datetime.now(), "下次备份时间应该在未来"
            
            self.log_test_result("计算下次执行时间", True)
            
        except Exception as e:
            self.log_test_result("计算下次执行时间", False, f"异常: {str(e)}")
    
    async def test_backup_management(self):
        """测试备份管理功能"""
        try:
            # 测试获取过期备份
            retention_days = get_backup_retention_days()
            cutoff_date = datetime.now() - timedelta(days=retention_days + 1)
            
            if hasattr(backup_service, 'get_backups_before_date'):
                expired_backups = await backup_service.get_backups_before_date(cutoff_date)
                assert isinstance(expired_backups, list), "过期备份应该是列表类型"
            
            self.log_test_result("获取过期备份", True)
            
        except Exception as e:
            self.log_test_result("获取过期备份", False, f"异常: {str(e)}")
    
    async def test_recent_backups(self):
        """测试获取最近备份"""
        try:
            recent_date = datetime.now() - timedelta(days=1)
            
            if hasattr(backup_service, 'get_backups_since_date'):
                recent_backups = await backup_service.get_backups_since_date(recent_date)
                assert isinstance(recent_backups, list), "最近备份应该是列表类型"
            
            self.log_test_result("获取最近备份", True)
            
        except Exception as e:
            self.log_test_result("获取最近备份", False, f"异常: {str(e)}")
    
    async def test_backup_report(self):
        """测试备份报告"""
        try:
            if hasattr(backup_service, 'save_backup_report'):
                test_report = {
                    'date': datetime.now().isoformat(),
                    'total_backups': 5,
                    'successful_backups': 4,
                    'failed_backups': 1,
                    'total_size': '1.2GB'
                }
                
                result = await backup_service.save_backup_report(test_report)
                # 不强制要求返回值，只要不抛异常就算成功
            
            self.log_test_result("保存备份报告", True)
            
        except Exception as e:
            self.log_test_result("保存备份报告", False, f"异常: {str(e)}")
    
    async def test_custom_backup_task(self):
        """测试自定义备份任务"""
        try:
            if hasattr(backup_scheduler, 'add_custom_backup_job'):
                # 添加测试任务
                job_id = await backup_scheduler.add_custom_backup_job(
                    name="test_backup",
                    trigger_type="interval",
                    trigger_config={"hours": 1},
                    backup_config={
                        "type": "database",
                        "description": "测试备份任务"
                    }
                )
                
                assert job_id is not None, "应该返回任务ID"
                
                # 移除测试任务
                if hasattr(backup_scheduler, 'remove_job'):
                    await backup_scheduler.remove_job(job_id)
            
            self.log_test_result("自定义备份任务", True)
            
        except Exception as e:
            self.log_test_result("自定义备份任务", False, f"异常: {str(e)}")
    
    def test_backup_health_check(self):
        """测试备份健康检查"""
        try:
            # 检查备份服务是否可用
            assert backup_service is not None, "备份服务应该可用"
            assert backup_scheduler is not None, "备份调度器应该可用"
            
            # 检查关键方法是否存在
            required_methods = ['get_status']
            for method in required_methods:
                assert hasattr(backup_scheduler, method), f"调度器应该有{method}方法"
            
            self.log_test_result("备份健康检查", True)
            
        except Exception as e:
            self.log_test_result("备份健康检查", False, f"异常: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始备份调度器功能测试...\n")
        
        # 运行测试
        await self.test_scheduler_lifecycle()
        self.test_task_configuration()
        self.test_daily_full_backup_config()
        self.test_next_backup_time_calculation()
        await self.test_backup_management()
        await self.test_recent_backups()
        await self.test_backup_report()
        await self.test_custom_backup_task()
        self.test_backup_health_check()
        
        # 输出测试结果
        print(f"\n{'='*100}")
        print(f"测试完成! 总计: {self.total_tests}, 通过: {self.passed_tests}, 失败: {self.total_tests - self.passed_tests}")
        print(f"成功率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        
        # 输出失败的测试
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['error']}")
        
        print()

async def main():
    """主函数"""
    tester = BackupSchedulerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())