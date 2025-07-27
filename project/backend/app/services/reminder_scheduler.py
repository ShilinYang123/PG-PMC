"""催办调度服务

定时任务服务，用于：
- 定时检查逾期催办
- 自动升级催办
- 发送定时通知
- 清理过期数据
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..db.database import get_db
from .reminder_notification_service import ReminderNotificationService
from .multi_channel_notification_service import MultiChannelNotificationService
from ..models.reminder import Reminder, ReminderStatus
from ..core.config import settings


class ReminderScheduler:
    """催办调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self._setup_jobs()
        
        logger.info("催办调度器初始化完成")
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 每5分钟检查一次逾期催办
        self.scheduler.add_job(
            self._sync_check_overdue_reminders,
            trigger=IntervalTrigger(minutes=5),
            id='check_overdue_reminders',
            name='检查逾期催办',
            max_instances=1,
            coalesce=True
        )
        
        # 每小时处理计划发送的通知
        self.scheduler.add_job(
            self._sync_process_scheduled_notifications,
            trigger=IntervalTrigger(hours=1),
            id='process_scheduled_notifications',
            name='处理计划通知',
            max_instances=1,
            coalesce=True
        )
        
        # 每天早上8点发送催办汇总
        self.scheduler.add_job(
            self._sync_send_daily_summary,
            trigger=CronTrigger(hour=8, minute=0),
            id='send_daily_summary',
            name='发送每日催办汇总',
            max_instances=1,
            coalesce=True
        )
        
        # 每天凌晨2点清理过期数据
        self.scheduler.add_job(
            self._sync_cleanup_expired_data,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_expired_data',
            name='清理过期数据',
            max_instances=1,
            coalesce=True
        )
        
        # 每周一早上9点发送周报
        self.scheduler.add_job(
            self._sync_send_weekly_report,
            trigger=CronTrigger(day_of_week=0, hour=9, minute=0),
            id='send_weekly_report',
            name='发送催办周报',
            max_instances=1,
            coalesce=True
        )
        
        logger.info("定时任务设置完成")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("催办调度器已启动")
        else:
            logger.warning("催办调度器已在运行中")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("催办调度器已停止")
        else:
            logger.warning("催办调度器未在运行")
    
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
    
    def _sync_check_overdue_reminders(self):
        """同步包装方法：检查逾期催办"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._check_overdue_reminders())
        finally:
            loop.close()
    
    def _sync_process_scheduled_notifications(self):
        """同步包装方法：处理计划通知"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._process_scheduled_notifications())
        finally:
            loop.close()
    
    def _sync_send_daily_summary(self):
        """同步包装方法：发送每日催办汇总"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_daily_summary())
        finally:
            loop.close()
    
    def _sync_cleanup_expired_data(self):
        """同步包装方法：清理过期数据"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._cleanup_expired_data())
        finally:
            loop.close()
    
    def _sync_send_weekly_report(self):
        """同步包装方法：发送催办周报"""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_weekly_report())
        finally:
            loop.close()
    
    async def _check_overdue_reminders(self):
        """检查逾期催办"""
        try:
            logger.debug("开始检查逾期催办")
            
            # 获取数据库会话
            db = next(get_db())
            try:
                reminder_notification_service = ReminderNotificationService(db)
                result = await reminder_notification_service.check_overdue_reminders()
                
                if result["success"]:
                    processed_count = result["processed_count"]
                    if processed_count > 0:
                        logger.info(f"逾期催办检查完成，处理了 {processed_count} 个催办")
                    else:
                        logger.debug("逾期催办检查完成，无需处理的催办")
                else:
                    logger.error(f"逾期催办检查失败: {result.get('error', 'Unknown error')}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"检查逾期催办时发生异常: {str(e)}")
    
    async def _process_scheduled_notifications(self):
        """处理计划发送的通知"""
        try:
            logger.debug("开始处理计划通知")
            
            db = next(get_db())
            try:
                notification_service = MultiChannelNotificationService(db)
                await notification_service.process_scheduled_messages()
                logger.debug("计划通知处理完成")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"处理计划通知时发生异常: {str(e)}")
    
    async def _send_daily_summary(self):
        """发送每日催办汇总"""
        try:
            logger.info("开始发送每日催办汇总")
            
            db = next(get_db())
            try:
                reminder_notification_service = ReminderNotificationService(db)
                result = await reminder_notification_service.send_daily_reminder_summary()
                
                if result["success"]:
                    logger.info(f"每日催办汇总发送成功: {result['date']}")
                else:
                    logger.error(f"每日催办汇总发送失败: {result.get('error', 'Unknown error')}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"发送每日催办汇总时发生异常: {str(e)}")
    
    async def _cleanup_expired_data(self):
        """清理过期数据"""
        try:
            logger.info("开始清理过期数据")
            
            db = next(get_db())
            try:
                # 清理30天前已响应的催办记录
                cutoff_date = datetime.now() - timedelta(days=30)
                
                expired_reminders = db.query(Reminder).filter(
                    Reminder.status == ReminderStatus.RESPONDED,
                    Reminder.responded_at < cutoff_date
                ).all()
                
                deleted_count = 0
                for reminder in expired_reminders:
                    db.delete(reminder)
                    deleted_count += 1
                
                if deleted_count > 0:
                    db.commit()
                    logger.info(f"清理过期数据完成，删除了 {deleted_count} 条已响应的催办记录")
                else:
                    logger.debug("清理过期数据完成，无需删除的记录")
                    
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"清理过期数据时发生异常: {str(e)}")
    
    async def _send_weekly_report(self):
        """发送催办周报"""
        try:
            logger.info("开始发送催办周报")
            
            db = next(get_db())
            try:
                # 计算本周的时间范围
                now = datetime.now()
                start_of_week = now - timedelta(days=now.weekday())
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                # 统计本周催办数据
                week_reminders = db.query(Reminder).filter(
                    Reminder.created_at >= start_of_week,
                    Reminder.created_at <= end_of_week
                ).all()
                
                week_responded = db.query(Reminder).filter(
                    Reminder.responded_at >= start_of_week,
                    Reminder.responded_at <= end_of_week,
                    Reminder.status == ReminderStatus.RESPONDED
                ).all()
                
                # 按类型统计
                type_stats = {}
                for reminder in week_reminders:
                    reminder_type = reminder.reminder_type.value
                    if reminder_type not in type_stats:
                        type_stats[reminder_type] = {"created": 0, "responded": 0}
                    type_stats[reminder_type]["created"] += 1
                
                for reminder in week_responded:
                    reminder_type = reminder.reminder_type.value
                    if reminder_type in type_stats:
                        type_stats[reminder_type]["responded"] += 1
                
                # 生成周报内容
                title = f"催办系统周报 - {start_of_week.strftime('%Y年第%W周')}"
                content = f"📈 催办系统周报\n\n"
                content += f"📅 统计周期: {start_of_week.strftime('%m月%d日')} - {end_of_week.strftime('%m月%d日')}\n\n"
                content += f"📊 总体统计:\n"
                content += f"• 新增催办: {len(week_reminders)} 个\n"
                content += f"• 已响应催办: {len(week_responded)} 个\n"
                
                if len(week_reminders) > 0:
                    response_rate = len(week_responded) / len(week_reminders) * 100
                    content += f"• 响应率: {response_rate:.1f}%\n\n"
                else:
                    content += f"• 响应率: 0%\n\n"
                
                if type_stats:
                    content += f"📋 分类统计:\n"
                    for reminder_type, stats in type_stats.items():
                        content += f"• {reminder_type}: 新增{stats['created']}个, 响应{stats['responded']}个\n"
                
                # 发送周报
                notification_service = MultiChannelNotificationService(db)
                result = await notification_service.send_notification(
                    title=title,
                    content=content,
                    level=notification_service.NotificationLevel.INFO,
                    recipients=["@all"],  # 发送给所有用户
                    channels=[notification_service.ChannelType.SYSTEM, notification_service.ChannelType.EMAIL],
                    template_data={
                        "week_start": start_of_week.isoformat(),
                        "week_end": end_of_week.isoformat(),
                        "created_count": len(week_reminders),
                        "responded_count": len(week_responded),
                        "type_stats": type_stats
                    }
                )
                
                if result.get("results"):
                    logger.info(f"催办周报发送成功: {start_of_week.strftime('%Y年第%W周')}")
                else:
                    logger.error("催办周报发送失败")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"发送催办周报时发生异常: {str(e)}")
    
    async def trigger_immediate_check(self) -> Dict[str, Any]:
        """立即触发逾期检查"""
        try:
            logger.info("手动触发逾期催办检查")
            await self._check_overdue_reminders()
            return {"success": True, "message": "逾期检查已完成"}
        except Exception as e:
            logger.error(f"手动触发逾期检查失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def trigger_immediate_summary(self) -> Dict[str, Any]:
        """立即触发汇总发送"""
        try:
            logger.info("手动触发每日汇总发送")
            await self._send_daily_summary()
            return {"success": True, "message": "每日汇总已发送"}
        except Exception as e:
            logger.error(f"手动触发每日汇总失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_custom_job(
        self,
        func,
        trigger,
        job_id: str,
        name: str,
        **kwargs
    ):
        """添加自定义任务"""
        try:
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=name,
                max_instances=1,
                coalesce=True,
                **kwargs
            )
            logger.info(f"自定义任务已添加: {name} ({job_id})")
        except Exception as e:
            logger.error(f"添加自定义任务失败: {str(e)}")
    
    def remove_job(self, job_id: str):
        """移除任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"任务已移除: {job_id}")
        except Exception as e:
            logger.error(f"移除任务失败: {str(e)}")


# 全局调度器实例
reminder_scheduler = ReminderScheduler()


def start_reminder_scheduler():
    """启动催办调度器"""
    reminder_scheduler.start()


def stop_reminder_scheduler():
    """停止催办调度器"""
    reminder_scheduler.stop()


def get_scheduler_status() -> Dict[str, Any]:
    """获取调度器状态"""
    return reminder_scheduler.get_status()