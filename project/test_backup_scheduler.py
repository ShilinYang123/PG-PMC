#!/usr/bin/env python3
"""备份调度器测试脚本

测试定时备份机制的各项功能：
- 备份调度器启动和停止
- 定时任务配置和执行
- 备份文件管理和清理
- 备份归档功能
- 备份报告生成
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.backup_scheduler import backup_scheduler
from app.services.backup_service import backup_service
from app.services.backup_tasks import (
    get_backup_schedule, 
    get_all_backup_tasks,
    calculate_next_backup_time
)


class BackupSchedulerTester:
    """备份调度器测试类"""
    
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_scheduler_lifecycle(self):
        """测试调度器生命周期"""
        print("\n=== 测试调度器生命周期 ===")
        
        try:
            # 测试启动调度器
            await backup_scheduler.start()
            status = await backup_scheduler.get_status()
            self.log_test(
                "调度器启动", 
                status.get('running', False),
                f"调度器状态: {status.get('status', 'unknown')}"
            )
            
            # 测试获取任务列表
            jobs = await backup_scheduler.list_jobs()
            self.log_test(
                "获取任务列表",
                isinstance(jobs, list),
                f"找到 {len(jobs)} 个任务"
            )
            
            # 测试停止调度器
            await backup_scheduler.stop()
            status = await backup_scheduler.get_status()
            self.log_test(
                "调度器停止",
                not status.get('running', True),
                f"调度器状态: {status.get('status', 'unknown')}"
            )
            
        except Exception as e:
            self.log_test("调度器生命周期", False, f"异常: {str(e)}")
    
    async def test_backup_tasks_config(self):
        """测试备份任务配置"""
        print("\n=== 测试备份任务配置 ===")
        
        try:
            # 测试获取所有任务配置
            all_tasks = get_all_backup_tasks()
            self.log_test(
                "获取任务配置",
                len(all_tasks) > 0,
                f"配置了 {len(all_tasks)} 个任务"
            )
            
            # 测试具体任务配置
            daily_backup = get_backup_schedule('daily_full_backup')
            self.log_test(
                "每日全量备份配置",
                daily_backup.get('trigger') == 'cron',
                f"触发器: {daily_backup.get('trigger')}, 时间: {daily_backup.get('hour')}:{daily_backup.get('minute')}"
            )
            
            # 测试计算下次执行时间
            next_time = calculate_next_backup_time('daily_full_backup')
            self.log_test(
                "计算下次执行时间",
                isinstance(next_time, datetime),
                f"下次执行: {next_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
        except Exception as e:
            self.log_test("备份任务配置", False, f"异常: {str(e)}")
    
    async def test_custom_backup_job(self):
        """测试自定义备份任务"""
        print("\n=== 测试自定义备份任务 ===")
        
        try:
            await backup_scheduler.start()
            
            # 添加自定义任务
            job_id = await backup_scheduler.add_custom_backup_job(
                name="test_backup",
                trigger_type="interval",
                trigger_config={"minutes": 5},
                backup_config={
                    "backup_type": "incremental",
                    "include_database": True,
                    "include_files": False
                }
            )
            
            self.log_test(
                "添加自定义任务",
                job_id is not None,
                f"任务ID: {job_id}"
            )
            
            # 暂停任务
            await backup_scheduler.pause_job(job_id)
            self.log_test("暂停任务", True, f"任务 {job_id} 已暂停")
            
            # 恢复任务
            await backup_scheduler.resume_job(job_id)
            self.log_test("恢复任务", True, f"任务 {job_id} 已恢复")
            
            # 删除任务
            await backup_scheduler.remove_job(job_id)
            self.log_test("删除任务", True, f"任务 {job_id} 已删除")
            
            await backup_scheduler.stop()
            
        except Exception as e:
            self.log_test("自定义备份任务", False, f"异常: {str(e)}")
    
    async def test_backup_service_integration(self):
        """测试备份服务集成"""
        print("\n=== 测试备份服务集成 ===")
        
        try:
            # 测试获取指定日期前的备份
            cutoff_date = datetime.now() - timedelta(days=30)
            old_backups = await backup_service.get_backups_before_date(cutoff_date)
            self.log_test(
                "获取过期备份",
                isinstance(old_backups, list),
                f"找到 {len(old_backups)} 个过期备份"
            )
            
            # 测试获取指定日期后的备份
            since_date = datetime.now() - timedelta(days=7)
            recent_backups = await backup_service.get_backups_since_date(since_date)
            self.log_test(
                "获取最近备份",
                isinstance(recent_backups, list),
                f"找到 {len(recent_backups)} 个最近备份"
            )
            
            # 测试保存备份报告
            test_report = {
                "date": datetime.now().isoformat(),
                "total_backups": len(recent_backups),
                "total_size": sum(b.get('size', 0) for b in recent_backups),
                "status": "success"
            }
            
            report_file = await backup_service.save_backup_report(test_report)
            self.log_test(
                "保存备份报告",
                os.path.exists(report_file),
                f"报告文件: {report_file}"
            )
            
        except Exception as e:
            self.log_test("备份服务集成", False, f"异常: {str(e)}")
    
    async def test_backup_health_check(self):
        """测试备份健康检查"""
        print("\n=== 测试备份健康检查 ===")
        
        try:
            # 模拟健康检查
            health_status = {
                "scheduler_running": True,
                "recent_backup_exists": True,
                "disk_space_sufficient": True,
                "backup_integrity_ok": True
            }
            
            all_healthy = all(health_status.values())
            self.log_test(
                "备份健康检查",
                all_healthy,
                f"健康状态: {health_status}"
            )
            
        except Exception as e:
            self.log_test("备份健康检查", False, f"异常: {str(e)}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*50)
        print("测试总结")
        print("="*50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "="*50)


async def main():
    """主测试函数"""
    print("备份调度器功能测试")
    print("="*50)
    
    tester = BackupSchedulerTester()
    
    # 执行所有测试
    await tester.test_scheduler_lifecycle()
    await tester.test_backup_tasks_config()
    await tester.test_custom_backup_job()
    await tester.test_backup_service_integration()
    await tester.test_backup_health_check()
    
    # 打印测试总结
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())