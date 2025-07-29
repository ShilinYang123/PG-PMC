"""通知配置管理服务

管理系统通知配置，包括：
- 通知渠道配置
- 通知规则配置
- 用户通知偏好
- 通知模板管理
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from ..models.notification import (
    NotificationTemplate, NotificationRule, NotificationType,
    NotificationPriority
)
from ..models.user import User
from ..schemas.notification import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationRuleCreate, NotificationRuleUpdate
)


class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    SMS = "sms"
    WECHAT = "wechat"
    SYSTEM = "system"


@dataclass
class ChannelConfig:
    """渠道配置"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]
    priority: int = 1


@dataclass
class UserNotificationPreference:
    """用户通知偏好"""
    user_id: int
    email_enabled: bool = True
    sms_enabled: bool = True
    wechat_enabled: bool = True
    system_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # 免打扰开始时间 HH:MM
    quiet_hours_end: Optional[str] = None    # 免打扰结束时间 HH:MM
    priority_threshold: NotificationPriority = NotificationPriority.LOW


class NotificationConfigService:
    """通知配置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.channel_configs = self._load_default_channel_configs()
        self.user_preferences = {}
        
    def _load_default_channel_configs(self) -> Dict[NotificationChannel, ChannelConfig]:
        """加载默认渠道配置"""
        return {
            NotificationChannel.EMAIL: ChannelConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                config={
                    "smtp_server": "smtp.qq.com",
                    "smtp_port": 587,
                    "use_tls": True,
                    "batch_size": 50,
                    "retry_count": 3
                },
                priority=1
            ),
            NotificationChannel.SMS: ChannelConfig(
                channel=NotificationChannel.SMS,
                enabled=True,
                config={
                    "provider": "mock",
                    "batch_size": 100,
                    "retry_count": 2,
                    "rate_limit": 1000  # 每小时限制
                },
                priority=2
            ),
            NotificationChannel.WECHAT: ChannelConfig(
                channel=NotificationChannel.WECHAT,
                enabled=True,
                config={
                    "corp_id": "your_corp_id",
                    "agent_id": "your_agent_id",
                    "batch_size": 200,
                    "retry_count": 3
                },
                priority=3
            ),
            NotificationChannel.SYSTEM: ChannelConfig(
                channel=NotificationChannel.SYSTEM,
                enabled=True,
                config={
                    "retention_days": 30,
                    "max_per_user": 1000
                },
                priority=4
            )
        }
    
    def get_channel_config(self, channel: NotificationChannel) -> Optional[ChannelConfig]:
        """获取渠道配置"""
        return self.channel_configs.get(channel)
    
    def update_channel_config(self, channel: NotificationChannel, config: Dict[str, Any]) -> bool:
        """更新渠道配置"""
        try:
            if channel in self.channel_configs:
                self.channel_configs[channel].config.update(config)
                logger.info(f"Updated channel config for {channel.value}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update channel config: {e}")
            return False
    
    def enable_channel(self, channel: NotificationChannel) -> bool:
        """启用通知渠道"""
        if channel in self.channel_configs:
            self.channel_configs[channel].enabled = True
            return True
        return False
    
    def disable_channel(self, channel: NotificationChannel) -> bool:
        """禁用通知渠道"""
        if channel in self.channel_configs:
            self.channel_configs[channel].enabled = False
            return True
        return False
    
    def get_user_preference(self, user_id: int) -> UserNotificationPreference:
        """获取用户通知偏好"""
        if user_id not in self.user_preferences:
            # 从数据库加载或创建默认偏好
            self.user_preferences[user_id] = UserNotificationPreference(user_id=user_id)
        return self.user_preferences[user_id]
    
    def update_user_preference(self, user_id: int, preference: UserNotificationPreference) -> bool:
        """更新用户通知偏好"""
        try:
            self.user_preferences[user_id] = preference
            # TODO: 保存到数据库
            logger.info(f"Updated notification preference for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user preference: {e}")
            return False
    
    def should_send_notification(self, user_id: int, channel: NotificationChannel, 
                               priority: NotificationPriority) -> bool:
        """判断是否应该发送通知"""
        # 检查渠道是否启用
        channel_config = self.get_channel_config(channel)
        if not channel_config or not channel_config.enabled:
            return False
        
        # 检查用户偏好
        user_pref = self.get_user_preference(user_id)
        
        # 检查渠道偏好
        if channel == NotificationChannel.EMAIL and not user_pref.email_enabled:
            return False
        elif channel == NotificationChannel.SMS and not user_pref.sms_enabled:
            return False
        elif channel == NotificationChannel.WECHAT and not user_pref.wechat_enabled:
            return False
        elif channel == NotificationChannel.SYSTEM and not user_pref.system_enabled:
            return False
        
        # 检查优先级阈值
        if priority.value < user_pref.priority_threshold.value:
            return False
        
        # 检查免打扰时间
        if self._is_in_quiet_hours(user_pref):
            # 只有高优先级通知才能在免打扰时间发送
            if priority != NotificationPriority.HIGH:
                return False
        
        return True
    
    def _is_in_quiet_hours(self, user_pref: UserNotificationPreference) -> bool:
        """检查是否在免打扰时间"""
        if not user_pref.quiet_hours_start or not user_pref.quiet_hours_end:
            return False
        
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(user_pref.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(user_pref.quiet_hours_end, "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:
                # 跨天的情况
                return now >= start_time or now <= end_time
        except Exception:
            return False
    
    def create_template(self, template_data: NotificationTemplateCreate) -> NotificationTemplate:
        """创建通知模板"""
        template = NotificationTemplate(
            name=template_data.name,
            type=template_data.type,
            title_template=template_data.title_template,
            content_template=template_data.content_template,
            variables=template_data.variables,
            is_active=template_data.is_active
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Created notification template: {template.name}")
        return template
    
    def update_template(self, template_id: int, template_data: NotificationTemplateUpdate) -> Optional[NotificationTemplate]:
        """更新通知模板"""
        template = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
        
        if not template:
            return None
        
        for field, value in template_data.dict(exclude_unset=True).items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"Updated notification template: {template.name}")
        return template
    
    def get_template(self, template_id: int) -> Optional[NotificationTemplate]:
        """获取通知模板"""
        return self.db.query(NotificationTemplate).filter(
            NotificationTemplate.id == template_id
        ).first()
    
    def list_templates(self, type_filter: Optional[NotificationType] = None) -> List[NotificationTemplate]:
        """列出通知模板"""
        query = self.db.query(NotificationTemplate)
        
        if type_filter:
            query = query.filter(NotificationTemplate.type == type_filter)
        
        return query.filter(NotificationTemplate.is_active == True).all()
    
    def create_rule(self, rule_data: NotificationRuleCreate) -> NotificationRule:
        """创建通知规则"""
        rule = NotificationRule(
            name=rule_data.name,
            event_type=rule_data.event_type,
            conditions=rule_data.conditions,
            template_id=rule_data.template_id,
            recipients=rule_data.recipients,
            channels=rule_data.channels,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Created notification rule: {rule.name}")
        return rule
    
    def update_rule(self, rule_id: int, rule_data: NotificationRuleUpdate) -> Optional[NotificationRule]:
        """更新通知规则"""
        rule = self.db.query(NotificationRule).filter(
            NotificationRule.id == rule_id
        ).first()
        
        if not rule:
            return None
        
        for field, value in rule_data.dict(exclude_unset=True).items():
            setattr(rule, field, value)
        
        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)
        
        logger.info(f"Updated notification rule: {rule.name}")
        return rule
    
    def get_rule(self, rule_id: int) -> Optional[NotificationRule]:
        """获取通知规则"""
        return self.db.query(NotificationRule).filter(
            NotificationRule.id == rule_id
        ).first()
    
    def list_rules(self, event_type: Optional[str] = None) -> List[NotificationRule]:
        """列出通知规则"""
        query = self.db.query(NotificationRule)
        
        if event_type:
            query = query.filter(NotificationRule.event_type == event_type)
        
        return query.filter(NotificationRule.is_active == True).all()
    
    def get_rules_by_event(self, event_type: str) -> List[NotificationRule]:
        """根据事件类型获取规则"""
        return self.db.query(NotificationRule).filter(
            and_(
                NotificationRule.event_type == event_type,
                NotificationRule.is_active == True
            )
        ).all()
    
    def test_notification_config(self, user_id: int, channel: NotificationChannel) -> Dict[str, Any]:
        """测试通知配置"""
        result = {
            "channel": channel.value,
            "user_id": user_id,
            "channel_enabled": False,
            "user_preference_enabled": False,
            "can_send": False,
            "config": {},
            "errors": []
        }
        
        try:
            # 检查渠道配置
            channel_config = self.get_channel_config(channel)
            if channel_config:
                result["channel_enabled"] = channel_config.enabled
                result["config"] = channel_config.config
            else:
                result["errors"].append(f"Channel {channel.value} not configured")
            
            # 检查用户偏好
            user_pref = self.get_user_preference(user_id)
            if channel == NotificationChannel.EMAIL:
                result["user_preference_enabled"] = user_pref.email_enabled
            elif channel == NotificationChannel.SMS:
                result["user_preference_enabled"] = user_pref.sms_enabled
            elif channel == NotificationChannel.WECHAT:
                result["user_preference_enabled"] = user_pref.wechat_enabled
            elif channel == NotificationChannel.SYSTEM:
                result["user_preference_enabled"] = user_pref.system_enabled
            
            # 检查是否可以发送
            result["can_send"] = self.should_send_notification(
                user_id, channel, NotificationPriority.MEDIUM
            )
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """获取通知统计信息"""
        stats = {
            "channels": {},
            "templates_count": 0,
            "rules_count": 0,
            "active_users": len(self.user_preferences)
        }
        
        # 渠道统计
        for channel, config in self.channel_configs.items():
            stats["channels"][channel.value] = {
                "enabled": config.enabled,
                "priority": config.priority
            }
        
        # 模板和规则统计
        stats["templates_count"] = self.db.query(NotificationTemplate).filter(
            NotificationTemplate.is_active == True
        ).count()
        
        stats["rules_count"] = self.db.query(NotificationRule).filter(
            NotificationRule.is_active == True
        ).count()
        
        return stats