#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份调度服务

定时任务服务，用于：
- 定时执行全量备份
- 定时执行增量备份
- 自动清理过期备份
- 备份文件归档管理
- 备份状态监控
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..db.database import get_db
from .backup_service import BackupService
from ..core.config import settings


class BackupScheduler:
    """备份调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.backup_service = BackupService()
        self._setup_jobs()
        
        logger.info("备份调度器初始化完成")
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 每天凌晨1点执行全量备份
        self.scheduler.add_job(
            self._sync_full_backup,
            trigger=CronTrigger(hour=1, minute=0),
            id='daily_full_backup',
            name='每日全量备份',
            max_instances=1,
            coalesce=True
        )
        
        # 每4小时执行增量备份
        self.scheduler.add_job(
            self._sync_incremental_backup,
            trigger=IntervalTrigger(hours=4),
            id='incremental_backup',
            name='增量备份',
            max_instances=1,
            coalesce=True
        )
        
        # 每天凌晨3点清理过期备份
        self.scheduler.add_job(
            self._sync_cleanup_expired_backups,
            trigger=CronTrigger(hour=3, minute=0),
            id='cleanup_expired_backups',
            name='清理过期备份',
            max_instances=1,
            coalesce=True
        )
        
        # 每周日凌晨4点执行备份归档
        self.scheduler.add_job(
            self._sync_archive_backups,
            trigger=CronTrigger(day_of_week=6, hour=4, minute=0),
            id='archive_backups',
            name='备份归档',
            max_instances=1,
            coalesce=True
        )
        
        # 每小时检查备份状态
        self.scheduler.add_job(
            self._sync_check_backup_status,
            trigger=IntervalTrigger(hours=1),
            id='check_backup_status',
            name='检查备份状态',
            max_instances=1,
            coalesce=True
        )
        
        # 每天早上8点生成备份报告
        self.scheduler.add_job(
            self._sync_generate_backup_report,
            trigger=CronTrigger(hour=8, minute=0),
            id='generate_backup_report',
            name='生成备份报告',
            max_instances=1,
            coalesce=True
        )
        
        logger.info("备份定时任务设置完成")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("备份调度器已启动")
        else:
            logger.warning("备份调度器已在运行中")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("备份调度器已停止")
            return True
        else:
            logger.warning("备份调度器未在运行")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "is_running": self.is_running,
            "jobs_count": len(jobs),
            "jobs": jobs
        }
    
    def _sync_full_backup(self):
        """同步执行全量备份"""
        asyncio.create_task(self._full_backup())
    
    def _sync_incremental_backup(self):
        """同步执行增量备份"""
        asyncio.create_task(self._incremental_backup())
    
    def _sync_cleanup_expired_backups(self):
        """同步清理过期备份"""
        asyncio.create_task(self._cleanup_expired_backups())
    
    def _sync_archive_backups(self):
        """同步备份归档"""
        asyncio.create_task(self._archive_backups())
    
    def _sync_check_backup_status(self):
        """同步检查备份状态"""
        asyncio.create_task(self._check_backup_status())
    
    def _sync_generate_backup_report(self):
        """同步生成备份报告"""
        asyncio.create_task(self._generate_backup_report())
    
    async def _full_backup(self):
        """执行全量备份"""
        try:
            logger.info("开始执行定时全量备份")
            
            # 数据库全量备份
            db_result = await self.backup_service.create_backup(
                backup_type="database",
                description="定时数据库全量备份",
                options={"compression": True, "verify": True}
            )
            
            # 文件全量备份
            file_result = await self.backup_service.create_backup(
                backup_type="files",
                description="定时文件全量备份",
                options={"compression": True, "verify": True}
            )
            
            # 配置全量备份
            config_result = await self.backup_service.create_backup(
                backup_type="config",
                description="定时配置全量备份",
                options={"compression": True, "verify": True}
            )
            
            logger.info(f"定时全量备份完成 - 数据库: {db_result['backup_id']}, 文件: {file_result['backup_id']}, 配置: {config_result['backup_id']}")
            
        except Exception as e:
            logger.error(f"定时全量备份失败: {str(e)}")
    
    async def _incremental_backup(self):
        """执行增量备份"""
        try:
            logger.info("开始执行定时增量备份")
            
            # 数据库增量备份
            db_result = await self.backup_service.create_backup(
                backup_type="incremental",
                description="定时数据库增量备份",
                options={"compression": True, "verify": True}
            )
            
            logger.info(f"定时增量备份完成 - 备份ID: {db_result['backup_id']}")
            
        except Exception as e:
            logger.error(f"定时增量备份失败: {str(e)}")
    
    async def _cleanup_expired_backups(self):
        """清理过期备份"""
        try:
            logger.info("开始清理过期备份")
            
            # 清理30天前的备份
            cutoff_date = datetime.now() - timedelta(days=30)
            result = await self.backup_service.cleanup_expired_backups(cutoff_date)
            
            logger.info(f"过期备份清理完成 - 清理数量: {result.get('cleaned_count', 0)}")
            
        except Exception as e:
            logger.error(f"清理过期备份失败: {str(e)}")
    
    async def _archive_backups(self):
        """备份归档"""
        try:
            logger.info("开始备份归档")
            
            # 获取7天前的备份进行归档
            archive_date = datetime.now() - timedelta(days=7)
            backups = await self.backup_service.get_backups_before_date(archive_date)
            
            archived_count = 0
            for backup in backups:
                try:
                    # 压缩并移动到归档目录
                    await self.backup_service.archive_backup(backup['backup_id'])
                    archived_count += 1
                except Exception as e:
                    logger.error(f"归档备份 {backup['backup_id']} 失败: {str(e)}")
            
            logger.info(f"备份归档完成 - 归档数量: {archived_count}")
            
        except Exception as e:
            logger.error(f"备份归档失败: {str(e)}")
    
    async def _check_backup_status(self):
        """检查备份状态"""
        try:
            logger.debug("检查备份状态")
            
            # 检查最近24小时的备份状态
            since_date = datetime.now() - timedelta(hours=24)
            recent_backups = await self.backup_service.get_backups_since_date(since_date)
            
            failed_backups = [b for b in recent_backups if b.get('status') == 'failed']
            
            if failed_backups:
                logger.warning(f"发现 {len(failed_backups)} 个失败的备份")
                # 这里可以发送告警通知
            
        except Exception as e:
            logger.error(f"检查备份状态失败: {str(e)}")
    
    async def _generate_backup_report(self):
        """生成备份报告"""
        try:
            logger.info("生成备份报告")
            
            # 获取备份统计信息
            stats = await self.backup_service.get_backup_statistics()
            
            # 生成报告内容
            report = {
                "date": datetime.now().isoformat(),
                "total_backups": stats.get('total_backups', 0),
                "successful_backups": stats.get('successful_backups', 0),
                "failed_backups": stats.get('failed_backups', 0),
                "total_size": stats.get('total_size', 0),
                "last_backup": stats.get('last_backup_time')
            }
            
            # 保存报告
            await self.backup_service.save_backup_report(report)
            
            logger.info("备份报告生成完成")
            
        except Exception as e:
            logger.error(f"生成备份报告失败: {str(e)}")
    
    async def add_custom_backup_job(self, name: str, trigger_type: str, 
                                   trigger_config: Dict[str, Any], 
                                   backup_config: Dict[str, Any]) -> str:
        """添加自定义备份任务"""
        try:
            job_id = f"custom_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if trigger_type == 'cron':
                trigger = CronTrigger(**trigger_config)
            elif trigger_type == 'interval':
                trigger = IntervalTrigger(**trigger_config)
            else:
                raise ValueError(f"不支持的触发器类型: {trigger_type}")
            
            # 创建备份任务函数
            def custom_backup_task():
                asyncio.create_task(self._execute_backup_task(name, backup_config))
            
            self.scheduler.add_job(
                custom_backup_task,
                trigger=trigger,
                id=job_id,
                name=f"自定义备份任务: {name}",
                replace_existing=True
            )
            
            logger.info(f"添加自定义备份任务成功: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"添加自定义备份任务失败: {str(e)}")
            raise
    
    async def remove_job(self, job_id: str):
        """移除备份任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"移除备份任务成功: {job_id}")
        except Exception as e:
            logger.error(f"移除备份任务失败: {str(e)}")
            raise
    
    async def modify_job(self, job_id: str, trigger_type: str, 
                        trigger_config: Dict[str, Any], 
                        backup_config: Dict[str, Any]):
        """修改备份任务"""
        try:
            if trigger_type == 'cron':
                trigger = CronTrigger(**trigger_config)
            elif trigger_type == 'interval':
                trigger = IntervalTrigger(**trigger_config)
            else:
                raise ValueError(f"不支持的触发器类型: {trigger_type}")
            
            self.scheduler.modify_job(job_id, trigger=trigger)
            logger.info(f"修改备份任务成功: {job_id}")
            
        except Exception as e:
            logger.error(f"修改备份任务失败: {str(e)}")
            raise
    
    async def pause_job(self, job_id: str):
        """暂停备份任务"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"暂停备份任务成功: {job_id}")
        except Exception as e:
            logger.error(f"暂停备份任务失败: {str(e)}")
            raise
    
    async def resume_job(self, job_id: str):
        """恢复备份任务"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"恢复备份任务成功: {job_id}")
        except Exception as e:
            logger.error(f"恢复备份任务失败: {str(e)}")
            raise


    async def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """立即执行备份任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                raise ValueError(f"任务不存在: {job_id}")
            
            # 立即执行任务
            execution_time = datetime.now()
            job.func()
            
            logger.info(f"立即执行备份任务成功: {job_id}")
            return {
                "job_id": job_id,
                "execution_time": execution_time.isoformat(),
                "status": "executed"
            }
            
        except Exception as e:
            logger.error(f"立即执行备份任务失败: {str(e)}")
            raise
    
    async def _execute_backup_task(self, name: str, backup_config: Dict[str, Any]):
        """执行备份任务"""
        try:
            logger.info(f"开始执行自定义备份任务: {name}")
            
            backup_type = backup_config.get('type', 'database')
            description = backup_config.get('description', f'自定义备份任务: {name}')
            options = backup_config.get('options', {})
            
            result = await self.backup_service.create_backup(
                backup_type=backup_type,
                description=description,
                options=options
            )
            
            logger.info(f"自定义备份任务完成: {name} - 备份ID: {result['backup_id']}")
            
        except Exception as e:
            logger.error(f"自定义备份任务失败: {name} - {str(e)}")


# 全局备份调度器实例
backup_scheduler = BackupScheduler()