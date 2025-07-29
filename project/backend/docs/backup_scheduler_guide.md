# 定时备份机制使用指南

## 概述

定时备份机制基于现有的调度服务，提供了完整的自动化备份解决方案，支持增量备份和全量备份，实现备份文件自动清理和归档。

## 主要功能

### 1. 预设定时任务

- **每日全量备份**: 每天凌晨2点执行完整备份
- **增量备份**: 每4小时执行一次增量备份
- **清理过期备份**: 每天凌晨3点清理过期备份文件
- **备份归档**: 每周日凌晨4点执行备份归档
- **健康检查**: 每小时检查备份系统状态
- **备份报告**: 每天生成备份状态报告

### 2. 自定义备份任务

支持添加、修改、删除、暂停、恢复自定义备份任务，提供灵活的备份策略配置。

### 3. 备份管理

- 自动清理过期备份文件
- 备份文件归档压缩
- 备份状态监控和报告
- 备份文件完整性检查

## 使用方法

### 启动备份调度器

备份调度器会随应用启动自动运行，无需手动启动。

### API接口

#### 获取调度器状态
```http
GET /api/backup/scheduler/status
```

#### 启动/停止调度器
```http
POST /api/backup/scheduler/start
POST /api/backup/scheduler/stop
```

#### 列出所有备份任务
```http
GET /api/backup/scheduler/jobs
```

#### 添加自定义备份任务
```http
POST /api/backup/scheduler/jobs
Content-Type: application/json

{
  "name": "custom_backup",
  "trigger_type": "cron",
  "trigger_config": {
    "hour": 6,
    "minute": 0
  },
  "backup_config": {
    "type": "database",
    "description": "自定义数据库备份",
    "options": {
      "include_database": true,
      "include_files": false
    }
  }
}
```

#### 删除备份任务
```http
DELETE /api/backup/scheduler/jobs/{job_id}
```

#### 修改备份任务
```http
PUT /api/backup/scheduler/jobs/{job_id}
```

#### 暂停/恢复备份任务
```http
POST /api/backup/scheduler/jobs/{job_id}/pause
POST /api/backup/scheduler/jobs/{job_id}/resume
```

#### 立即执行备份任务
```http
POST /api/backup/scheduler/jobs/{job_id}/run
```

## 配置说明

### 触发器类型

#### Cron触发器
```python
{
  "trigger_type": "cron",
  "trigger_config": {
    "hour": 2,        # 小时 (0-23)
    "minute": 0,      # 分钟 (0-59)
    "day_of_week": 0, # 星期几 (0=周日, 6=周六)
    "day": 1          # 月份中的第几天 (1-31)
  }
}
```

#### 间隔触发器
```python
{
  "trigger_type": "interval",
  "trigger_config": {
    "hours": 4,       # 间隔小时数
    "minutes": 30     # 间隔分钟数
  }
}
```

### 备份配置

```python
{
  "backup_config": {
    "type": "database",           # 备份类型: database, files, full
    "description": "备份描述",    # 备份描述
    "options": {
      "include_database": true,   # 包含数据库
      "include_files": true,     # 包含文件
      "include_config": true,    # 包含配置文件
      "compression": "gzip"      # 压缩方式
    }
  }
}
```

## 备份保留策略

- **全量备份**: 保留30天
- **增量备份**: 保留7天
- **归档备份**: 长期保存
- **备份报告**: 保留90天

## 监控和日志

### 日志位置
- 调度器日志: `logs/backup_scheduler.log`
- 备份任务日志: `logs/backup_tasks.log`

### 监控指标
- 备份成功率
- 备份文件大小
- 备份执行时间
- 存储空间使用情况

## 故障排除

### 常见问题

1. **备份任务未执行**
   - 检查调度器是否正在运行
   - 查看任务配置是否正确
   - 检查系统资源是否充足

2. **备份文件损坏**
   - 检查存储设备状态
   - 验证备份文件完整性
   - 查看备份过程中的错误日志

3. **存储空间不足**
   - 清理过期备份文件
   - 调整备份保留策略
   - 增加存储容量

### 性能优化

- 合理设置备份频率
- 使用增量备份减少数据传输
- 启用备份压缩节省存储空间
- 在系统负载较低时执行备份

## 安全考虑

- 备份文件加密存储
- 访问权限控制
- 备份传输安全
- 定期验证备份完整性

## 扩展功能

- 支持远程备份存储
- 备份文件同步到云存储
- 备份状态邮件通知
- 备份性能分析报告