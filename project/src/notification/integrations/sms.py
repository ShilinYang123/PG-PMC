"""短信集成模块

提供短信发送的集成功能。
"""

import aiohttp
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, List
import logging
import json

from ..exceptions import ChannelError, AuthenticationError
from ..models import NotificationMessage

logger = logging.getLogger(__name__)


class SMSIntegration:
    """短信集成类（预留实现）"""
    
    def __init__(self, api_key: str, api_secret: str, api_url: str,
                 sign_name: str = "系统通知"):
        """初始化短信集成
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            api_url: API接口地址
            sign_name: 短信签名
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url
        self.sign_name = sign_name
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成API签名
        
        Args:
            params: 请求参数
            
        Returns:
            str: 签名字符串
        """
        # 按键名排序
        sorted_params = sorted(params.items())
        
        # 构建签名字符串
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
        sign_str += f'&key={self.api_secret}'
        
        # 生成MD5签名
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
    
    async def send_sms(self, phone_numbers: List[str], content: str,
                      template_id: Optional[str] = None,
                      template_params: Optional[Dict[str, str]] = None) -> bool:
        """发送短信
        
        Args:
            phone_numbers: 手机号列表
            content: 短信内容
            template_id: 模板ID
            template_params: 模板参数
            
        Returns:
            bool: 发送是否成功
        """
        try:
            session = await self._get_session()
            
            # 构建请求参数
            params = {
                'api_key': self.api_key,
                'timestamp': str(int(time.time())),
                'sign_name': self.sign_name,
                'phone_numbers': ','.join(phone_numbers),
            }
            
            if template_id and template_params:
                params['template_id'] = template_id
                params['template_params'] = json.dumps(template_params)
            else:
                params['content'] = content
            
            # 生成签名
            params['signature'] = self._generate_signature(params)
            
            # 发送请求
            async with session.post(self.api_url, data=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('code') == 0:
                        logger.info(f"SMS sent successfully to {', '.join(phone_numbers)}")
                        return True
                    else:
                        logger.error(f"SMS API error: {result.get('message')}")
                        return False
                else:
                    logger.error(f"SMS API request failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    async def send_notification(self, message: NotificationMessage) -> bool:
        """发送通知消息
        
        Args:
            message: 通知消息对象
            
        Returns:
            bool: 发送是否成功
        """
        phone_numbers = message.recipients.get('phones', [])
        if not phone_numbers:
            logger.warning("No phone numbers specified in recipients")
            return False
        
        content = message.content
        
        # 检查是否使用模板
        template_id = message.metadata.get('template_id')
        template_params = message.metadata.get('template_params')
        
        return await self.send_sms(
            phone_numbers=phone_numbers,
            content=content,
            template_id=template_id,
            template_params=template_params
        )
    
    async def query_balance(self) -> Optional[float]:
        """查询账户余额
        
        Returns:
            Optional[float]: 账户余额，查询失败返回None
        """
        try:
            session = await self._get_session()
            
            params = {
                'api_key': self.api_key,
                'timestamp': str(int(time.time())),
                'action': 'query_balance'
            }
            
            params['signature'] = self._generate_signature(params)
            
            async with session.post(self.api_url, data=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('code') == 0:
                        return float(result.get('balance', 0))
                    else:
                        logger.error(f"Query balance error: {result.get('message')}")
                        return None
                else:
                    logger.error(f"Query balance request failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to query balance: {e}")
            return None
    
    def test_connection(self) -> bool:
        """测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 这里可以实现一个简单的API测试调用
            # 比如查询余额或发送测试短信
            logger.info("SMS API connection test - placeholder implementation")
            return True
            
        except Exception as e:
            logger.error(f"SMS API connection test failed: {e}")
            return False
    
    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()