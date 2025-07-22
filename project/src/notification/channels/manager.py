"""通知渠道管理器

负责管理所有通知渠道的注册、选择和状态监控。
"""

import asyncio
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import logging

from .base import NotificationChannel
from ..models import NotificationMessage, ChannelConfig, ChannelType
from ..exceptions import ChannelError, ChannelUnavailableError

logger = logging.getLogger(__name__)


class ChannelManager:
    """通知渠道管理器"""
    
    def __init__(self):
        """初始化渠道管理器"""
        self._channels: Dict[str, NotificationChannel] = {}
        self._channel_classes: Dict[ChannelType, Type[NotificationChannel]] = {}
        self._default_channels: Dict[ChannelType, str] = {}
        self._health_check_interval = 300  # 5分钟
        self._health_check_task = None
        self._running = False
    
    def register_channel_class(self, channel_type: ChannelType, channel_class: Type[NotificationChannel]):
        """注册渠道类
        
        Args:
            channel_type: 渠道类型
            channel_class: 渠道类
        """
        self._channel_classes[channel_type] = channel_class
        logger.info(f"Registered channel class: {channel_type.value} -> {channel_class.__name__}")
    
    def add_channel(self, config: ChannelConfig) -> NotificationChannel:
        """添加通知渠道
        
        Args:
            config: 渠道配置
            
        Returns:
            NotificationChannel: 创建的渠道实例
            
        Raises:
            ChannelError: 渠道类型未注册或配置错误
        """
        if config.channel_type not in self._channel_classes:
            raise ChannelError(f"Channel type '{config.channel_type.value}' not registered")
        
        if config.name in self._channels:
            raise ChannelError(f"Channel '{config.name}' already exists")
        
        try:
            channel_class = self._channel_classes[config.channel_type]
            channel = channel_class(config)
            self._channels[config.name] = channel
            
            # 设置为默认渠道（如果是该类型的第一个渠道）
            if config.channel_type not in self._default_channels:
                self._default_channels[config.channel_type] = config.name
            
            logger.info(f"Added channel: {config.name} ({config.channel_type.value})")
            return channel
            
        except Exception as e:
            raise ChannelError(f"Failed to create channel '{config.name}': {str(e)}")
    
    def remove_channel(self, name: str) -> bool:
        """移除通知渠道
        
        Args:
            name: 渠道名称
            
        Returns:
            bool: 是否成功移除
        """
        if name not in self._channels:
            return False
        
        channel = self._channels[name]
        del self._channels[name]
        
        # 如果是默认渠道，需要重新选择默认渠道
        for channel_type, default_name in self._default_channels.items():
            if default_name == name:
                # 寻找同类型的其他渠道
                for other_name, other_channel in self._channels.items():
                    if other_channel.config.channel_type == channel_type:
                        self._default_channels[channel_type] = other_name
                        break
                else:
                    # 没有同类型的其他渠道，删除默认设置
                    del self._default_channels[channel_type]
                break
        
        logger.info(f"Removed channel: {name}")
        return True
    
    def get_channel(self, name: str) -> Optional[NotificationChannel]:
        """获取指定渠道
        
        Args:
            name: 渠道名称
            
        Returns:
            Optional[NotificationChannel]: 渠道实例
        """
        return self._channels.get(name)
    
    def get_channels_by_type(self, channel_type: ChannelType) -> List[NotificationChannel]:
        """获取指定类型的所有渠道
        
        Args:
            channel_type: 渠道类型
            
        Returns:
            List[NotificationChannel]: 渠道列表
        """
        return [
            channel for channel in self._channels.values()
            if channel.config.channel_type == channel_type
        ]
    
    def get_available_channels(self, channel_type: Optional[ChannelType] = None) -> List[NotificationChannel]:
        """获取可用的渠道
        
        Args:
            channel_type: 可选的渠道类型过滤
            
        Returns:
            List[NotificationChannel]: 可用渠道列表
        """
        channels = self._channels.values()
        if channel_type:
            channels = [ch for ch in channels if ch.config.channel_type == channel_type]
        
        # 这里返回启用的渠道，实际可用性在发送时检查
        return [ch for ch in channels if ch.enabled]
    
    async def select_best_channel(self, 
                                channel_type: Optional[ChannelType] = None,
                                preferred_channel: Optional[str] = None) -> Optional[NotificationChannel]:
        """选择最佳渠道
        
        Args:
            channel_type: 可选的渠道类型
            preferred_channel: 首选渠道名称
            
        Returns:
            Optional[NotificationChannel]: 选中的渠道
        """
        # 如果指定了首选渠道，优先使用
        if preferred_channel and preferred_channel in self._channels:
            channel = self._channels[preferred_channel]
            if await channel.is_available():
                return channel
        
        # 获取可用渠道
        available_channels = self.get_available_channels(channel_type)
        
        # 检查实际可用性并选择最佳渠道
        for channel in available_channels:
            if await channel.is_available():
                return channel
        
        return None
    
    async def send_message(self, 
                         message: NotificationMessage,
                         channel_name: Optional[str] = None,
                         channel_type: Optional[ChannelType] = None) -> tuple[bool, Optional[str], Optional[str]]:
        """发送消息
        
        Args:
            message: 通知消息
            channel_name: 指定渠道名称
            channel_type: 指定渠道类型
            
        Returns:
            (success, error_message, used_channel): 发送结果、错误信息和使用的渠道名称
        """
        # 选择渠道
        channel = await self.select_best_channel(channel_type, channel_name)
        
        if not channel:
            error_msg = "No available channel found"
            if channel_type:
                error_msg += f" for type '{channel_type.value}'"
            if channel_name:
                error_msg += f" with name '{channel_name}'"
            return False, error_msg, None
        
        # 发送消息
        try:
            success, error_message = await channel.send_with_rate_limit(message)
            return success, error_message, channel.name
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", channel.name
    
    async def broadcast_message(self, 
                              message: NotificationMessage,
                              channel_type: Optional[ChannelType] = None,
                              exclude_channels: Optional[List[str]] = None) -> Dict[str, tuple[bool, Optional[str]]]:
        """广播消息到多个渠道
        
        Args:
            message: 通知消息
            channel_type: 可选的渠道类型过滤
            exclude_channels: 排除的渠道名称列表
            
        Returns:
            Dict[str, tuple[bool, Optional[str]]]: 各渠道的发送结果
        """
        exclude_channels = exclude_channels or []
        available_channels = self.get_available_channels(channel_type)
        
        # 过滤排除的渠道
        channels_to_send = [
            ch for ch in available_channels 
            if ch.name not in exclude_channels
        ]
        
        # 并发发送
        tasks = [
            channel.send_with_rate_limit(message)
            for channel in channels_to_send
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        send_results = {}
        for channel, result in zip(channels_to_send, results):
            if isinstance(result, Exception):
                send_results[channel.name] = (False, str(result))
            else:
                send_results[channel.name] = result
        
        return send_results
    
    async def health_check_all(self) -> Dict[str, bool]:
        """对所有渠道进行健康检查
        
        Returns:
            Dict[str, bool]: 各渠道的健康状态
        """
        if not self._channels:
            return {}
        
        tasks = [
            channel.health_check()
            for channel in self._channels.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for channel, result in zip(self._channels.values(), results):
            if isinstance(result, Exception):
                health_status[channel.name] = False
            else:
                health_status[channel.name] = result
        
        return health_status
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有渠道的状态
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有渠道的状态信息
        """
        return {
            name: channel.get_status()
            for name, channel in self._channels.items()
        }
    
    async def start(self):
        """启动渠道管理器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动健康检查任务
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Channel manager started")
    
    async def stop(self):
        """停止渠道管理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Channel manager stopped")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self.health_check_all()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)  # 出错时等待1分钟再重试
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """列出所有渠道的基本信息
        
        Returns:
            List[Dict[str, Any]]: 渠道信息列表
        """
        return [
            {
                "name": channel.name,
                "type": channel.config.channel_type.value,
                "enabled": channel.enabled,
                "healthy": channel._health_status,
                "is_default": channel.name in self._default_channels.values()
            }
            for channel in self._channels.values()
        ]
    
    def __len__(self) -> int:
        return len(self._channels)
    
    def __contains__(self, name: str) -> bool:
        return name in self._channels
    
    def __iter__(self):
        return iter(self._channels.values())