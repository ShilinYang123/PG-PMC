"""API认证模块

提供各种API认证方式的实现。
"""

import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import jwt
from datetime import datetime, timedelta


class APIAuth(ABC):
    """API认证基类"""
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """获取认证头信息
        
        Returns:
            Dict[str, str]: 认证头字典
        """
        pass
    
    @abstractmethod
    def sign_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """签名请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 签名后的参数
        """
        pass


class TokenAuth(APIAuth):
    """Token认证"""
    
    def __init__(self, token: str, token_type: str = "Bearer"):
        """初始化Token认证
        
        Args:
            token: 访问令牌
            token_type: 令牌类型
        """
        self.token = token
        self.token_type = token_type
    
    def get_headers(self) -> Dict[str, str]:
        """获取认证头信息"""
        return {
            'Authorization': f'{self.token_type} {self.token}'
        }
    
    def sign_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Token认证不需要额外签名"""
        return params or {}


class KeyAuth(APIAuth):
    """API Key认证"""
    
    def __init__(self, api_key: str, api_secret: str, key_name: str = "api_key"):
        """初始化API Key认证
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            key_name: 密钥参数名
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.key_name = key_name
    
    def get_headers(self) -> Dict[str, str]:
        """获取认证头信息"""
        return {
            'X-API-Key': self.api_key
        }
    
    def sign_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用HMAC-SHA256签名请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            params: 请求参数
            
        Returns:
            Dict[str, Any]: 签名后的参数
        """
        if params is None:
            params = {}
        
        # 添加时间戳
        timestamp = str(int(time.time()))
        params['timestamp'] = timestamp
        params[self.key_name] = self.api_key
        
        # 构建签名字符串
        sorted_params = sorted(params.items())
        sign_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
        sign_str = f'{method.upper()}&{url}&{sign_str}'
        
        # 生成HMAC-SHA256签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        return params


class JWTAuth(APIAuth):
    """JWT认证"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", 
                 expires_in: int = 3600, issuer: Optional[str] = None):
        """初始化JWT认证
        
        Args:
            secret_key: JWT密钥
            algorithm: 签名算法
            expires_in: 过期时间（秒）
            issuer: 签发者
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expires_in = expires_in
        self.issuer = issuer
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    def _generate_token(self, payload: Optional[Dict[str, Any]] = None) -> str:
        """生成JWT令牌
        
        Args:
            payload: 载荷数据
            
        Returns:
            str: JWT令牌
        """
        now = datetime.utcnow()
        
        token_payload = {
            'iat': now,
            'exp': now + timedelta(seconds=self.expires_in)
        }
        
        if self.issuer:
            token_payload['iss'] = self.issuer
        
        if payload:
            token_payload.update(payload)
        
        return jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)
    
    def get_token(self, payload: Optional[Dict[str, Any]] = None) -> str:
        """获取有效的JWT令牌
        
        Args:
            payload: 载荷数据
            
        Returns:
            str: JWT令牌
        """
        now = datetime.utcnow()
        
        # 检查令牌是否过期
        if (self._token is None or 
            self._token_expires is None or 
            now >= self._token_expires - timedelta(minutes=5)):
            
            self._token = self._generate_token(payload)
            self._token_expires = now + timedelta(seconds=self.expires_in)
        
        return self._token
    
    def get_headers(self) -> Dict[str, str]:
        """获取认证头信息"""
        token = self.get_token()
        return {
            'Authorization': f'Bearer {token}'
        }
    
    def sign_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """JWT认证不需要额外签名"""
        return params or {}
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None


class WeChatAuth(APIAuth):
    """微信API认证"""
    
    def __init__(self, corp_id: str, corp_secret: str):
        """初始化微信认证
        
        Args:
            corp_id: 企业ID
            corp_secret: 企业密钥
        """
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def get_access_token(self) -> str:
        """获取访问令牌（需要在具体实现中调用微信API）
        
        Returns:
            str: 访问令牌
        """
        # 这里应该调用微信API获取access_token
        # 为了示例，返回一个占位符
        return "placeholder_access_token"
    
    def get_headers(self) -> Dict[str, str]:
        """获取认证头信息"""
        return {
            'Content-Type': 'application/json'
        }
    
    def sign_request(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """微信API使用access_token参数认证"""
        if params is None:
            params = {}
        
        # 注意：实际使用时需要异步获取access_token
        # params['access_token'] = await self.get_access_token()
        
        return params