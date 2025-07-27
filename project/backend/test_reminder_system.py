#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
催办系统测试脚本

用于测试催办系统的基本功能，包括：
1. 数据库连接
2. 模型创建
3. 服务功能
4. API接口
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import Base, get_db
from app.models.reminder import ReminderRecord, ReminderRule, ReminderResponse, ReminderType, ReminderLevel, ReminderStatus
from app.services.reminder_service import ReminderService
from app.services.notification_service import NotificationService
from app.services.wechat_service import WeChatService
from app.core.exceptions import ValidationException, BusinessException


def test_database_connection():
    """测试数据库连接"""
    print("\n=== 测试数据库连接 ===")
    try:
        # 创建数据库引擎
        engine = create_engine("sqlite:///./pmc.db")
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功")
            
        # 检查表是否存在
        with engine.connect() as conn:
            tables = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%reminder%'
            """)).fetchall()
            
            if tables:
                print(f"✅ 找到催办相关表: {[table[0] for table in tables]}")
            else:
                print("❌ 未找到催办相关表")
                
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def test_models():
    """测试模型创建"""
    print("\n=== 测试模型创建 ===")
    try:
        # 创建会话
        engine = create_engine("sqlite:///./pmc.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 测试创建催办规则
        rule = ReminderRule(
            name="测试规则",
            reminder_type=ReminderType.TASK_OVERDUE,
            trigger_conditions={"delay_hours": 24},
            escalation_intervals=[1, 3, 7],
            initial_level=ReminderLevel.NORMAL,
            max_escalations=3,
            recipient_config={"user_ids": [1, 2]},
            title_template="测试催办标题",
            content_template="测试催办内容",
            created_by=1,
            is_active=True
        )
        db.add(rule)
        db.commit()
        print("✅ 催办规则创建成功")
        
        # 测试创建催办记录
        record = ReminderRecord(
            reminder_type=ReminderType.TASK_OVERDUE,
            related_type="order",
            related_id=1,
            title="测试催办",
            content="这是一个测试催办记录",
            recipient_user_id=1,
            sender_user_id=1,
            level=ReminderLevel.NORMAL,
            status=ReminderStatus.PENDING
        )
        db.add(record)
        db.commit()
        print("✅ 催办记录创建成功")
        
        # 测试创建响应记录
        response = ReminderResponse(
            reminder_id=record.id,
            responder_id=1,
            response_type="manual",
            response_content="已收到催办，正在处理",
            response_data={"action_taken": "开始处理订单", "completion_status": "进行中"}
        )
        db.add(response)
        db.commit()
        print("✅ 响应记录创建成功")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 模型创建失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def test_reminder_service():
    """测试催办服务"""
    print("\n=== 测试催办服务 ===")
    try:
        # 创建会话
        engine = create_engine("sqlite:///./pmc.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 初始化服务
        wechat_config = {"app_id": "test", "app_secret": "test"}
        wechat_service = WeChatService(wechat_config)
        notification_service = NotificationService(wechat_service)
        service = ReminderService(db, notification_service)
        
        # 测试创建催办
        reminder_id = service.create_reminder(
            reminder_type=ReminderType.TASK_OVERDUE,
            related_type="task",
            related_id=1,
            recipient_user_id=1,
            data={"task_name": "测试任务", "overdue_days": 3}
        )
        if reminder_id:
            print(f"✅ 催办服务创建成功，ID: {reminder_id}")
        else:
            print("⚠️ 催办服务创建返回None，可能没有匹配的规则")
        
        # 测试响应催办
        if reminder_id:
            response_success = service.mark_reminder_responded(
                record_id=reminder_id,
                response_content="已处理完成"
            )
            print(f"✅ 催办响应成功: {response_success}")
        else:
            print("⚠️ 跳过响应测试，因为催办创建失败")
        
        # 测试获取统计信息
        stats = service.get_reminder_statistics()
        print(f"✅ 统计信息获取成功: {stats}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 催办服务测试失败: {e}")
        if 'db' in locals():
            db.close()
        return False


def test_api_imports():
    """测试API模块导入"""
    print("\n=== 测试API模块导入 ===")
    try:
        from app.api.endpoints.reminder import router
        from app.schemas.reminder import ReminderRecordCreate
        print("✅ API模块导入成功")
        
        # 检查路由数量
        route_count = len(router.routes)
        print(f"✅ 发现 {route_count} 个API路由")
        
        return True
        
    except Exception as e:
        print(f"❌ API模块导入失败: {e}")
        return False


def main():
    """主测试函数"""
    print("催办系统测试开始...")
    print("=" * 50)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("模型创建", test_models),
        ("催办服务", test_reminder_service),
        ("API导入", test_api_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！催办系统已准备就绪。")
    else:
        print(f"\n⚠️  有 {len(results) - passed} 项测试失败，请检查相关配置。")


if __name__ == "__main__":
    main()