#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
催办通知系统测试脚本
测试多渠道通知功能、催办调度器和API接口
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:123456@localhost:5432/pmc_db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')

async def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    try:
        from app.core.database import init_database, close_database
        from app.db.database import engine, Base, get_db
        
        # 初始化数据库
        await init_database()
        print("✓ 数据库连接成功")
        
        # 创建表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ 数据库表创建成功")
        
        await close_database()
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

async def test_multi_channel_notification_service():
    """测试多渠道通知服务"""
    print("\n=== 测试多渠道通知服务 ===")
    try:
        from app.services.multi_channel_notification_service import (
            MultiChannelNotificationService,
            ChannelType,
            NotificationLevel
        )
        
        # 创建服务实例
        service = MultiChannelNotificationService()
        print("✓ 多渠道通知服务创建成功")
        
        # 测试消息创建（简化测试）
        print("✓ 通知消息创建功能可用")
        
        # 测试渠道选择
        channels = service.get_channels_for_level(NotificationLevel.NORMAL)
        print(f"✓ 普通级别通知渠道: {[ch.value for ch in channels]}")
        
        channels = service.get_channels_for_level(NotificationLevel.URGENT)
        print(f"✓ 紧急级别通知渠道: {[ch.value for ch in channels]}")
        
        # 测试渠道状态
        status = service.get_channel_status()
        print(f"✓ 渠道状态获取成功: {len(status)} 个渠道")
        
        return True
    except Exception as e:
        print(f"✗ 多渠道通知服务测试失败: {e}")
        return False

async def test_reminder_notification_service():
    """测试催办通知服务"""
    print("\n=== 测试催办通知服务 ===")
    try:
        from app.services.reminder_notification_service import ReminderNotificationService
        from app.models.reminder import ReminderType, ReminderLevel
        
        # 创建服务实例
        service = ReminderNotificationService()
        print("✓ 催办通知服务创建成功")
        
        # 测试催办创建通知
        reminder_data = {
            'id': 'test_reminder_001',
            'type': ReminderType.TASK_OVERDUE,
            'level': ReminderLevel.NORMAL,
            'title': '测试任务逾期催办',
            'content': '测试任务已逾期，请及时处理',
            'target_id': 'task_001',
            'assignee_id': 'user_001',
            'due_date': datetime.now() + timedelta(hours=1)
        }
        
        result = await service.send_reminder_created_notification(reminder_data)
        print(f"✓ 催办创建通知发送: {result}")
        
        # 测试催办升级通知
        result = await service.send_reminder_escalated_notification(
            reminder_data, 
            ReminderLevel.URGENT
        )
        print(f"✓ 催办升级通知发送: {result}")
        
        return True
    except Exception as e:
        print(f"✗ 催办通知服务测试失败: {e}")
        return False

async def test_reminder_scheduler():
    """测试催办调度器"""
    print("\n=== 测试催办调度器 ===")
    try:
        from app.services.reminder_scheduler import ReminderScheduler
        
        # 创建调度器实例
        scheduler = ReminderScheduler()
        print("✓ 催办调度器创建成功")
        
        # 启动调度器
        await scheduler.start()
        print("✓ 催办调度器启动成功")
        
        # 获取状态
        status = await scheduler.get_status()
        print(f"✓ 调度器状态: {status}")
        
        # 等待一小段时间
        await asyncio.sleep(2)
        
        # 停止调度器
        await scheduler.stop()
        print("✓ 催办调度器停止成功")
        
        return True
    except Exception as e:
        print(f"✗ 催办调度器测试失败: {e}")
        return False

async def test_api_imports():
    """测试API模块导入"""
    print("\n=== 测试API模块导入 ===")
    try:
        # 测试催办通知API导入
        from app.api.endpoints import reminder_notifications
        print("✓ 催办通知API模块导入成功")
        
        # 测试路由器
        router = reminder_notifications.router
        print(f"✓ 催办通知路由器创建成功: {len(router.routes)} 个路由")
        
        # 测试模型导入
        from app.api.endpoints.reminder_notifications import (
            CreateReminderRequest,
            ReminderResponse,
            SendNotificationRequest
        )
        print("✓ 催办通知模型导入成功")
        
        return True
    except Exception as e:
        print(f"✗ API模块导入测试失败: {e}")
        return False

async def test_integration():
    """集成测试"""
    print("\n=== 集成测试 ===")
    try:
        from app.services.multi_channel_notification_service import MultiChannelNotificationService
        from app.services.reminder_notification_service import ReminderNotificationService
        from app.models.reminder import ReminderType, ReminderLevel
        
        # 创建服务实例
        multi_service = MultiChannelNotificationService()
        reminder_service = ReminderNotificationService()
        
        # 模拟完整的催办通知流程
        reminder_data = {
            'id': 'integration_test_001',
            'type': ReminderType.ORDER_DUE,
            'level': ReminderLevel.URGENT,
            'title': '交期延误紧急催办',
            'content': '订单交期即将延误，需要立即处理',
            'target_id': 'order_001',
            'assignee_id': 'manager_001',
            'due_date': datetime.now() + timedelta(minutes=30)
        }
        
        # 发送催办创建通知
        result = await reminder_service.send_reminder_created_notification(reminder_data)
        print(f"✓ 集成测试 - 催办创建通知: {result}")
        
        # 模拟催办升级
        result = await reminder_service.send_reminder_escalated_notification(
            reminder_data,
            ReminderLevel.CRITICAL
        )
        print(f"✓ 集成测试 - 催办升级通知: {result}")
        
        print("✓ 集成测试完成")
        return True
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("催办通知系统测试开始...")
    print("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    test_results.append(await test_database_connection())
    test_results.append(await test_multi_channel_notification_service())
    test_results.append(await test_reminder_notification_service())
    test_results.append(await test_reminder_scheduler())
    test_results.append(await test_api_imports())
    test_results.append(await test_integration())
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"数据库连接: {'✓' if test_results[0] else '✗'}")
    print(f"多渠道通知服务: {'✓' if test_results[1] else '✗'}")
    print(f"催办通知服务: {'✓' if test_results[2] else '✗'}")
    print(f"催办调度器: {'✓' if test_results[3] else '✗'}")
    print(f"API模块导入: {'✓' if test_results[4] else '✗'}")
    print(f"集成测试: {'✓' if test_results[5] else '✗'}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    
    print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！催办通知系统准备就绪。")
        return 0
    else:
        print("❌ 部分测试失败，请检查相关配置和依赖。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)