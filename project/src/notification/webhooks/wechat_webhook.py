"""微信Webhook处理器

处理企业微信API和群机器人的回调消息。
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .base import BaseWebhookHandler, WebhookEvent, WebhookEventType
from ..exceptions import WebhookError

logger = logging.getLogger(__name__)


class WeChatWebhookHandler(BaseWebhookHandler):
    """微信Webhook处理器"""
    
    def __init__(self, secret: Optional[str] = None, token: Optional[str] = None, 
                 encoding_aes_key: Optional[str] = None):
        """初始化微信Webhook处理器
        
        Args:
            secret: 群机器人密钥
            token: 企业微信应用Token
            encoding_aes_key: 企业微信应用EncodingAESKey
        """
        super().__init__(secret)
        self.token = token
        self.encoding_aes_key = encoding_aes_key
    
    async def handle_request(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """处理webhook请求
        
        Args:
            headers: HTTP请求头
            body: 请求体
            
        Returns:
            响应数据
        """
        try:
            # 验证签名
            if not self.verify_signature(headers, body):
                raise WebhookError("Invalid signature")
            
            # 解析请求数据
            content_type = headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                # JSON格式（群机器人回调）
                data = json.loads(body.decode('utf-8'))
                event = self.parse_bot_event(data)
            elif 'application/xml' in content_type or 'text/xml' in content_type:
                # XML格式（企业微信API回调）
                data = self._parse_xml(body)
                event = self.parse_api_event(data)
            else:
                # 尝试解析为JSON
                try:
                    data = json.loads(body.decode('utf-8'))
                    event = self.parse_bot_event(data)
                except json.JSONDecodeError:
                    raise WebhookError(f"Unsupported content type: {content_type}")
            
            # 触发事件处理器
            if event:
                await self._trigger_event_handlers(event)
                logger.info(f"Processed webhook event: {event.event_type.value}")
            
            return {'status': 'success', 'message': 'Event processed'}
            
        except Exception as e:
            logger.error(f"Error handling webhook request: {e}")
            raise WebhookError(f"Failed to process webhook: {str(e)}")
    
    def verify_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        """验证请求签名
        
        Args:
            headers: HTTP请求头
            body: 请求体
            
        Returns:
            签名是否有效
        """
        # 群机器人签名验证
        if 'x-wechatwork-signature' in headers:
            signature = headers['x-wechatwork-signature']
            timestamp = headers.get('x-wechatwork-timestamp', '')
            nonce = headers.get('x-wechatwork-nonce', '')
            
            if self.secret:
                # 构建签名字符串
                sign_string = f"{self.token}{timestamp}{nonce}{body.decode('utf-8')}"
                return self._verify_hmac_signature(signature, sign_string.encode('utf-8'), 'sha1')
        
        # 企业微信API签名验证
        elif 'signature' in headers:
            signature = headers['signature']
            timestamp = headers.get('timestamp', '')
            nonce = headers.get('nonce', '')
            
            if self.token:
                # 构建签名字符串
                sign_list = [self.token, timestamp, nonce]
                sign_list.sort()
                sign_string = ''.join(sign_list)
                
                import hashlib
                expected_signature = hashlib.sha1(sign_string.encode('utf-8')).hexdigest()
                return signature == expected_signature
        
        # 如果没有配置验证信息，则跳过验证
        return not self.secret and not self.token
    
    def parse_event(self, data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """解析事件数据（通用接口）
        
        Args:
            data: 原始事件数据
            
        Returns:
            解析后的事件对象
        """
        # 根据数据结构判断事件类型
        if 'msgtype' in data or 'chatid' in data:
            return self.parse_bot_event(data)
        else:
            return self.parse_api_event(data)
    
    def parse_bot_event(self, data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """解析群机器人事件
        
        Args:
            data: 机器人事件数据
            
        Returns:
            解析后的事件对象
        """
        try:
            # 群机器人主要接收用户交互事件
            event_type = WebhookEventType.USER_INTERACTION
            
            # 提取关键信息
            message_id = data.get('msgid')
            user_id = data.get('from', {}).get('userid') if isinstance(data.get('from'), dict) else None
            
            return WebhookEvent(
                event_type=event_type,
                timestamp=datetime.now(),
                source='wechat_bot',
                data=data,
                message_id=message_id,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error parsing bot event: {e}")
            return None
    
    def parse_api_event(self, data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """解析企业微信API事件
        
        Args:
            data: API事件数据
            
        Returns:
            解析后的事件对象
        """
        try:
            # 根据事件类型映射
            event_type_mapping = {
                'send_msg_result': WebhookEventType.MESSAGE_SENT,
                'msg_audit': WebhookEventType.MESSAGE_DELIVERED,
                'user_add': WebhookEventType.SYSTEM_EVENT,
                'user_modify': WebhookEventType.SYSTEM_EVENT,
                'user_delete': WebhookEventType.SYSTEM_EVENT,
                'party_create': WebhookEventType.SYSTEM_EVENT,
                'party_modify': WebhookEventType.SYSTEM_EVENT,
                'party_delete': WebhookEventType.SYSTEM_EVENT,
            }
            
            msg_type = data.get('MsgType', data.get('msgtype', 'unknown'))
            event_type = event_type_mapping.get(msg_type, WebhookEventType.UNKNOWN)
            
            # 提取关键信息
            message_id = data.get('MsgId', data.get('msgid'))
            user_id = data.get('FromUserName', data.get('userid'))
            
            return WebhookEvent(
                event_type=event_type,
                timestamp=datetime.now(),
                source='wechat_api',
                data=data,
                message_id=str(message_id) if message_id else None,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error parsing API event: {e}")
            return None
    
    def _parse_xml(self, xml_data: bytes) -> Dict[str, Any]:
        """解析XML数据
        
        Args:
            xml_data: XML字节数据
            
        Returns:
            解析后的字典数据
        """
        try:
            root = ET.fromstring(xml_data.decode('utf-8'))
            result = {}
            
            for child in root:
                if child.text:
                    # 尝试转换数字
                    try:
                        if '.' in child.text:
                            result[child.tag] = float(child.text)
                        else:
                            result[child.tag] = int(child.text)
                    except ValueError:
                        result[child.tag] = child.text
                else:
                    result[child.tag] = child.text
            
            return result
            
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            raise WebhookError(f"Invalid XML format: {str(e)}")
    
    def create_response(self, success: bool = True, message: str = "success") -> Dict[str, Any]:
        """创建响应数据
        
        Args:
            success: 是否成功
            message: 响应消息
            
        Returns:
            响应数据
        """
        return {
            'errcode': 0 if success else -1,
            'errmsg': message
        }


class WeChatCallbackManager:
    """微信回调管理器"""
    
    def __init__(self):
        self.handlers: Dict[str, WeChatWebhookHandler] = {}
        self._global_handlers: Dict[WebhookEventType, list] = {
            event_type: [] for event_type in WebhookEventType
        }
    
    def add_handler(self, name: str, handler: WeChatWebhookHandler):
        """添加处理器
        
        Args:
            name: 处理器名称
            handler: 处理器实例
        """
        self.handlers[name] = handler
    
    def get_handler(self, name: str) -> Optional[WeChatWebhookHandler]:
        """获取处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            处理器实例
        """
        return self.handlers.get(name)
    
    def add_global_event_handler(self, event_type: WebhookEventType, handler):
        """添加全局事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._global_handlers[event_type].append(handler)
        
        # 为所有现有处理器添加事件处理器
        for webhook_handler in self.handlers.values():
            webhook_handler.add_event_handler(event_type, handler)
    
    async def handle_webhook(self, handler_name: str, headers: Dict[str, str], 
                           body: bytes) -> Dict[str, Any]:
        """处理webhook请求
        
        Args:
            handler_name: 处理器名称
            headers: HTTP请求头
            body: 请求体
            
        Returns:
            响应数据
        """
        handler = self.get_handler(handler_name)
        if not handler:
            raise WebhookError(f"Handler '{handler_name}' not found")
        
        return await handler.handle_request(headers, body)


# 全局回调管理器实例
_callback_manager = None

def get_callback_manager() -> WeChatCallbackManager:
    """获取全局回调管理器"""
    global _callback_manager
    if _callback_manager is None:
        _callback_manager = WeChatCallbackManager()
    return _callback_manager