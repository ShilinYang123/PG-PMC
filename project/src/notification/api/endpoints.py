"""API端点配置模块

定义各种通知服务的API端点。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class HTTPMethod(Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class APIEndpoint:
    """API端点配置"""
    url: str
    method: HTTPMethod
    description: str
    required_params: Optional[list] = None
    optional_params: Optional[list] = None
    headers: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.required_params is None:
            self.required_params = []
        if self.optional_params is None:
            self.optional_params = []
        if self.headers is None:
            self.headers = {}


class APIEndpoints:
    """API端点集合"""
    
    # 微信企业应用API端点
    WECHAT_API = {
        'get_token': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/gettoken',
            method=HTTPMethod.GET,
            description='获取访问令牌',
            required_params=['corpid', 'corpsecret']
        ),
        'send_message': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            method=HTTPMethod.POST,
            description='发送应用消息',
            required_params=['access_token'],
            headers={'Content-Type': 'application/json'}
        ),
        'get_user': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/user/get',
            method=HTTPMethod.GET,
            description='读取成员信息',
            required_params=['access_token', 'userid']
        ),
        'list_department': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/department/list',
            method=HTTPMethod.GET,
            description='获取部门列表',
            required_params=['access_token'],
            optional_params=['id']
        ),
        'upload_media': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/media/upload',
            method=HTTPMethod.POST,
            description='上传临时素材',
            required_params=['access_token', 'type']
        )
    }
    
    # 微信群机器人API端点
    WECHAT_BOT = {
        'send_message': APIEndpoint(
            url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
            method=HTTPMethod.POST,
            description='发送群机器人消息',
            required_params=['key'],
            headers={'Content-Type': 'application/json'}
        )
    }
    
    # 邮件服务API端点（示例）
    EMAIL_API = {
        'send_email': APIEndpoint(
            url='https://api.emailservice.com/v1/send',
            method=HTTPMethod.POST,
            description='发送邮件',
            required_params=['api_key', 'to', 'subject', 'content'],
            headers={'Content-Type': 'application/json'}
        ),
        'get_status': APIEndpoint(
            url='https://api.emailservice.com/v1/status/{message_id}',
            method=HTTPMethod.GET,
            description='查询邮件状态',
            required_params=['api_key', 'message_id']
        )
    }
    
    # 短信服务API端点（示例）
    SMS_API = {
        'send_sms': APIEndpoint(
            url='https://api.smsservice.com/v1/send',
            method=HTTPMethod.POST,
            description='发送短信',
            required_params=['api_key', 'phone', 'content'],
            headers={'Content-Type': 'application/json'}
        ),
        'query_balance': APIEndpoint(
            url='https://api.smsservice.com/v1/balance',
            method=HTTPMethod.GET,
            description='查询余额',
            required_params=['api_key']
        ),
        'get_template': APIEndpoint(
            url='https://api.smsservice.com/v1/template/{template_id}',
            method=HTTPMethod.GET,
            description='获取短信模板',
            required_params=['api_key', 'template_id']
        )
    }
    
    # 钉钉API端点（预留）
    DINGTALK_API = {
        'get_token': APIEndpoint(
            url='https://oapi.dingtalk.com/gettoken',
            method=HTTPMethod.GET,
            description='获取访问令牌',
            required_params=['appkey', 'appsecret']
        ),
        'send_message': APIEndpoint(
            url='https://oapi.dingtalk.com/robot/send',
            method=HTTPMethod.POST,
            description='发送群机器人消息',
            required_params=['access_token'],
            headers={'Content-Type': 'application/json'}
        )
    }
    
    # Slack API端点（预留）
    SLACK_API = {
        'send_message': APIEndpoint(
            url='https://slack.com/api/chat.postMessage',
            method=HTTPMethod.POST,
            description='发送消息',
            required_params=['token', 'channel', 'text'],
            headers={'Content-Type': 'application/json'}
        ),
        'upload_file': APIEndpoint(
            url='https://slack.com/api/files.upload',
            method=HTTPMethod.POST,
            description='上传文件',
            required_params=['token', 'channels']
        )
    }
    
    @classmethod
    def get_endpoint(cls, service: str, action: str) -> Optional[APIEndpoint]:
        """获取指定服务的API端点
        
        Args:
            service: 服务名称（如 'wechat_api', 'wechat_bot'）
            action: 操作名称（如 'send_message', 'get_token'）
            
        Returns:
            Optional[APIEndpoint]: API端点配置，不存在返回None
        """
        service_map = {
            'wechat_api': cls.WECHAT_API,
            'wechat_bot': cls.WECHAT_BOT,
            'email': cls.EMAIL_API,
            'sms': cls.SMS_API,
            'dingtalk': cls.DINGTALK_API,
            'slack': cls.SLACK_API
        }
        
        service_endpoints = service_map.get(service)
        if service_endpoints:
            return service_endpoints.get(action)
        return None
    
    @classmethod
    def list_services(cls) -> list:
        """列出所有支持的服务
        
        Returns:
            list: 服务名称列表
        """
        return ['wechat_api', 'wechat_bot', 'email', 'sms', 'dingtalk', 'slack']
    
    @classmethod
    def list_actions(cls, service: str) -> list:
        """列出指定服务的所有操作
        
        Args:
            service: 服务名称
            
        Returns:
            list: 操作名称列表
        """
        service_map = {
            'wechat_api': cls.WECHAT_API,
            'wechat_bot': cls.WECHAT_BOT,
            'email': cls.EMAIL_API,
            'sms': cls.SMS_API,
            'dingtalk': cls.DINGTALK_API,
            'slack': cls.SLACK_API
        }
        
        service_endpoints = service_map.get(service)
        if service_endpoints:
            return list(service_endpoints.keys())
        return []
    
    @classmethod
    def build_url(cls, endpoint: APIEndpoint, **kwargs) -> str:
        """构建完整的API URL
        
        Args:
            endpoint: API端点配置
            **kwargs: URL参数
            
        Returns:
            str: 完整的API URL
        """
        url = endpoint.url
        
        # 替换URL中的占位符
        for key, value in kwargs.items():
            placeholder = f'{{{key}}}'
            if placeholder in url:
                url = url.replace(placeholder, str(value))
        
        return url
    
    @classmethod
    def validate_params(cls, endpoint: APIEndpoint, params: Dict[str, Any]) -> tuple:
        """验证API参数
        
        Args:
            endpoint: API端点配置
            params: 请求参数
            
        Returns:
            tuple: (is_valid, missing_params, extra_params)
        """
        param_keys = set(params.keys())
        required_keys = set(endpoint.required_params)
        optional_keys = set(endpoint.optional_params)
        
        # 检查必需参数
        missing_params = required_keys - param_keys
        
        # 检查额外参数
        allowed_keys = required_keys | optional_keys
        extra_params = param_keys - allowed_keys
        
        is_valid = len(missing_params) == 0
        
        return is_valid, list(missing_params), list(extra_params)