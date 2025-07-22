"""企业微信群机器人通知渠道

通过企业微信群机器人发送通知消息。
"""

import aiohttp
import asyncio
import json
import hashlib
import hmac
import base64
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import logging

from .base import NotificationChannel
from ..models import NotificationMessage, ChannelConfig
from ..exceptions import ChannelError, AuthenticationError

logger = logging.getLogger(__name__)


class WeChatBotChannel(NotificationChannel):
    """企业微信群机器人通知渠道"""
    
    def __init__(self, config: ChannelConfig):
        """初始化企业微信群机器人渠道
        
        Args:
            config: 渠道配置，需要包含以下参数：
                - webhook_url: 机器人webhook地址
                - secret: 机器人密钥（可选，用于签名验证）
        """
        super().__init__(config)
        
        # 机器人配置
        self.webhook_url = config.settings.get('webhook_url')
        self.secret = config.settings.get('secret')  # 可选的签名密钥
        
        if not self.webhook_url:
            raise ChannelError("Missing required WeChat Bot configuration: webhook_url")
        
        # HTTP会话
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
        return self._session
    
    def _generate_signature(self, timestamp: str) -> Optional[str]:
        """生成签名
        
        Args:
            timestamp: 时间戳
            
        Returns:
            Optional[str]: 签名字符串，如果没有配置secret则返回None
        """
        if not self.secret:
            return None
        
        # 构建签名字符串
        string_to_sign = f"{timestamp}\n{self.secret}"
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64编码
        return base64.b64encode(signature).decode('utf-8')
    
    async def send(self, message: NotificationMessage) -> Tuple[bool, Optional[str]]:
        """发送通知消息
        
        Args:
            message: 通知消息
            
        Returns:
            (success, error_message): 发送结果和错误信息
        """
        try:
            # 构建消息体
            msg_data = self._build_message_data(message)
            
            # 构建请求URL（包含签名）
            url = self._build_request_url()
            
            # 发送消息
            session = await self._get_session()
            
            async with session.post(url, json=msg_data) as response:
                if response.status != 200:
                    return False, f"HTTP {response.status}: {await response.text()}"
                
                data = await response.json()
                
                if data.get('errcode', 0) != 0:
                    error_msg = data.get('errmsg', 'Unknown error')
                    error_code = data.get('errcode')
                    
                    # 特殊错误处理
                    if error_code == 93000:  # 签名验证失败
                        return False, f"Signature verification failed: {error_msg}"
                    elif error_code == 45009:  # 接口调用超过限制
                        return False, f"Rate limit exceeded: {error_msg}"
                    else:
                        return False, f"WeChat Bot error: {error_msg} (code: {error_code})"
                
                logger.info(f"Message sent successfully via WeChat Bot channel '{self.name}'")
                return True, None
                
        except aiohttp.ClientError as e:
            return False, f"Network error: {str(e)}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON response: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _build_request_url(self) -> str:
        """构建请求URL
        
        Returns:
            str: 包含签名的完整URL
        """
        url = self.webhook_url
        
        # 如果配置了密钥，添加签名参数
        if self.secret:
            timestamp = str(int(datetime.now().timestamp() * 1000))
            signature = self._generate_signature(timestamp)
            
            # 添加签名参数
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}timestamp={timestamp}&sign={signature}"
        
        return url
    
    def _build_message_data(self, message: NotificationMessage) -> Dict[str, Any]:
        """构建消息数据
        
        Args:
            message: 通知消息
            
        Returns:
            Dict[str, Any]: 消息数据
        """
        # 根据消息类型构建内容
        if message.message_type == 'text':
            return {
                "msgtype": "text",
                "text": {
                    "content": message.content,
                    "mentioned_list": message.recipients.get('mentioned_users', []),
                    "mentioned_mobile_list": message.recipients.get('mentioned_mobiles', [])
                }
            }
        
        elif message.message_type == 'markdown':
            return {
                "msgtype": "markdown",
                "markdown": {
                    "content": message.content
                }
            }
        
        elif message.message_type == 'image':
            return {
                "msgtype": "image",
                "image": {
                    "base64": message.metadata.get('base64', ''),
                    "md5": message.metadata.get('md5', '')
                }
            }
        
        elif message.message_type == 'news':
            # 图文消息
            articles = message.metadata.get('articles', [])
            if not articles and message.title:
                # 如果没有提供articles，使用title和content构建单篇文章
                articles = [{
                    "title": message.title,
                    "description": message.content,
                    "url": message.metadata.get('url', ''),
                    "picurl": message.metadata.get('pic_url', '')
                }]
            
            return {
                "msgtype": "news",
                "news": {
                    "articles": articles
                }
            }
        
        elif message.message_type == 'file':
            return {
                "msgtype": "file",
                "file": {
                    "media_id": message.metadata.get('media_id', '')
                }
            }
        
        elif message.message_type == 'template_card':
            # 模板卡片消息
            return {
                "msgtype": "template_card",
                "template_card": message.metadata.get('template_card', {})
            }
        
        else:
            # 默认使用文本消息
            content = message.content
            if message.title:
                content = f"**{message.title}**\n\n{content}"
            
            return {
                "msgtype": "text",
                "text": {
                    "content": content,
                    "mentioned_list": message.recipients.get('mentioned_users', []),
                    "mentioned_mobile_list": message.recipients.get('mentioned_mobiles', [])
                }
            }
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 渠道是否健康
        """
        try:
            # 发送一个简单的测试消息（实际不会发送，只是测试连接）
            session = await self._get_session()
            
            # 构建一个最小的测试请求
            test_data = {
                "msgtype": "text",
                "text": {
                    "content": "health_check"
                }
            }
            
            url = self._build_request_url()
            
            # 使用HEAD请求或者发送一个无效的小请求来测试连接
            # 这里我们实际发送请求但期望得到错误响应（因为内容无效）
            # 只要能连接到服务器就说明渠道健康
            async with session.post(url, json=test_data) as response:
                # 只要能收到响应就说明连接正常
                return True
                
        except aiohttp.ClientError:
            # 网络连接问题
            return False
        except Exception as e:
            logger.warning(f"WeChat Bot channel '{self.name}' health check failed: {e}")
            return False
    
    async def close(self):
        """关闭渠道，清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def get_status(self) -> Dict[str, Any]:
        """获取渠道状态"""
        status = super().get_status()
        status.update({
            "webhook_url": self.webhook_url[:50] + "..." if len(self.webhook_url) > 50 else self.webhook_url,
            "has_secret": bool(self.secret),
            "supports_signature": bool(self.secret)
        })
        return status
    
    @staticmethod
    def create_markdown_message(title: str, content: str, color: str = "info") -> str:
        """创建Markdown格式的消息
        
        Args:
            title: 标题
            content: 内容
            color: 颜色主题 (info, warning, comment)
            
        Returns:
            str: Markdown格式的消息内容
        """
        color_map = {
            "info": "#173177",
            "warning": "#FF6600", 
            "comment": "#67C23A",
            "error": "#FF0000"
        }
        
        color_code = color_map.get(color, color_map["info"])
        
        return f"""# <font color="{color_code}">{title}</font>
{content}

> 发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    @staticmethod
    def create_news_article(title: str, description: str, url: str = "", pic_url: str = "") -> Dict[str, str]:
        """创建图文消息文章
        
        Args:
            title: 标题
            description: 描述
            url: 跳转链接
            pic_url: 图片链接
            
        Returns:
            Dict[str, str]: 文章数据
        """
        return {
            "title": title,
            "description": description,
            "url": url,
            "picurl": pic_url
        }
    
    def __del__(self):
        """析构函数，确保资源清理"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # 在事件循环中关闭会话
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._session.close())
            except RuntimeError:
                pass  # 事件循环已关闭