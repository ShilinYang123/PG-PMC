"""通知系统API客户端

提供统一的API调用接口。
"""

import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlencode
import logging

from .auth import APIAuth
from .endpoints import APIEndpoints, APIEndpoint, HTTPMethod
from ..exceptions import ChannelError, AuthenticationError, RetryError
from ..models import NotificationMessage

logger = logging.getLogger(__name__)


class APIResponse:
    """API响应封装"""
    
    def __init__(self, status_code: int, data: Any, headers: Dict[str, str], 
                 raw_response: Optional[str] = None):
        self.status_code = status_code
        self.data = data
        self.headers = headers
        self.raw_response = raw_response
    
    @property
    def is_success(self) -> bool:
        """是否成功响应"""
        return 200 <= self.status_code < 300
    
    @property
    def is_client_error(self) -> bool:
        """是否客户端错误"""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """是否服务器错误"""
        return 500 <= self.status_code < 600
    
    def json(self) -> Any:
        """获取JSON数据"""
        return self.data
    
    def text(self) -> str:
        """获取文本数据"""
        return self.raw_response or str(self.data)


class NotificationAPIClient:
    """通知系统API客户端"""
    
    def __init__(self, auth: Optional[APIAuth] = None, 
                 timeout: int = 30, max_retries: int = 3,
                 retry_delay: float = 1.0):
        """初始化API客户端
        
        Args:
            auth: API认证对象
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _make_request(self, method: HTTPMethod, url: str, 
                           params: Optional[Dict[str, Any]] = None,
                           data: Optional[Dict[str, Any]] = None,
                           headers: Optional[Dict[str, str]] = None,
                           files: Optional[Dict[str, Any]] = None) -> APIResponse:
        """发起HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            params: URL参数
            data: 请求体数据
            headers: 请求头
            files: 文件数据
            
        Returns:
            APIResponse: API响应对象
        """
        session = await self._get_session()
        
        # 合并请求头
        request_headers = {}
        if self.auth:
            request_headers.update(self.auth.get_headers())
        if headers:
            request_headers.update(headers)
        
        # 处理认证签名
        if self.auth and params:
            params = self.auth.sign_request(method.value, url, params)
        
        # 构建请求参数
        kwargs = {
            'headers': request_headers
        }
        
        if params:
            if method == HTTPMethod.GET:
                # GET请求将参数添加到URL
                url += '?' + urlencode(params)
            else:
                kwargs['params'] = params
        
        if data:
            if 'Content-Type' in request_headers and 'application/json' in request_headers['Content-Type']:
                kwargs['json'] = data
            else:
                kwargs['data'] = data
        
        if files:
            # 处理文件上传
            form_data = aiohttp.FormData()
            for key, value in files.items():
                if isinstance(value, tuple):
                    # (filename, file_object, content_type)
                    form_data.add_field(key, value[1], filename=value[0], content_type=value[2])
                else:
                    form_data.add_field(key, value)
            kwargs['data'] = form_data
        
        # 发起请求
        async with session.request(method.value, url, **kwargs) as response:
            # 读取响应数据
            raw_text = await response.text()
            
            try:
                response_data = await response.json()
            except (json.JSONDecodeError, aiohttp.ContentTypeError):
                response_data = raw_text
            
            return APIResponse(
                status_code=response.status,
                data=response_data,
                headers=dict(response.headers),
                raw_response=raw_text
            )
    
    async def request_with_retry(self, method: HTTPMethod, url: str,
                                **kwargs) -> APIResponse:
        """带重试的请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            APIResponse: API响应对象
            
        Raises:
            RetryError: 重试次数耗尽
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._make_request(method, url, **kwargs)
                
                # 检查是否需要重试
                if response.is_success or response.is_client_error:
                    return response
                
                # 服务器错误，可以重试
                if attempt < self.max_retries:
                    logger.warning(f"Request failed with status {response.status_code}, retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                    continue
                
                return response
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Request failed with error {e}, retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                break
        
        raise RetryError(f"Request failed after {self.max_retries} retries", last_exception)
    
    async def call_api(self, service: str, action: str, 
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None,
                      files: Optional[Dict[str, Any]] = None,
                      **url_params) -> APIResponse:
        """调用API
        
        Args:
            service: 服务名称
            action: 操作名称
            params: URL参数
            data: 请求体数据
            files: 文件数据
            **url_params: URL占位符参数
            
        Returns:
            APIResponse: API响应对象
            
        Raises:
            ValueError: 无效的服务或操作
            ChannelError: API调用失败
        """
        # 获取API端点配置
        endpoint = APIEndpoints.get_endpoint(service, action)
        if not endpoint:
            raise ValueError(f"Unknown service '{service}' or action '{action}'")
        
        # 验证参数
        if params:
            is_valid, missing_params, extra_params = APIEndpoints.validate_params(endpoint, params)
            if not is_valid:
                raise ValueError(f"Missing required parameters: {missing_params}")
            if extra_params:
                logger.warning(f"Extra parameters will be ignored: {extra_params}")
        
        # 构建URL
        url = APIEndpoints.build_url(endpoint, **url_params)
        
        try:
            response = await self.request_with_retry(
                method=endpoint.method,
                url=url,
                params=params,
                data=data,
                headers=endpoint.headers,
                files=files
            )
            
            if not response.is_success:
                error_msg = f"API call failed: {response.status_code}"
                if response.data:
                    error_msg += f" - {response.data}"
                raise ChannelError(error_msg)
            
            return response
            
        except RetryError as e:
            raise ChannelError(f"API call failed after retries: {e}")
    
    async def send_wechat_message(self, access_token: str, 
                                 message: NotificationMessage) -> APIResponse:
        """发送微信消息
        
        Args:
            access_token: 访问令牌
            message: 通知消息
            
        Returns:
            APIResponse: API响应对象
        """
        # 构建消息数据
        message_data = {
            'touser': '|'.join(message.recipients.get('users', [])),
            'toparty': '|'.join(message.recipients.get('departments', [])),
            'totag': '|'.join(message.recipients.get('tags', [])),
            'msgtype': message.message_type or 'text',
            'agentid': message.metadata.get('agent_id', 1000001)
        }
        
        # 根据消息类型添加内容
        if message.message_type == 'text':
            message_data['text'] = {'content': message.content}
        elif message.message_type == 'markdown':
            message_data['markdown'] = {'content': message.content}
        elif message.message_type == 'textcard':
            message_data['textcard'] = {
                'title': message.title or '通知',
                'description': message.content,
                'url': message.metadata.get('url', ''),
                'btntxt': message.metadata.get('btn_text', '详情')
            }
        
        return await self.call_api(
            service='wechat_api',
            action='send_message',
            params={'access_token': access_token},
            data=message_data
        )
    
    async def send_wechat_bot_message(self, webhook_key: str,
                                     message: NotificationMessage) -> APIResponse:
        """发送微信群机器人消息
        
        Args:
            webhook_key: Webhook密钥
            message: 通知消息
            
        Returns:
            APIResponse: API响应对象
        """
        # 构建消息数据
        message_data = {
            'msgtype': message.message_type or 'text'
        }
        
        if message.message_type == 'text':
            message_data['text'] = {
                'content': message.content,
                'mentioned_list': message.recipients.get('mentioned_users', []),
                'mentioned_mobile_list': message.recipients.get('mentioned_mobiles', [])
            }
        elif message.message_type == 'markdown':
            message_data['markdown'] = {
                'content': message.content
            }
        
        return await self.call_api(
            service='wechat_bot',
            action='send_message',
            params={'key': webhook_key},
            data=message_data
        )
    
    async def get_wechat_token(self, corp_id: str, corp_secret: str) -> APIResponse:
        """获取微信访问令牌
        
        Args:
            corp_id: 企业ID
            corp_secret: 企业密钥
            
        Returns:
            APIResponse: API响应对象
        """
        return await self.call_api(
            service='wechat_api',
            action='get_token',
            params={
                'corpid': corp_id,
                'corpsecret': corp_secret
            }
        )
    
    async def close(self):
        """关闭客户端"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局API客户端实例
_global_client: Optional[NotificationAPIClient] = None


def get_api_client(auth: Optional[APIAuth] = None) -> NotificationAPIClient:
    """获取全局API客户端实例
    
    Args:
        auth: API认证对象
        
    Returns:
        NotificationAPIClient: API客户端实例
    """
    global _global_client
    
    if _global_client is None:
        _global_client = NotificationAPIClient(auth=auth)
    elif auth and _global_client.auth != auth:
        # 如果认证对象不同，创建新的客户端
        _global_client = NotificationAPIClient(auth=auth)
    
    return _global_client


async def close_global_client():
    """关闭全局API客户端"""
    global _global_client
    
    if _global_client:
        await _global_client.close()
        _global_client = None