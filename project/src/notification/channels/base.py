"""通知渠道抽象基类

定义了所有通知渠道必须实现的接口。
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models import NotificationMessage, ChannelConfig
from ..exceptions import ChannelError, RateLimitError


class NotificationChannel(ABC):
    """通知渠道抽象基类"""
    
    def __init__(self, config: ChannelConfig):
        """初始化通知渠道
        
        Args:
            config: 渠道配置
        """
        self.config = config
        self.name = config.name
        self.enabled = config.enabled
        self.rate_limit = config.rate_limit
        self.timeout = config.timeout
        
        # 速率限制相关
        self._rate_limit_window = 60  # 1分钟窗口
        self._rate_limit_requests = []
        self._rate_limit_lock = asyncio.Lock()
        
        # 健康状态
        self._last_health_check = None
        self._health_status = True
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> Tuple[bool, Optional[str]]:
        """发送通知
        
        Args:
            message: 通知消息
            
        Returns:
            (success, error_message): 发送结果和错误信息
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 渠道是否健康
        """
        pass
    
    async def is_available(self) -> bool:
        """检查渠道是否可用
        
        Returns:
            bool: 渠道是否可用
        """
        if not self.enabled:
            return False
        
        # 检查健康状态
        if not await self._check_health_status():
            return False
        
        # 检查速率限制
        if not await self._check_rate_limit():
            return False
        
        return True
    
    async def _check_health_status(self) -> bool:
        """检查健康状态"""
        now = datetime.now()
        
        # 如果最近检查过且状态良好，直接返回
        if (self._last_health_check and 
            now - self._last_health_check < timedelta(minutes=5) and 
            self._health_status):
            return True
        
        # 执行健康检查
        try:
            self._health_status = await self.health_check()
            self._last_health_check = now
            
            if self._health_status:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
                
        except Exception:
            self._health_status = False
            self._consecutive_failures += 1
        
        # 如果连续失败次数过多，暂时禁用渠道
        if self._consecutive_failures >= self._max_consecutive_failures:
            self.enabled = False
        
        return self._health_status
    
    async def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        async with self._rate_limit_lock:
            now = datetime.now()
            
            # 清理过期的请求记录
            cutoff_time = now - timedelta(seconds=self._rate_limit_window)
            self._rate_limit_requests = [
                req_time for req_time in self._rate_limit_requests 
                if req_time > cutoff_time
            ]
            
            # 检查是否超过速率限制
            if len(self._rate_limit_requests) >= self.rate_limit:
                return False
            
            return True
    
    async def _record_request(self):
        """记录请求"""
        async with self._rate_limit_lock:
            self._rate_limit_requests.append(datetime.now())
    
    async def send_with_rate_limit(self, message: NotificationMessage) -> Tuple[bool, Optional[str]]:
        """带速率限制的发送
        
        Args:
            message: 通知消息
            
        Returns:
            (success, error_message): 发送结果和错误信息
        """
        # 检查渠道是否可用
        if not await self.is_available():
            if not self.enabled:
                return False, f"Channel '{self.name}' is disabled"
            elif not self._health_status:
                return False, f"Channel '{self.name}' is unhealthy"
            else:
                return False, f"Channel '{self.name}' rate limit exceeded"
        
        # 记录请求
        await self._record_request()
        
        try:
            # 发送消息
            success, error_message = await asyncio.wait_for(
                self.send(message), 
                timeout=self.timeout
            )
            
            # 更新健康状态
            if success:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
            
            return success, error_message
            
        except asyncio.TimeoutError:
            self._consecutive_failures += 1
            return False, f"Channel '{self.name}' timeout after {self.timeout} seconds"
        except Exception as e:
            self._consecutive_failures += 1
            return False, f"Channel '{self.name}' error: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """获取渠道状态
        
        Returns:
            Dict: 渠道状态信息
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "healthy": self._health_status,
            "consecutive_failures": self._consecutive_failures,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "rate_limit": self.rate_limit,
            "current_requests": len(self._rate_limit_requests),
            "config": self.config.to_dict()
        }
    
    def reset_health_status(self):
        """重置健康状态"""
        self._health_status = True
        self._consecutive_failures = 0
        self._last_health_check = None
        if not self.config.enabled:  # 只有在配置中启用时才重新启用
            self.enabled = True
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
    
    def __repr__(self) -> str:
        return self.__str__()