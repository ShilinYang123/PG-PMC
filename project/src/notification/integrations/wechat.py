"""微信集成模块

提供企业微信API和群机器人的高级集成功能。
"""

import aiohttp
import asyncio
import json
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from ..exceptions import (
    NotificationError, ChannelError, AuthenticationError, 
    RateLimitError, MessageValidationError
)
from ..models import NotificationMessage, ChannelConfig
from ..utils import generate_message_id, format_timestamp

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    NEWS = "news"
    FILE = "file"
    TEXTCARD = "textcard"
    TEMPLATE_CARD = "template_card"


@dataclass
class WeChatUser:
    """微信用户信息"""
    userid: str
    name: Optional[str] = None
    department: Optional[List[int]] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'userid': self.userid,
            'name': self.name,
            'department': self.department,
            'mobile': self.mobile,
            'email': self.email
        }


@dataclass
class WeChatDepartment:
    """微信部门信息"""
    id: int
    name: str
    parentid: int = 1
    order: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'parentid': self.parentid,
            'order': self.order
        }


class WeChatAPIClient:
    """企业微信API客户端"""
    
    def __init__(self, corp_id: str, corp_secret: str, agent_id: str, 
                 base_url: str = "https://qyapi.weixin.qq.com"):
        """初始化API客户端
        
        Args:
            corp_id: 企业ID
            corp_secret: 应用密钥
            agent_id: 应用ID
            base_url: API基础URL
        """
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.base_url = base_url
        
        # Token管理
        self._access_token = None
        self._token_expires_at = None
        self._token_lock = asyncio.Lock()
        
        # HTTP会话
        self._session = None
        
        # API端点
        self._endpoints = {
            'token': f"{base_url}/cgi-bin/gettoken",
            'send_message': f"{base_url}/cgi-bin/message/send",
            'get_user': f"{base_url}/cgi-bin/user/get",
            'list_users': f"{base_url}/cgi-bin/user/list",
            'get_department': f"{base_url}/cgi-bin/department/get",
            'list_departments': f"{base_url}/cgi-bin/department/list",
            'upload_media': f"{base_url}/cgi-bin/media/upload",
            'get_media': f"{base_url}/cgi-bin/media/get"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
        return self._session
    
    async def get_access_token(self) -> str:
        """获取访问令牌"""
        async with self._token_lock:
            # 检查现有令牌是否有效
            if (self._access_token and 
                self._token_expires_at and 
                datetime.now() < self._token_expires_at - timedelta(minutes=5)):
                return self._access_token
            
            # 获取新令牌
            session = await self._get_session()
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            
            try:
                async with session.get(self._endpoints['token'], params=params) as response:
                    if response.status != 200:
                        raise AuthenticationError(f"HTTP {response.status}: {await response.text()}")
                    
                    data = await response.json()
                    
                    if data.get('errcode', 0) != 0:
                        error_msg = data.get('errmsg', 'Unknown error')
                        raise AuthenticationError(f"WeChat API error: {error_msg} (code: {data.get('errcode')})")
                    
                    self._access_token = data['access_token']
                    expires_in = data.get('expires_in', 7200)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info("WeChat API access token refreshed")
                    return self._access_token
                    
            except aiohttp.ClientError as e:
                raise AuthenticationError(f"Network error while getting access token: {str(e)}")
    
    async def _api_request(self, method: str, endpoint: str, 
                          params: Optional[Dict] = None, 
                          data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送API请求"""
        access_token = await self.get_access_token()
        session = await self._get_session()
        
        # 添加access_token到参数
        if params is None:
            params = {}
        params['access_token'] = access_token
        
        url = self._endpoints.get(endpoint, endpoint)
        
        try:
            if method.upper() == 'GET':
                async with session.get(url, params=params) as response:
                    result = await response.json()
            else:
                async with session.request(method, url, params=params, json=data) as response:
                    result = await response.json()
            
            # 检查API错误
            if result.get('errcode', 0) != 0:
                error_msg = result.get('errmsg', 'Unknown error')
                error_code = result.get('errcode')
                
                if error_code in [40014, 42001]:  # Token相关错误
                    self._access_token = None
                    self._token_expires_at = None
                    raise AuthenticationError(f"Token error: {error_msg}")
                elif error_code == 45009:
                    raise RateLimitError(f"Rate limit exceeded: {error_msg}")
                else:
                    raise ChannelError(f"WeChat API error: {error_msg} (code: {error_code})")
            
            return result
            
        except aiohttp.ClientError as e:
            raise ChannelError(f"Network error: {str(e)}")
    
    async def send_message(self, message: NotificationMessage) -> bool:
        """发送消息"""
        msg_data = self._build_message_data(message)
        result = await self._api_request('POST', 'send_message', data=msg_data)
        return result.get('errcode', 0) == 0
    
    def _build_message_data(self, message: NotificationMessage) -> Dict[str, Any]:
        """构建消息数据"""
        msg_data = {
            "touser": message.recipients.get('users', '@all'),
            "toparty": message.recipients.get('departments', ''),
            "totag": message.recipients.get('tags', ''),
            "agentid": self.agent_id,
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
        }
        
        if message.message_type == 'text':
            msg_data.update({
                "msgtype": "text",
                "text": {"content": message.content}
            })
        elif message.message_type == 'markdown':
            msg_data.update({
                "msgtype": "markdown",
                "markdown": {"content": message.content}
            })
        elif message.message_type == 'textcard':
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
            # 默认文本消息
            content = message.content
            if message.title:
                content = f"**{message.title}**\n\n{content}"
            msg_data.update({
                "msgtype": "text",
                "text": {"content": content}
            })
        
        return msg_data
    
    async def get_user(self, userid: str) -> Optional[WeChatUser]:
        """获取用户信息"""
        try:
            result = await self._api_request('GET', 'get_user', params={'userid': userid})
            if 'userid' in result:
                return WeChatUser(
                    userid=result['userid'],
                    name=result.get('name'),
                    department=result.get('department'),
                    mobile=result.get('mobile'),
                    email=result.get('email')
                )
        except ChannelError:
            pass
        return None
    
    async def list_users(self, department_id: int = 1, fetch_child: bool = False) -> List[WeChatUser]:
        """获取部门用户列表"""
        params = {
            'department_id': department_id,
            'fetch_child': 1 if fetch_child else 0
        }
        
        result = await self._api_request('GET', 'list_users', params=params)
        users = []
        
        for user_data in result.get('userlist', []):
            users.append(WeChatUser(
                userid=user_data['userid'],
                name=user_data.get('name'),
                department=user_data.get('department'),
                mobile=user_data.get('mobile'),
                email=user_data.get('email')
            ))
        
        return users
    
    async def list_departments(self, department_id: Optional[int] = None) -> List[WeChatDepartment]:
        """获取部门列表"""
        params = {}
        if department_id is not None:
            params['id'] = department_id
        
        result = await self._api_request('GET', 'list_departments', params=params)
        departments = []
        
        for dept_data in result.get('department', []):
            departments.append(WeChatDepartment(
                id=dept_data['id'],
                name=dept_data['name'],
                parentid=dept_data.get('parentid', 1),
                order=dept_data.get('order', 1)
            ))
        
        return departments
    
    async def close(self):
        """关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()


class WeChatBotClient:
    """企业微信群机器人客户端"""
    
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """初始化机器人客户端
        
        Args:
            webhook_url: 机器人webhook地址
            secret: 机器人密钥（可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
        return self._session
    
    def _generate_signature(self, timestamp: str) -> Optional[str]:
        """生成签名"""
        if not self.secret:
            return None
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        signature = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _build_request_url(self) -> str:
        """构建请求URL"""
        url = self.webhook_url
        
        if self.secret:
            timestamp = str(int(datetime.now().timestamp() * 1000))
            signature = self._generate_signature(timestamp)
            
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}timestamp={timestamp}&sign={signature}"
        
        return url
    
    async def send_text(self, content: str, mentioned_list: Optional[List[str]] = None,
                       mentioned_mobile_list: Optional[List[str]] = None) -> bool:
        """发送文本消息"""
        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or []
            }
        }
        return await self._send_message(data)
    
    async def send_markdown(self, content: str) -> bool:
        """发送Markdown消息"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        return await self._send_message(data)
    
    async def send_news(self, articles: List[Dict[str, str]]) -> bool:
        """发送图文消息"""
        data = {
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }
        return await self._send_message(data)
    
    async def send_image(self, base64_data: str, md5_hash: str) -> bool:
        """发送图片消息"""
        data = {
            "msgtype": "image",
            "image": {
                "base64": base64_data,
                "md5": md5_hash
            }
        }
        return await self._send_message(data)
    
    async def _send_message(self, data: Dict[str, Any]) -> bool:
        """发送消息"""
        session = await self._get_session()
        url = self._build_request_url()
        
        try:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status}: {await response.text()}")
                    return False
                
                result = await response.json()
                
                if result.get('errcode', 0) != 0:
                    error_msg = result.get('errmsg', 'Unknown error')
                    logger.error(f"WeChat Bot error: {error_msg}")
                    return False
                
                return True
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
    
    async def close(self):
        """关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()


class WeChatIntegration:
    """微信集成管理器"""
    
    def __init__(self):
        self.api_clients: Dict[str, WeChatAPIClient] = {}
        self.bot_clients: Dict[str, WeChatBotClient] = {}
    
    def add_api_client(self, name: str, corp_id: str, corp_secret: str, agent_id: str) -> WeChatAPIClient:
        """添加API客户端"""
        client = WeChatAPIClient(corp_id, corp_secret, agent_id)
        self.api_clients[name] = client
        return client
    
    def add_bot_client(self, name: str, webhook_url: str, secret: Optional[str] = None) -> WeChatBotClient:
        """添加机器人客户端"""
        client = WeChatBotClient(webhook_url, secret)
        self.bot_clients[name] = client
        return client
    
    def get_api_client(self, name: str) -> Optional[WeChatAPIClient]:
        """获取API客户端"""
        return self.api_clients.get(name)
    
    def get_bot_client(self, name: str) -> Optional[WeChatBotClient]:
        """获取机器人客户端"""
        return self.bot_clients.get(name)
    
    async def send_to_all_channels(self, message: str, title: Optional[str] = None) -> Dict[str, bool]:
        """向所有渠道发送消息"""
        results = {}
        
        # 发送到API渠道
        for name, client in self.api_clients.items():
            try:
                msg = NotificationMessage(
                    id=generate_message_id(),
                    title=title,
                    content=message,
                    message_type='text',
                    recipients={'users': '@all'}
                )
                results[f"api_{name}"] = await client.send_message(msg)
            except Exception as e:
                logger.error(f"Failed to send via API client {name}: {e}")
                results[f"api_{name}"] = False
        
        # 发送到机器人渠道
        for name, client in self.bot_clients.items():
            try:
                content = message
                if title:
                    content = f"**{title}**\n\n{message}"
                results[f"bot_{name}"] = await client.send_text(content)
            except Exception as e:
                logger.error(f"Failed to send via Bot client {name}: {e}")
                results[f"bot_{name}"] = False
        
        return results
    
    async def close_all(self):
        """关闭所有客户端"""
        for client in self.api_clients.values():
            await client.close()
        
        for client in self.bot_clients.values():
            await client.close()
        
        self.api_clients.clear()
        self.bot_clients.clear()


# 全局集成实例
_wechat_integration = None

def get_wechat_integration() -> WeChatIntegration:
    """获取全局微信集成实例"""
    global _wechat_integration
    if _wechat_integration is None:
        _wechat_integration = WeChatIntegration()
    return _wechat_integration