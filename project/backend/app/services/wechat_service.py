"""微信通知服务

实现微信消息推送功能，支持：
- 生产进度提醒
- 交期预警通知
- 异常情况告警
- 日报周报推送
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import asyncio
from jinja2 import Template


class MessageType(Enum):
    """消息类型枚举"""
    PROGRESS_UPDATE = "progress_update"  # 进度更新
    DUE_DATE_WARNING = "due_date_warning"  # 交期预警
    EXCEPTION_ALERT = "exception_alert"  # 异常告警
    DAILY_REPORT = "daily_report"  # 日报
    WEEKLY_REPORT = "weekly_report"  # 周报
    SCHEDULE_NOTIFICATION = "schedule_notification"  # 排产通知


class Priority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class WeChatConfig:
    """微信配置"""
    corp_id: str  # 企业ID
    corp_secret: str  # 应用密钥
    agent_id: str  # 应用ID
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


@dataclass
class NotificationRule:
    """通知规则"""
    rule_id: str
    name: str
    message_type: MessageType
    trigger_conditions: Dict  # 触发条件
    recipients: List[str]  # 接收人列表
    template: str  # 消息模板
    is_active: bool = True
    send_time: Optional[str] = None  # 定时发送时间 (HH:MM)


@dataclass
class Message:
    """消息对象"""
    message_id: str
    message_type: MessageType
    priority: Priority
    recipients: List[str]
    title: str
    content: str
    data: Dict
    created_at: datetime
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed
    retry_count: int = 0


class WeChatService:
    """微信服务"""
    
    def __init__(self, config: WeChatConfig):
        self.config = config
        self.notification_rules: List[NotificationRule] = []
        self.message_queue: List[Message] = []
        self.sent_messages: List[Message] = []
        self._init_default_rules()
        
    def _init_default_rules(self):
        """初始化默认通知规则"""
        default_rules = [
            NotificationRule(
                rule_id="due_date_warning_3days",
                name="交期3天预警",
                message_type=MessageType.DUE_DATE_WARNING,
                trigger_conditions={"days_before_due": 3},
                recipients=["@all"],
                template="⚠️ 交期预警\n\n订单号：{{order_id}}\n产品：{{product_name}}\n交期：{{due_date}}\n剩余时间：{{remaining_days}}天\n\n请及时跟进生产进度！"
            ),
            NotificationRule(
                rule_id="due_date_warning_1day",
                name="交期1天预警",
                message_type=MessageType.DUE_DATE_WARNING,
                trigger_conditions={"days_before_due": 1},
                recipients=["@all"],
                template="🚨 紧急交期预警\n\n订单号：{{order_id}}\n产品：{{product_name}}\n交期：{{due_date}}\n剩余时间：{{remaining_days}}天\n\n请立即处理！"
            ),
            NotificationRule(
                rule_id="daily_progress_report",
                name="每日生产进度报告",
                message_type=MessageType.DAILY_REPORT,
                trigger_conditions={},
                recipients=["@all"],
                template="📊 每日生产报告\n\n日期：{{date}}\n完成订单：{{completed_orders}}个\n进行中订单：{{in_progress_orders}}个\n设备利用率：{{equipment_utilization}}%\n\n详细信息请查看系统。",
                send_time="18:00"
            ),
            NotificationRule(
                rule_id="schedule_notification",
                name="排产结果通知",
                message_type=MessageType.SCHEDULE_NOTIFICATION,
                trigger_conditions={},
                recipients=["@all"],
                template="📋 排产完成通知\n\n排产时间：{{schedule_time}}\n成功排产：{{scheduled_count}}个订单\n失败订单：{{failed_count}}个\n\n请查看详细排产计划。"
            )
        ]
        
        self.notification_rules.extend(default_rules)
        logger.info(f"初始化了 {len(default_rules)} 个默认通知规则")
    
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        # 检查token是否有效
        if (self.config.access_token and 
            self.config.token_expires_at and 
            datetime.now() < self.config.token_expires_at):
            return self.config.access_token
        
        # 获取新token
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.config.corp_id,
            "corpsecret": self.config.corp_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.config.access_token = data["access_token"]
                # token有效期2小时，提前10分钟刷新
                self.config.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 600)
                logger.info("微信访问令牌获取成功")
                return self.config.access_token
            else:
                logger.error(f"获取微信访问令牌失败: {data}")
                raise Exception(f"获取访问令牌失败: {data.get('errmsg')}")
                
        except Exception as e:
            logger.error(f"获取微信访问令牌异常: {e}")
            raise
    
    async def send_text_message(self, recipients: List[str], content: str, safe: int = 0) -> bool:
        """发送文本消息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            # 构建消息体
            data = {
                "touser": "|".join(recipients) if recipients != ["@all"] else "@all",
                "msgtype": "text",
                "agentid": self.config.agent_id,
                "text": {
                    "content": content
                },
                "safe": safe
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"微信消息发送成功: {recipients}")
                return True
            else:
                logger.error(f"微信消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送微信消息异常: {e}")
            return False
    
    async def send_markdown_message(self, recipients: List[str], content: str) -> bool:
        """发送Markdown消息"""
        try:
            access_token = await self.get_access_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
            
            data = {
                "touser": "|".join(recipients) if recipients != ["@all"] else "@all",
                "msgtype": "markdown",
                "agentid": self.config.agent_id,
                "markdown": {
                    "content": content
                }
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"微信Markdown消息发送成功: {recipients}")
                return True
            else:
                logger.error(f"微信Markdown消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送微信Markdown消息异常: {e}")
            return False
    
    def create_message(self, message_type: MessageType, priority: Priority, 
                      recipients: List[str], title: str, data: Dict) -> Message:
        """创建消息"""
        # 查找对应的通知规则
        rule = next((r for r in self.notification_rules 
                    if r.message_type == message_type and r.is_active), None)
        
        if not rule:
            logger.warning(f"未找到消息类型 {message_type} 的通知规则")
            content = f"{title}\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        else:
            # 使用模板渲染消息内容
            template = Template(rule.template)
            content = template.render(**data)
        
        message = Message(
            message_id=f"{message_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            message_type=message_type,
            priority=priority,
            recipients=recipients,
            title=title,
            content=content,
            data=data,
            created_at=datetime.now()
        )
        
        self.message_queue.append(message)
        logger.info(f"创建消息: {message.message_id}, 类型: {message_type.value}")
        return message
    
    async def send_message(self, message: Message) -> bool:
        """发送消息"""
        try:
            success = await self.send_text_message(message.recipients, message.content)
            
            if success:
                message.status = "sent"
                message.sent_at = datetime.now()
                self.sent_messages.append(message)
                # 从队列中移除
                if message in self.message_queue:
                    self.message_queue.remove(message)
            else:
                message.status = "failed"
                message.retry_count += 1
            
            return success
            
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            message.status = "failed"
            message.retry_count += 1
            return False
    
    async def process_message_queue(self):
        """处理消息队列"""
        if not self.message_queue:
            return
        
        # 按优先级排序
        sorted_messages = sorted(self.message_queue, key=lambda m: m.priority.value, reverse=True)
        
        for message in sorted_messages[:10]:  # 每次最多处理10条消息
            if message.retry_count >= 3:
                logger.error(f"消息 {message.message_id} 重试次数超限，放弃发送")
                message.status = "failed"
                self.message_queue.remove(message)
                continue
            
            await self.send_message(message)
            await asyncio.sleep(0.5)  # 避免频率限制
    
    def send_due_date_warning(self, order_data: Dict):
        """发送交期预警"""
        due_date = datetime.fromisoformat(order_data['due_date'])
        days_remaining = (due_date - datetime.now()).days
        
        if days_remaining <= 1:
            priority = Priority.URGENT
        elif days_remaining <= 3:
            priority = Priority.HIGH
        else:
            priority = Priority.NORMAL
        
        data = {
            'order_id': order_data['order_id'],
            'product_name': order_data['product_name'],
            'due_date': due_date.strftime('%Y-%m-%d'),
            'remaining_days': days_remaining
        }
        
        self.create_message(
            MessageType.DUE_DATE_WARNING,
            priority,
            ["@all"],
            f"交期预警 - 订单{order_data['order_id']}",
            data
        )
    
    def send_schedule_notification(self, schedule_result: Dict):
        """发送排产通知"""
        data = {
            'schedule_time': schedule_result['schedule_time'].strftime('%Y-%m-%d %H:%M'),
            'scheduled_count': schedule_result['scheduled_count'],
            'failed_count': schedule_result['failed_count']
        }
        
        self.create_message(
            MessageType.SCHEDULE_NOTIFICATION,
            Priority.NORMAL,
            ["@all"],
            "排产完成通知",
            data
        )
    
    def send_daily_report(self, report_data: Dict):
        """发送日报"""
        data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'completed_orders': report_data.get('completed_orders', 0),
            'in_progress_orders': report_data.get('in_progress_orders', 0),
            'equipment_utilization': report_data.get('equipment_utilization', 0)
        }
        
        self.create_message(
            MessageType.DAILY_REPORT,
            Priority.NORMAL,
            ["@all"],
            "每日生产报告",
            data
        )
    
    def send_exception_alert(self, exception_data: Dict):
        """发送异常告警"""
        self.create_message(
            MessageType.EXCEPTION_ALERT,
            Priority.URGENT,
            ["@all"],
            f"生产异常告警 - {exception_data.get('type', '未知异常')}",
            exception_data
        )
    
    def add_notification_rule(self, rule: NotificationRule):
        """添加通知规则"""
        self.notification_rules.append(rule)
        logger.info(f"添加通知规则: {rule.name}")
    
    def update_notification_rule(self, rule_id: str, updates: Dict) -> bool:
        """更新通知规则"""
        rule = next((r for r in self.notification_rules if r.rule_id == rule_id), None)
        if not rule:
            return False
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        logger.info(f"更新通知规则: {rule_id}")
        return True
    
    def get_message_statistics(self) -> Dict:
        """获取消息统计"""
        total_sent = len(self.sent_messages)
        pending_count = len([m for m in self.message_queue if m.status == "pending"])
        failed_count = len([m for m in self.message_queue if m.status == "failed"])
        
        return {
            'total_sent': total_sent,
            'pending_count': pending_count,
            'failed_count': failed_count,
            'success_rate': round((total_sent / (total_sent + failed_count) * 100) if (total_sent + failed_count) > 0 else 0, 2)
        }


# 创建全局微信服务实例（需要配置）
# wechat_service = WeChatService(WeChatConfig(
#     corp_id="your_corp_id",
#     corp_secret="your_corp_secret",
#     agent_id="your_agent_id"
# ))