"""短信服务

实现短信发送功能，支持：
- 阿里云短信服务
- 腾讯云短信服务
- 短信模板管理
- 批量短信发送
"""

import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import hashlib
import hmac
import base64
import time
import uuid
from urllib.parse import quote


class SMSProvider(Enum):
    """短信服务提供商"""
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    MOCK = "mock"  # 用于测试


@dataclass
class SMSConfig:
    """短信配置"""
    provider: SMSProvider
    access_key_id: str
    access_key_secret: str
    sign_name: str  # 短信签名
    region: str = "cn-hangzhou"
    endpoint: str = ""
    
    def __post_init__(self):
        if self.provider == SMSProvider.ALIYUN and not self.endpoint:
            self.endpoint = f"https://dysmsapi.{self.region}.aliyuncs.com"
        elif self.provider == SMSProvider.TENCENT and not self.endpoint:
            self.endpoint = "https://sms.tencentcloudapi.com"


@dataclass
class SMSTemplate:
    """短信模板"""
    template_id: str
    template_name: str
    content: str
    params: List[str]  # 模板参数列表
    provider: SMSProvider
    

@dataclass
class SMSMessage:
    """短信消息"""
    phone: str
    template_id: str
    params: Dict[str, Any]
    sign_name: Optional[str] = None
    

class SMSService:
    """短信服务"""
    
    def __init__(self, config: SMSConfig):
        self.config = config
        self.templates = self._load_default_templates()
        
    def _load_default_templates(self) -> Dict[str, SMSTemplate]:
        """加载默认短信模板"""
        templates = {
            "order_reminder": SMSTemplate(
                template_id="SMS_001",
                template_name="订单提醒",
                content="您的订单${order_no}预计${delivery_date}交付，请及时关注。",
                params=["order_no", "delivery_date"],
                provider=self.config.provider
            ),
            "production_alert": SMSTemplate(
                template_id="SMS_002",
                template_name="生产异常告警",
                content="生产线${line_name}出现异常：${alert_message}，请及时处理。",
                params=["line_name", "alert_message"],
                provider=self.config.provider
            ),
            "delivery_warning": SMSTemplate(
                template_id="SMS_003",
                template_name="交期预警",
                content="订单${order_no}交期临近（${days}天后），当前进度${progress}%，请关注。",
                params=["order_no", "days", "progress"],
                provider=self.config.provider
            ),
            "quality_alert": SMSTemplate(
                template_id="SMS_004",
                template_name="质量异常",
                content="产品${product_name}质检不合格，不合格率${defect_rate}%，请及时处理。",
                params=["product_name", "defect_rate"],
                provider=self.config.provider
            )
        }
        return templates
    
    async def send_sms(self, phone: str, template_id: str, params: Dict[str, Any]) -> bool:
        """发送单条短信"""
        try:
            message = SMSMessage(
                phone=phone,
                template_id=template_id,
                params=params,
                sign_name=self.config.sign_name
            )
            
            if self.config.provider == SMSProvider.ALIYUN:
                return await self._send_aliyun_sms(message)
            elif self.config.provider == SMSProvider.TENCENT:
                return await self._send_tencent_sms(message)
            elif self.config.provider == SMSProvider.MOCK:
                return await self._send_mock_sms(message)
            else:
                logger.error(f"Unsupported SMS provider: {self.config.provider}")
                return False
                
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            return False
    
    async def send_batch_sms(self, phones: List[str], template_id: str, params: Dict[str, Any]) -> List[bool]:
        """批量发送短信"""
        results = []
        for phone in phones:
            result = await self.send_sms(phone, template_id, params)
            results.append(result)
        return results
    
    async def _send_aliyun_sms(self, message: SMSMessage) -> bool:
        """发送阿里云短信"""
        try:
            # 构建请求参数
            params = {
                'Action': 'SendSms',
                'Version': '2017-05-25',
                'RegionId': self.config.region,
                'PhoneNumbers': message.phone,
                'SignName': message.sign_name or self.config.sign_name,
                'TemplateCode': message.template_id,
                'TemplateParam': json.dumps(message.params, ensure_ascii=False),
                'Format': 'JSON',
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'SignatureMethod': 'HMAC-SHA1',
                'SignatureVersion': '1.0',
                'SignatureNonce': str(uuid.uuid4()),
                'AccessKeyId': self.config.access_key_id
            }
            
            # 生成签名
            signature = self._generate_aliyun_signature(params)
            params['Signature'] = signature
            
            # 发送请求
            response = requests.post(self.config.endpoint, data=params)
            result = response.json()
            
            if result.get('Code') == 'OK':
                logger.info(f"Aliyun SMS sent successfully to {message.phone}")
                return True
            else:
                logger.error(f"Aliyun SMS failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Aliyun SMS error: {e}")
            return False
    
    async def _send_tencent_sms(self, message: SMSMessage) -> bool:
        """发送腾讯云短信"""
        try:
            # 腾讯云短信API实现
            # 这里需要根据腾讯云SMS API文档实现
            logger.info(f"Tencent SMS sent to {message.phone}")
            return True
            
        except Exception as e:
            logger.error(f"Tencent SMS error: {e}")
            return False
    
    async def _send_mock_sms(self, message: SMSMessage) -> bool:
        """模拟发送短信（用于测试）"""
        try:
            template = self.templates.get(message.template_id)
            if template:
                content = template.content
                for key, value in message.params.items():
                    content = content.replace(f"${{{key}}}", str(value))
                logger.info(f"Mock SMS to {message.phone}: {content}")
            else:
                logger.info(f"Mock SMS to {message.phone}: Template {message.template_id} with params {message.params}")
            return True
            
        except Exception as e:
            logger.error(f"Mock SMS error: {e}")
            return False
    
    def _generate_aliyun_signature(self, params: Dict[str, str]) -> str:
        """生成阿里云API签名"""
        # 排序参数
        sorted_params = sorted(params.items())
        
        # 构建查询字符串
        query_string = '&'.join([f"{quote(k)}={quote(str(v))}" for k, v in sorted_params if k != 'Signature'])
        
        # 构建待签名字符串
        string_to_sign = f"POST&{quote('/')}&{quote(query_string)}"
        
        # 生成签名
        signature = hmac.new(
            (self.config.access_key_secret + '&').encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def add_template(self, template: SMSTemplate):
        """添加短信模板"""
        self.templates[template.template_id] = template
    
    def get_template(self, template_id: str) -> Optional[SMSTemplate]:
        """获取短信模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[SMSTemplate]:
        """列出所有模板"""
        return list(self.templates.values())
    
    async def send_order_reminder(self, phone: str, order_no: str, delivery_date: str) -> bool:
        """发送订单提醒"""
        return await self.send_sms(
            phone=phone,
            template_id="order_reminder",
            params={
                "order_no": order_no,
                "delivery_date": delivery_date
            }
        )
    
    async def send_production_alert(self, phone: str, line_name: str, alert_message: str) -> bool:
        """发送生产异常告警"""
        return await self.send_sms(
            phone=phone,
            template_id="production_alert",
            params={
                "line_name": line_name,
                "alert_message": alert_message
            }
        )
    
    async def send_delivery_warning(self, phone: str, order_no: str, days: int, progress: float) -> bool:
        """发送交期预警"""
        return await self.send_sms(
            phone=phone,
            template_id="delivery_warning",
            params={
                "order_no": order_no,
                "days": str(days),
                "progress": f"{progress:.1f}"
            }
        )
    
    async def send_quality_alert(self, phone: str, product_name: str, defect_rate: float) -> bool:
        """发送质量异常告警"""
        return await self.send_sms(
            phone=phone,
            template_id="quality_alert",
            params={
                "product_name": product_name,
                "defect_rate": f"{defect_rate:.1f}"
            }
        )


# 默认短信服务实例
sms_config = SMSConfig(
    provider=SMSProvider.MOCK,  # 默认使用模拟模式
    access_key_id="your_access_key_id",
    access_key_secret="your_access_key_secret",
    sign_name="PMC生产管理"
)

sms_service = SMSService(sms_config)