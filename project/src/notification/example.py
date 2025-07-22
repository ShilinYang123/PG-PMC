"""通知系统使用示例

展示如何使用PMC通知系统的各种功能。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from .service import NotificationService
from .config import NotificationConfig
from .models import NotificationPriority, ChannelType
from .utils import MessageFormatter


async def basic_usage_example():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    # 创建配置
    config_dict = {
        "service": {
            "name": "PMC Notification Service",
            "debug": True
        },
        "queue": {
            "max_size": 100,
            "batch_size": 5
        },
        "scheduler": {
            "worker_count": 1
        },
        "channels": [
            {
                "name": "wechat_api_test",
                "type": "wechat_api",
                "enabled": True,
                "settings": {
                    "corp_id": "test_corp_id",
                    "agent_id": "test_agent_id",
                    "secret": "test_secret"
                }
            },
            {
                "name": "wechat_bot_test",
                "type": "wechat_bot",
                "enabled": True,
                "settings": {
                    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test_key",
                    "secret": "test_secret"
                }
            }
        ]
    }
    
    # 创建通知服务
    service = NotificationService(config_dict)
    
    # 初始化服务
    await service.initialize(config_dict.get('channels', []))
    
    # 启动服务
    await service.start()
    
    try:
        # 发送简单文本消息
        message_id = await service.send_text(
            content="这是一条测试消息",
            recipients={"users": ["test_user"]}
        )
        print(f"发送文本消息，ID: {message_id}")
        
        # 发送Markdown消息
        markdown_content = """
**系统状态报告**

- CPU使用率: 75%
- 内存使用率: 60%
- 磁盘使用率: 45%

状态: 正常 ✅
        """.strip()
        
        message_id = await service.send_markdown(
            content=markdown_content,
            priority=NotificationPriority.HIGH
        )
        print(f"发送Markdown消息，ID: {message_id}")
        
        # 使用模板发送消息
        message_id = await service.send_alert(
            message="系统CPU使用率过高",
            level="warning"
        )
        print(f"发送告警消息，ID: {message_id}")
        
        # 等待消息处理
        await asyncio.sleep(2)
        
        # 检查消息状态
        status = await service.get_message_status(message_id)
        if status:
            print(f"消息状态: {status.status.value}")
        
    finally:
        # 停止服务
        await service.stop()


async def advanced_usage_example():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")
    
    # 创建服务
    service = NotificationService()
    
    # 手动配置渠道
    channels_config = [
        {
            "name": "primary_wechat",
            "type": "wechat_api",
            "enabled": True,
            "settings": {
                "corp_id": "primary_corp_id",
                "agent_id": "primary_agent_id",
                "secret": "primary_secret"
            },
            "rate_limit": 60,
            "timeout": 30
        },
        {
            "name": "backup_bot",
            "type": "wechat_bot",
            "enabled": True,
            "settings": {
                "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=backup_key",
                "secret": "backup_secret"
            },
            "rate_limit": 20,
            "timeout": 30
        }
    ]
    
    await service.initialize(channels_config)
    await service.start()
    
    try:
        # 批量发送消息
        notifications = [
            {
                "content": "批量消息1",
                "message_type": "text",
                "recipients": {"users": ["user1"]}
            },
            {
                "content": "批量消息2",
                "message_type": "text",
                "recipients": {"users": ["user2"]}
            },
            {
                "template_id": "task_completed",
                "template_vars": {
                    "task_name": "数据备份",
                    "status": "成功"
                },
                "recipients": {"users": ["admin"]}
            }
        ]
        
        message_ids = await service.send_batch_notifications(notifications)
        print(f"批量发送消息，IDs: {message_ids}")
        
        # 广播消息到所有渠道
        broadcast_ids = await service.broadcast_notification(
            title="系统维护通知",
            content="系统将于今晚22:00进行维护，预计持续2小时",
            message_type="markdown",
            priority=NotificationPriority.HIGH
        )
        print(f"广播消息，IDs: {broadcast_ids}")
        
        # 计划发送消息
        scheduled_time = datetime.now() + timedelta(minutes=5)
        message_id = await service.send_notification(
            title="计划消息",
            content="这是一条计划在5分钟后发送的消息",
            scheduled_time=scheduled_time
        )
        print(f"计划消息，ID: {message_id}")
        
        # 添加事件回调
        def on_message_sent(event_data):
            print(f"消息发送事件: {event_data}")
        
        def on_message_failed(event_data):
            print(f"消息失败事件: {event_data}")
        
        service.add_event_callback('message_sent', on_message_sent)
        service.add_event_callback('message_failed', on_message_failed)
        
        # 等待处理
        await asyncio.sleep(3)
        
        # 获取统计信息
        stats = service.get_stats()
        print(f"服务统计: {stats}")
        
        # 健康检查
        health = await service.health_check()
        print(f"健康状态: {health}")
        
    finally:
        await service.stop()


async def template_usage_example():
    """模板使用示例"""
    print("\n=== 模板使用示例 ===")
    
    from .models import NotificationTemplate
    
    service = NotificationService()
    await service.initialize()
    await service.start()
    
    try:
        # 创建自定义模板
        custom_template = NotificationTemplate(
            template_id="custom_report",
            name="自定义报告",
            title="{report_type}报告",
            content="""
**{report_type}报告**

**时间范围:** {start_date} 至 {end_date}

**关键指标:**
- 总数: {total_count}
- 成功率: {success_rate}%
- 平均响应时间: {avg_response_time}ms

**详细数据:**
{detailed_data}

**生成时间:** {generated_at}
            """.strip(),
            message_type="markdown",
            variables=["report_type", "start_date", "end_date", "total_count", 
                      "success_rate", "avg_response_time", "detailed_data", "generated_at"]
        )
        
        # 添加模板
        service.add_template(custom_template)
        
        # 使用自定义模板发送消息
        message_id = await service.send_notification(
            template_id="custom_report",
            template_vars={
                "report_type": "性能",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "total_count": "1,234",
                "success_rate": "99.5",
                "avg_response_time": "150",
                "detailed_data": "详细数据请查看附件",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        print(f"使用自定义模板发送消息，ID: {message_id}")
        
        # 列出所有模板
        templates = service.list_templates()
        print(f"可用模板数量: {len(templates)}")
        for template in templates:
            print(f"- {template.template_id}: {template.name}")
        
    finally:
        await service.stop()


async def formatter_usage_example():
    """格式化器使用示例"""
    print("\n=== 格式化器使用示例 ===")
    
    # 格式化告警消息
    alert_msg = MessageFormatter.format_alert(
        level="error",
        message="数据库连接失败",
        details={
            "错误代码": "DB_CONN_001",
            "服务器": "db-server-01",
            "重试次数": "3"
        }
    )
    print("告警消息格式:")
    print(alert_msg)
    
    # 格式化任务状态消息
    task_msg = MessageFormatter.format_task_status(
        task_name="数据同步任务",
        status="running",
        progress=75,
        details="正在同步用户数据"
    )
    print("\n任务状态消息格式:")
    print(task_msg)
    
    # 格式化数据报告消息
    report_msg = MessageFormatter.format_data_report(
        title="每日运营报告",
        data={
            "新增用户": 156,
            "活跃用户": 2340,
            "订单数量": 89,
            "收入": "¥12,345.67"
        },
        chart_url="https://example.com/chart/daily-report"
    )
    print("\n数据报告消息格式:")
    print(report_msg)


async def error_handling_example():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    from .exceptions import NotificationError, ChannelError
    
    service = NotificationService()
    
    try:
        # 尝试在未初始化的服务上发送消息
        await service.send_text("测试消息")
    except NotificationError as e:
        print(f"捕获到通知错误: {e}")
    
    # 正确初始化服务
    await service.initialize()
    await service.start()
    
    try:
        # 尝试使用不存在的模板
        await service.send_notification(
            template_id="non_existent_template",
            template_vars={"test": "value"}
        )
    except NotificationError as e:
        print(f"模板错误: {e}")
    
    try:
        # 尝试发送到不存在的渠道
        await service.send_text(
            content="测试消息",
            channel_name="non_existent_channel"
        )
    except (NotificationError, ChannelError) as e:
        print(f"渠道错误: {e}")
    
    finally:
        await service.stop()


async def main():
    """主函数"""
    print("PMC通知系统使用示例")
    print("=" * 50)
    
    # 运行各种示例
    await basic_usage_example()
    await advanced_usage_example()
    await template_usage_example()
    await formatter_usage_example()
    await error_handling_example()
    
    print("\n所有示例运行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())