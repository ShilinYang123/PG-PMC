"""企业微信API通知渠道

通过企业微信API发送通知消息。
"""

import aiohttp
import asyncio
import json
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from .base import NotificationChannel
from ..models import NotificationMessage, ChannelConfig, NotificationStatus
from ..exceptions import ChannelError, AuthenticationError, RateLimitError
from ..api import NotificationAPIClient, TokenAuth

logger = logging.getLogger(__name__)


class WeChatAPIChannel(NotificationChannel):
    """企业微信API通知渠道"""
    
    def __init__(self, config: ChannelConfig):
        """初始化企业微信API渠道
        
        Args:
            config: 渠道配置，需要包含以下参数：
                - corp_id: 企业ID
                - corp_secret: 应用密钥
                - agent_id: 应用ID
                - base_url: API基础URL（可选，默认为官方API）
        """
        super().__init__(config)
        
        # 企业微信配置
        self.corp_id = config.settings.get('corp_id')
        self.corp_secret = config.settings.get('corp_secret')
        self.agent_id = config.settings.get('agent_id')
        self.base_url = config.settings.get('base_url', 'https://qyapi.weixin.qq.com')
        
        if not all([self.corp_id, self.corp_secret, self.agent_id]):
            raise ChannelError("Missing required WeChat API configuration: corp_id, corp_secret, agent_id")
        
        # Access Token管理
        self._access_token = None
        self._token_expires_at = None
        self._token_lock = asyncio.Lock()
        
        # HTTP会话
        self._session = None
        
        # API端点
        self._token_url = f"{self.base_url}/cgi-bin/gettoken"
        self._send_url = f"{self.base_url}/cgi-bin/message/send"
        
        # 初始化API客户端
        self._api_client: Optional[NotificationAPIClient] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
        return self._session
    
    def _get_api_client(self) -> NotificationAPIClient:
        """获取API客户端"""
        if self._api_client is None:
            self._api_client = NotificationAPIClient(
                timeout=30,
                max_retries=3,
                retry_delay=1.0
            )
        return self._api_client
    
    async def _get_access_token(self) -> str:
        """获取访问令牌
        
        Returns:
            str: 访问令牌
            
        Raises:
            AuthenticationError: 获取令牌失败
        """
        async with self._token_lock:
            # 检查现有令牌是否有效
            if (self._access_token and 
                self._token_expires_at and 
                datetime.now() < self._token_expires_at - timedelta(minutes=5)):
                return self._access_token
            
            # 使用API客户端获取新令牌
            api_client = self._get_api_client()
            
            try:
                response = await api_client.get_wechat_token(
                    corp_id=self.corp_id,
                    corp_secret=self.corp_secret
                )
                
                if not response.is_success:
                    raise AuthenticationError(f"Failed to get access token: HTTP {response.status_code}")
                
                data = response.json()
                
                if data.get('errcode', 0) != 0:
                    error_msg = data.get('errmsg', 'Unknown error')
                    raise AuthenticationError(f"WeChat API error: {error_msg} (code: {data.get('errcode')})")
                
                self._access_token = data['access_token']
                expires_in = data.get('expires_in', 7200)  # 默认2小时
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"WeChat API access token refreshed for channel '{self.name}'")
                return self._access_token
                
            except Exception as e:
                if isinstance(e, AuthenticationError):
                    raise
                raise AuthenticationError(f"Error getting access token: {str(e)}")
    
    async def send(self, message: NotificationMessage) -> Tuple[bool, Optional[str]]:
        """发送通知消息
        
        Args:
            message: 通知消息
            
        Returns:
            (success, error_message): 发送结果和错误信息
        """
        try:
            # 获取访问令牌
            access_token = await self._get_access_token()
            
            # 使用API客户端发送消息
            api_client = self._get_api_client()
            
            response = await api_client.send_wechat_message(
                access_token=access_token,
                message=message
            )
            
            if not response.is_success:
                error_text = response.text()
                return False, f"HTTP {response.status_code}: {error_text}"
            
            data = response.json()
            
            if data.get('errcode', 0) != 0:
                error_msg = data.get('errmsg', 'Unknown error')
                error_code = data.get('errcode')
                
                # 特殊错误处理
                if error_code in [40014, 42001]:  # Token相关错误
                    # 清除缓存的token
                    self._access_token = None
                    self._token_expires_at = None
                    return False, f"Authentication error: {error_msg}"
                elif error_code == 45009:  # 接口调用超过限制
                    return False, f"Rate limit exceeded: {error_msg}"
                else:
                    return False, f"WeChat API error: {error_msg} (code: {error_code})"
            
            logger.info(f"Message sent successfully via WeChat API channel '{self.name}'")
            return True, None
            
        except AuthenticationError as e:
            return False, str(e)
        except aiohttp.ClientError as e:
            return False, f"Network error: {str(e)}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON response: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _build_message_data(self, message: NotificationMessage) -> Dict[str, Any]:
        """构建消息数据
        
        Args:
            message: 通知消息
            
        Returns:
            Dict[str, Any]: 消息数据
        """
        # 基础消息结构
        msg_data = {
            "touser": message.recipients.get('users', '@all'),  # 用户列表，默认全部
            "toparty": message.recipients.get('departments', ''),  # 部门列表
            "totag": message.recipients.get('tags', ''),  # 标签列表
            "agentid": self.agent_id,
            "safe": 0,  # 是否是保密消息
            "enable_id_trans": 0,  # 是否开启id转译
            "enable_duplicate_check": 0,  # 是否开启重复消息检查
        }
        
        # 根据消息类型构建内容
        if message.message_type == 'text':
            msg_data.update({
                "msgtype": "text",
                "text": {
                    "content": message.content
                }
            })
        elif message.message_type == 'markdown':
            msg_data.update({
                "msgtype": "markdown",
                "markdown": {
                    "content": message.content
                }
            })
        elif message.message_type == 'textcard':
            # 文本卡片消息
            msg_data.update({
                "msgtype": "textcard",
                "textcard": {
                    "title": message.title or "通知",
                    "description": message.content,
                    "url": message.metadata.get('url', ''),
                    "btntxt": message.metadata.get('button_text', '详情')
                }
            })
        else:
            # 默认使用文本消息
            content = message.content
            if message.title:
                content = f"**{message.title}**\n\n{content}"
            
            msg_data.update({
                "msgtype": "text",
                "text": {
                    "content": content
                }
            })
        
        return msg_data
    
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 渠道是否健康
        """
        try:
            # 尝试获取访问令牌
            await self._get_access_token()
            return True
        except Exception as e:
            logger.warning(f"WeChat API channel '{self.name}' health check failed: {e}")
            return False
    
    async def close(self):
        """关闭渠道，清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
        
        if self._api_client:
            await self._api_client.close()
        
        logger.info(f"WeChat API channel '{self.name}' closed")
    
    def get_status(self) -> Dict[str, Any]:
        """获取渠道状态"""
        status = super().get_status()
        status.update({
            "corp_id": self.corp_id,
            "agent_id": self.agent_id,
            "has_access_token": self._access_token is not None,
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "base_url": self.base_url
        })
        return status
    
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