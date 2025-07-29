"""备份任务配置

定义各种备份任务的调度频率和参数
"""

from typing import Dict, Any
from datetime import datetime, timedelta

# 备份任务调度配置
BACKUP_TASK_SCHEDULE = {
    # 每日全量备份 - 凌晨2点执行
    'daily_full_backup': {
        'trigger': 'cron',
        'hour': 2,
        'minute': 0,
        'description': '每日全量备份',
        'backup_type': 'full',
        'include_database': True,
        'include_files': True,
        'include_config': True,
        'retention_days': 30
    },
    
    # 每4小时增量备份
    'incremental_backup': {
        'trigger': 'interval',
        'hours': 4,
        'description': '增量备份',
        'backup_type': 'incremental',
        'include_database': True,
        'include_files': True,
        'include_config': False,
        'retention_days': 7
    },
    
    # 每日清理过期备份 - 凌晨3点执行
    'cleanup_expired_backups': {
        'trigger': 'cron',
        'hour': 3,
        'minute': 0,
        'description': '清理过期备份',
        'retention_days': 30
    },
    
    # 每周备份归档 - 周日凌晨4点执行
    'weekly_backup_archive': {
        'trigger': 'cron',
        'day_of_week': 0,  # 周日
        'hour': 4,
        'minute': 0,
        'description': '每周备份归档',
        'archive_older_than_days': 7
    },
    
    # 每小时检查备份状态
    'backup_health_check': {
        'trigger': 'interval',
        'minutes': 60,
        'description': '备份健康检查',
        'check_recent_backups': True,
        'alert_on_failure': True
    },
    
    # 每日生成备份报告 - 早上8点执行
    'daily_backup_report': {
        'trigger': 'cron',
        'hour': 8,
        'minute': 0,
        'description': '每日备份报告',
        'include_statistics': True,
        'send_email': True
    },
    
    # 每周数据库优化备份 - 周六凌晨1点执行
    'weekly_database_optimize': {
        'trigger': 'cron',
        'day_of_week': 5,  # 周六
        'hour': 1,
        'minute': 0,
        'description': '每周数据库优化备份',
        'backup_type': 'full',
        'optimize_database': True,
        'include_database': True,
        'include_files': False,
        'include_config': False
    },
    
    # 每月配置文件备份 - 每月1号凌晨5点执行
    'monthly_config_backup': {
        'trigger': 'cron',
        'day': 1,
        'hour': 5,
        'minute': 0,
        'description': '每月配置文件备份',
        'backup_type': 'full',
        'include_database': False,
        'include_files': False,
        'include_config': True,
        'retention_days': 365
    }
}

# 备份任务默认参数
DEFAULT_BACKUP_PARAMS = {
    'max_retries': 3,
    'retry_delay': 300,  # 5分钟
    'timeout': 3600,     # 1小时
    'compression_level': 6,
    'verify_backup': True,
    'send_notification': True
}

# 备份优先级配置
BACKUP_PRIORITY = {
    'database': 1,    # 最高优先级
    'config': 2,      # 中等优先级
    'files': 3,       # 较低优先级
    'logs': 4         # 最低优先级
}

# 备份存储配置
BACKUP_STORAGE_CONFIG = {
    'local': {
        'enabled': True,
        'path': 'backups',
        'max_size_gb': 100
    },
    'remote': {
        'enabled': False,
        'type': 's3',  # 或 'ftp', 'sftp'
        'config': {
            'bucket': 'pmc-backups',
            'region': 'us-east-1'
        }
    }
}

# 备份通知配置
BACKUP_NOTIFICATION_CONFIG = {
    'email': {
        'enabled': True,
        'recipients': ['admin@company.com'],
        'on_success': False,
        'on_failure': True,
        'on_warning': True
    },
    'webhook': {
        'enabled': False,
        'url': 'https://hooks.slack.com/services/...',
        'on_success': True,
        'on_failure': True
    }
}

# 备份监控配置
BACKUP_MONITORING_CONFIG = {
    'health_check_interval': 3600,  # 1小时
    'max_backup_age_hours': 25,     # 超过25小时没有备份则告警
    'min_backup_size_mb': 1,        # 备份文件小于1MB则告警
    'max_backup_duration_minutes': 120,  # 备份超过2小时则告警
    'disk_usage_threshold': 0.9     # 磁盘使用率超过90%则告警
}


def get_backup_schedule(task_name: str) -> Dict[str, Any]:
    """获取备份任务调度配置"""
    return BACKUP_TASK_SCHEDULE.get(task_name, {})


def get_all_backup_tasks() -> Dict[str, Dict[str, Any]]:
    """获取所有备份任务配置"""
    return BACKUP_TASK_SCHEDULE


def is_backup_task_enabled(task_name: str) -> bool:
    """检查备份任务是否启用"""
    task_config = BACKUP_TASK_SCHEDULE.get(task_name, {})
    return task_config.get('enabled', True)


def get_backup_retention_days(backup_type: str) -> int:
    """获取备份保留天数"""
    retention_map = {
        'full': 30,
        'incremental': 7,
        'config': 90,
        'archive': 365
    }
    return retention_map.get(backup_type, 30)


def calculate_next_backup_time(task_name: str) -> datetime:
    """计算下次备份时间"""
    task_config = get_backup_schedule(task_name)
    
    if not task_config:
        return datetime.now() + timedelta(hours=24)
    
    trigger = task_config.get('trigger', 'interval')
    now = datetime.now()
    
    if trigger == 'cron':
        # 计算下次cron执行时间
        hour = task_config.get('hour', 0)
        minute = task_config.get('minute', 0)
        
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果今天的时间已过，则安排到明天
        if next_time <= now:
            next_time += timedelta(days=1)
            
        # 处理周任务
        if 'day_of_week' in task_config:
            day_of_week = task_config['day_of_week']
            days_ahead = day_of_week - next_time.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_time += timedelta(days=days_ahead)
            
        # 处理月任务
        if 'day' in task_config:
            day = task_config['day']
            if next_time.day >= day:
                # 下个月
                if next_time.month == 12:
                    next_time = next_time.replace(year=next_time.year + 1, month=1, day=day)
                else:
                    next_time = next_time.replace(month=next_time.month + 1, day=day)
            else:
                next_time = next_time.replace(day=day)
                
        return next_time
        
    elif trigger == 'interval':
        # 计算间隔执行时间
        hours = task_config.get('hours', 0)
        minutes = task_config.get('minutes', 0)
        
        interval = timedelta(hours=hours, minutes=minutes)
        return now + interval
    
    return now + timedelta(hours=24)


def is_task_enabled(task_name: str) -> bool:
    """检查任务是否启用"""
    task_config = get_backup_schedule(task_name)
    if not task_config:
        return False
    return task_config.get('enabled', True)


def get_backup_retention_days(task_name: str = 'daily_full_backup') -> int:
    """获取备份保留天数"""
    task_config = get_backup_schedule(task_name)
    if not task_config:
        return 30  # 默认保留30天
    return task_config.get('retention_days', 30)