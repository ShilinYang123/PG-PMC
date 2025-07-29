"""Celery应用配置

配置Celery任务队列和定时任务调度
"""

from celery import Celery
from celery.schedules import crontab
from .config import settings

# 创建Celery应用实例
celery_app = Celery(
    "pg_pmc",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.reminder_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks",
        "app.tasks.import_export_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 任务结果设置
    result_expires=3600,  # 1小时后过期
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # 任务路由
    task_routes={
        "app.tasks.reminder_tasks.*": {"queue": "reminders"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.import_export_tasks.*": {"queue": "import_export"},
    },
    
    # 工作进程设置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 定时任务调度
    beat_schedule={
        # 催办系统定时任务
        "process-pending-reminders": {
            "task": "process_pending_reminders",
            "schedule": 300.0,  # 每5分钟
        },
        "check-order-due-reminders": {
            "task": "check_order_due_reminders",
            "schedule": 3600.0,  # 每小时
        },
        "check-task-overdue-reminders": {
            "task": "check_task_overdue_reminders",
            "schedule": 1800.0,  # 每30分钟
        },
        "check-quality-issue-reminders": {
            "task": "check_quality_issue_reminders",
            "schedule": 3600.0,  # 每小时
        },
        "check-equipment-maintenance-reminders": {
            "task": "check_equipment_maintenance_reminders",
            "schedule": crontab(hour=8, minute=0),  # 每天早上8点
        },
        "cleanup-old-reminder-records": {
            "task": "cleanup_old_reminder_records",
            "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
        },
        "generate-reminder-daily-report": {
            "task": "generate_reminder_daily_report",
            "schedule": crontab(hour=8, minute=30),  # 每天早上8:30
        },
        
        # 通知系统定时任务
        "process-scheduled-notifications": {
            "task": "process_scheduled_notifications",
            "schedule": 60.0,  # 每分钟
        },
        "retry-failed-notifications": {
            "task": "retry_failed_notifications",
            "schedule": 1800.0,  # 每30分钟
        },
        
        # 报表生成定时任务
        "generate-daily-reports": {
            "task": "generate_daily_reports",
            "schedule": crontab(hour=7, minute=0),  # 每天早上7点
        },
        "generate-weekly-reports": {
            "task": "generate_weekly_reports",
            "schedule": crontab(hour=6, minute=0, day_of_week=1),  # 每周一早上6点
        },
    },
)

# 任务发现
celery_app.autodiscover_tasks()

# 启动时的钩子
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置周期性任务"""
    # 这里可以添加动态任务调度逻辑
    pass

# 任务失败处理
@celery_app.task(bind=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')

# 导出Celery应用
__all__ = ["celery_app"]