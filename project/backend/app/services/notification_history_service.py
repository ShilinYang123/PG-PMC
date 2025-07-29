"""通知历史记录管理服务

管理通知发送历史，包括：
- 通知记录存储
- 发送状态跟踪
- 统计分析
- 历史查询
"""

import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from loguru import logger

from ..models.notification import Notification, NotificationStatus, NotificationPriority, NotificationChannel
from ..models.user import User
from ..database import get_db


@dataclass
class NotificationRecord:
    """通知记录"""
    id: int
    user_id: int
    channel: str
    recipient: str
    title: str
    content: str
    template_id: Optional[str]
    priority: str
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class NotificationStats:
    """通知统计"""
    total_count: int
    sent_count: int
    delivered_count: int
    read_count: int
    failed_count: int
    success_rate: float
    delivery_rate: float
    read_rate: float
    avg_delivery_time: Optional[float]  # 平均送达时间（秒）
    avg_read_time: Optional[float]      # 平均阅读时间（秒）


@dataclass
class ChannelStats:
    """渠道统计"""
    channel: str
    stats: NotificationStats
    daily_stats: List[Dict[str, Any]]
    hourly_stats: List[Dict[str, Any]]


@dataclass
class UserStats:
    """用户统计"""
    user_id: int
    username: str
    stats: NotificationStats
    channel_preferences: Dict[str, int]
    last_activity: Optional[datetime]


class NotificationHistoryService:
    """通知历史记录管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_record(self, user_id: int, channel: str, recipient: str,
                     title: str, content: str, template_id: Optional[str] = None,
                     priority: NotificationPriority = NotificationPriority.MEDIUM,
                     metadata: Optional[Dict[str, Any]] = None) -> int:
        """创建通知记录"""
        try:
            notification = Notification(
                user_id=user_id,
                channel=NotificationChannel(channel),
                recipient=recipient,
                title=title,
                content=content,
                template_id=template_id,
                priority=priority,
                status=NotificationStatus.PENDING,
                metadata=json.dumps(metadata or {}),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"Created notification record {notification.id}")
            return notification.id
            
        except Exception as e:
            logger.error(f"Error creating notification record: {e}")
            self.db.rollback()
            raise
    
    def update_status(self, notification_id: int, status: NotificationStatus,
                     error_message: Optional[str] = None,
                     sent_at: Optional[datetime] = None,
                     delivered_at: Optional[datetime] = None,
                     read_at: Optional[datetime] = None) -> bool:
        """更新通知状态"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                logger.warning(f"Notification {notification_id} not found")
                return False
            
            notification.status = status
            notification.updated_at = datetime.now()
            
            if error_message:
                notification.error_message = error_message
            if sent_at:
                notification.sent_at = sent_at
            if delivered_at:
                notification.delivered_at = delivered_at
            if read_at:
                notification.read_at = read_at
            
            # 更新重试次数
            if status == NotificationStatus.FAILED:
                notification.retry_count = (notification.retry_count or 0) + 1
            
            self.db.commit()
            logger.debug(f"Updated notification {notification_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
            self.db.rollback()
            return False
    
    def mark_as_sent(self, notification_id: int) -> bool:
        """标记为已发送"""
        return self.update_status(
            notification_id,
            NotificationStatus.SENT,
            sent_at=datetime.now()
        )
    
    def mark_as_delivered(self, notification_id: int) -> bool:
        """标记为已送达"""
        return self.update_status(
            notification_id,
            NotificationStatus.DELIVERED,
            delivered_at=datetime.now()
        )
    
    def mark_as_read(self, notification_id: int) -> bool:
        """标记为已读"""
        return self.update_status(
            notification_id,
            NotificationStatus.READ,
            read_at=datetime.now()
        )
    
    def mark_as_failed(self, notification_id: int, error_message: str) -> bool:
        """标记为失败"""
        return self.update_status(
            notification_id,
            NotificationStatus.FAILED,
            error_message=error_message
        )
    
    def get_record(self, notification_id: int) -> Optional[NotificationRecord]:
        """获取通知记录"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                return None
            
            return NotificationRecord(
                id=notification.id,
                user_id=notification.user_id,
                channel=notification.channel.value,
                recipient=notification.recipient,
                title=notification.title,
                content=notification.content,
                template_id=notification.template_id,
                priority=notification.priority.value,
                status=notification.status.value,
                sent_at=notification.sent_at,
                delivered_at=notification.delivered_at,
                read_at=notification.read_at,
                error_message=notification.error_message,
                retry_count=notification.retry_count or 0,
                metadata=json.loads(notification.metadata or "{}"),
                created_at=notification.created_at,
                updated_at=notification.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error getting notification record: {e}")
            return None
    
    def get_user_notifications(self, user_id: int, limit: int = 50,
                              offset: int = 0, channel: Optional[str] = None,
                              status: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[NotificationRecord]:
        """获取用户通知记录"""
        try:
            query = self.db.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if channel:
                query = query.filter(Notification.channel == NotificationChannel(channel))
            if status:
                query = query.filter(Notification.status == NotificationStatus(status))
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            records = []
            for notification in notifications:
                record = NotificationRecord(
                    id=notification.id,
                    user_id=notification.user_id,
                    channel=notification.channel.value,
                    recipient=notification.recipient,
                    title=notification.title,
                    content=notification.content,
                    template_id=notification.template_id,
                    priority=notification.priority.value,
                    status=notification.status.value,
                    sent_at=notification.sent_at,
                    delivered_at=notification.delivered_at,
                    read_at=notification.read_at,
                    error_message=notification.error_message,
                    retry_count=notification.retry_count or 0,
                    metadata=json.loads(notification.metadata or "{}"),
                    created_at=notification.created_at,
                    updated_at=notification.updated_at
                )
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def get_statistics(self, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      channel: Optional[str] = None,
                      user_id: Optional[int] = None) -> NotificationStats:
        """获取通知统计"""
        try:
            query = self.db.query(Notification)
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            if channel:
                query = query.filter(Notification.channel == NotificationChannel(channel))
            if user_id:
                query = query.filter(Notification.user_id == user_id)
            
            # 基础统计
            total_count = query.count()
            sent_count = query.filter(
                Notification.status.in_([
                    NotificationStatus.SENT,
                    NotificationStatus.DELIVERED,
                    NotificationStatus.READ
                ])
            ).count()
            delivered_count = query.filter(
                Notification.status.in_([
                    NotificationStatus.DELIVERED,
                    NotificationStatus.READ
                ])
            ).count()
            read_count = query.filter(
                Notification.status == NotificationStatus.READ
            ).count()
            failed_count = query.filter(
                Notification.status == NotificationStatus.FAILED
            ).count()
            
            # 计算比率
            success_rate = (sent_count / total_count * 100) if total_count > 0 else 0
            delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
            read_rate = (read_count / delivered_count * 100) if delivered_count > 0 else 0
            
            # 计算平均时间
            avg_delivery_time = None
            avg_read_time = None
            
            # 平均送达时间
            delivered_notifications = query.filter(
                and_(
                    Notification.sent_at.isnot(None),
                    Notification.delivered_at.isnot(None)
                )
            ).all()
            
            if delivered_notifications:
                delivery_times = [
                    (n.delivered_at - n.sent_at).total_seconds()
                    for n in delivered_notifications
                ]
                avg_delivery_time = sum(delivery_times) / len(delivery_times)
            
            # 平均阅读时间
            read_notifications = query.filter(
                and_(
                    Notification.delivered_at.isnot(None),
                    Notification.read_at.isnot(None)
                )
            ).all()
            
            if read_notifications:
                read_times = [
                    (n.read_at - n.delivered_at).total_seconds()
                    for n in read_notifications
                ]
                avg_read_time = sum(read_times) / len(read_times)
            
            return NotificationStats(
                total_count=total_count,
                sent_count=sent_count,
                delivered_count=delivered_count,
                read_count=read_count,
                failed_count=failed_count,
                success_rate=round(success_rate, 2),
                delivery_rate=round(delivery_rate, 2),
                read_rate=round(read_rate, 2),
                avg_delivery_time=round(avg_delivery_time, 2) if avg_delivery_time else None,
                avg_read_time=round(avg_read_time, 2) if avg_read_time else None
            )
            
        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return NotificationStats(
                total_count=0, sent_count=0, delivered_count=0,
                read_count=0, failed_count=0, success_rate=0,
                delivery_rate=0, read_rate=0,
                avg_delivery_time=None, avg_read_time=None
            )
    
    def get_channel_statistics(self, start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[ChannelStats]:
        """获取渠道统计"""
        try:
            channels = [channel.value for channel in NotificationChannel]
            channel_stats = []
            
            for channel in channels:
                # 获取渠道基础统计
                stats = self.get_statistics(
                    start_date=start_date,
                    end_date=end_date,
                    channel=channel
                )
                
                # 获取每日统计
                daily_stats = self._get_daily_stats(channel, start_date, end_date)
                
                # 获取每小时统计
                hourly_stats = self._get_hourly_stats(channel, start_date, end_date)
                
                channel_stats.append(ChannelStats(
                    channel=channel,
                    stats=stats,
                    daily_stats=daily_stats,
                    hourly_stats=hourly_stats
                ))
            
            return channel_stats
            
        except Exception as e:
            logger.error(f"Error getting channel statistics: {e}")
            return []
    
    def get_user_statistics(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> List[UserStats]:
        """获取用户统计"""
        try:
            # 获取活跃用户
            query = self.db.query(Notification.user_id).distinct()
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            user_ids = [row[0] for row in query.limit(limit).all()]
            user_stats = []
            
            for user_id in user_ids:
                # 获取用户信息
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    continue
                
                # 获取用户统计
                stats = self.get_statistics(
                    start_date=start_date,
                    end_date=end_date,
                    user_id=user_id
                )
                
                # 获取渠道偏好
                channel_preferences = self._get_user_channel_preferences(
                    user_id, start_date, end_date
                )
                
                # 获取最后活动时间
                last_activity = self.db.query(func.max(Notification.read_at)).filter(
                    Notification.user_id == user_id
                ).scalar()
                
                user_stats.append(UserStats(
                    user_id=user_id,
                    username=user.username,
                    stats=stats,
                    channel_preferences=channel_preferences,
                    last_activity=last_activity
                ))
            
            return user_stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return []
    
    def _get_daily_stats(self, channel: str, start_date: Optional[datetime],
                        end_date: Optional[datetime]) -> List[Dict[str, Any]]:
        """获取每日统计"""
        try:
            query = self.db.query(
                func.date(Notification.created_at).label('date'),
                func.count(Notification.id).label('total'),
                func.sum(
                    func.case(
                        [(Notification.status.in_([
                            NotificationStatus.SENT,
                            NotificationStatus.DELIVERED,
                            NotificationStatus.READ
                        ]), 1)],
                        else_=0
                    )
                ).label('sent'),
                func.sum(
                    func.case(
                        [(Notification.status == NotificationStatus.FAILED, 1)],
                        else_=0
                    )
                ).label('failed')
            ).filter(Notification.channel == NotificationChannel(channel))
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            results = query.group_by(
                func.date(Notification.created_at)
            ).order_by(
                func.date(Notification.created_at)
            ).all()
            
            daily_stats = []
            for result in results:
                daily_stats.append({
                    'date': result.date.isoformat(),
                    'total': result.total,
                    'sent': result.sent or 0,
                    'failed': result.failed or 0,
                    'success_rate': round((result.sent or 0) / result.total * 100, 2) if result.total > 0 else 0
                })
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []
    
    def _get_hourly_stats(self, channel: str, start_date: Optional[datetime],
                         end_date: Optional[datetime]) -> List[Dict[str, Any]]:
        """获取每小时统计"""
        try:
            # 只获取最近24小时的数据
            if not start_date:
                start_date = datetime.now() - timedelta(hours=24)
            
            query = self.db.query(
                func.extract('hour', Notification.created_at).label('hour'),
                func.count(Notification.id).label('total'),
                func.sum(
                    func.case(
                        [(Notification.status.in_([
                            NotificationStatus.SENT,
                            NotificationStatus.DELIVERED,
                            NotificationStatus.READ
                        ]), 1)],
                        else_=0
                    )
                ).label('sent')
            ).filter(
                and_(
                    Notification.channel == NotificationChannel(channel),
                    Notification.created_at >= start_date
                )
            )
            
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            results = query.group_by(
                func.extract('hour', Notification.created_at)
            ).order_by(
                func.extract('hour', Notification.created_at)
            ).all()
            
            hourly_stats = []
            for result in results:
                hourly_stats.append({
                    'hour': int(result.hour),
                    'total': result.total,
                    'sent': result.sent or 0,
                    'success_rate': round((result.sent or 0) / result.total * 100, 2) if result.total > 0 else 0
                })
            
            return hourly_stats
            
        except Exception as e:
            logger.error(f"Error getting hourly stats: {e}")
            return []
    
    def _get_user_channel_preferences(self, user_id: int,
                                     start_date: Optional[datetime],
                                     end_date: Optional[datetime]) -> Dict[str, int]:
        """获取用户渠道偏好"""
        try:
            query = self.db.query(
                Notification.channel,
                func.count(Notification.id).label('count')
            ).filter(Notification.user_id == user_id)
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            results = query.group_by(Notification.channel).all()
            
            preferences = {}
            for result in results:
                preferences[result.channel.value] = result.count
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user channel preferences: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """清理旧记录"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = self.db.query(Notification).filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old notification records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            self.db.rollback()
            return 0
    
    def export_records(self, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      format: str = "json") -> str:
        """导出记录"""
        try:
            query = self.db.query(Notification)
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            notifications = query.order_by(Notification.created_at.desc()).all()
            
            records = []
            for notification in notifications:
                record = {
                    'id': notification.id,
                    'user_id': notification.user_id,
                    'channel': notification.channel.value,
                    'recipient': notification.recipient,
                    'title': notification.title,
                    'content': notification.content,
                    'template_id': notification.template_id,
                    'priority': notification.priority.value,
                    'status': notification.status.value,
                    'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                    'delivered_at': notification.delivered_at.isoformat() if notification.delivered_at else None,
                    'read_at': notification.read_at.isoformat() if notification.read_at else None,
                    'error_message': notification.error_message,
                    'retry_count': notification.retry_count or 0,
                    'metadata': json.loads(notification.metadata or "{}"),
                    'created_at': notification.created_at.isoformat(),
                    'updated_at': notification.updated_at.isoformat()
                }
                records.append(record)
            
            if format == "json":
                return json.dumps(records, ensure_ascii=False, indent=2)
            elif format == "csv":
                # TODO: 实现CSV导出
                return "CSV export not implemented yet"
            else:
                raise ValueError(f"Unsupported format: {format}")
            
        except Exception as e:
            logger.error(f"Error exporting records: {e}")
            return ""


def get_history_service(db: Session) -> NotificationHistoryService:
    """获取历史记录服务实例"""
    return NotificationHistoryService(db)