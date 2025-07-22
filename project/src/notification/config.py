"""通知系统配置管理

提供配置加载、验证和管理功能。
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .models import ChannelType
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class NotificationConfig:
    """通知系统配置"""
    
    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict[str, Any]] = None):
        """初始化配置
        
        Args:
            config_path: 配置文件路径
            config_dict: 配置字典
        """
        self._config = {}
        self._config_path = config_path
        
        if config_dict:
            self._config = config_dict.copy()
        elif config_path:
            self.load_from_file(config_path)
        else:
            self._load_default_config()
        
        self._validate_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            "service": {
                "name": "PMC Notification Service",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "queue": {
                "max_size": 1000,
                "batch_size": 10,
                "retry_delay": 5,
                "max_retries": 3,
                "cleanup_interval": 3600,
                "message_ttl": 604800  # 7 days
            },
            "scheduler": {
                "worker_count": 2,
                "health_check_interval": 60,
                "stats_interval": 300
            },
            "channels": [],
            "templates": {},
            "security": {
                "encrypt_sensitive_data": True,
                "token_expiry": 3600,
                "rate_limit_enabled": True
            },
            "monitoring": {
                "enabled": True,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health"
            }
        }
    
    def load_from_file(self, config_path: str):
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    self._config = yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    self._config = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {config_file.suffix}")
            
            logger.info(f"Configuration loaded from: {config_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def save_to_file(self, config_path: Optional[str] = None):
        """保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用初始化时的路径
        """
        path = config_path or self._config_path
        if not path:
            raise ConfigurationError("No configuration file path specified")
        
        config_file = Path(path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                elif config_file.suffix.lower() == '.json':
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {config_file.suffix}")
            
            logger.info(f"Configuration saved to: {path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def _validate_config(self):
        """验证配置"""
        # 验证必需的配置节
        required_sections = ['service', 'queue', 'scheduler']
        for section in required_sections:
            if section not in self._config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # 验证队列配置
        queue_config = self._config['queue']
        if queue_config.get('max_size', 0) <= 0:
            raise ConfigurationError("queue.max_size must be positive")
        
        if queue_config.get('batch_size', 0) <= 0:
            raise ConfigurationError("queue.batch_size must be positive")
        
        if queue_config.get('max_retries', 0) < 0:
            raise ConfigurationError("queue.max_retries must be non-negative")
        
        # 验证调度器配置
        scheduler_config = self._config['scheduler']
        if scheduler_config.get('worker_count', 0) <= 0:
            raise ConfigurationError("scheduler.worker_count must be positive")
        
        # 验证渠道配置
        channels = self._config.get('channels', [])
        for i, channel in enumerate(channels):
            self._validate_channel_config(channel, i)
        
        logger.info("Configuration validation passed")
    
    def _validate_channel_config(self, channel: Dict[str, Any], index: int):
        """验证渠道配置
        
        Args:
            channel: 渠道配置
            index: 渠道索引
        """
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in channel:
                raise ConfigurationError(f"Channel {index}: missing required field '{field}'")
        
        # 验证渠道类型
        try:
            ChannelType(channel['type'])
        except ValueError:
            valid_types = [t.value for t in ChannelType]
            raise ConfigurationError(
                f"Channel {index}: invalid type '{channel['type']}'. "
                f"Valid types: {valid_types}"
            )
        
        # 验证渠道名称唯一性
        channel_names = [ch['name'] for ch in self._config.get('channels', [])]
        if channel_names.count(channel['name']) > 1:
            raise ConfigurationError(f"Duplicate channel name: {channel['name']}")
        
        # 验证特定渠道类型的配置
        channel_type = ChannelType(channel['type'])
        settings = channel.get('settings', {})
        
        if channel_type == ChannelType.WECHAT_API:
            required_settings = ['corp_id', 'agent_id', 'secret']
            for setting in required_settings:
                if setting not in settings:
                    raise ConfigurationError(
                        f"Channel {channel['name']}: missing required setting '{setting}' for WeChat API"
                    )
        
        elif channel_type == ChannelType.WECHAT_BOT:
            required_settings = ['webhook_url', 'secret']
            for setting in required_settings:
                if setting not in settings:
                    raise ConfigurationError(
                        f"Channel {channel['name']}: missing required setting '{setting}' for WeChat Bot"
                    )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, updates: Dict[str, Any]):
        """更新配置
        
        Args:
            updates: 更新的配置
        """
        def deep_update(base: dict, updates: dict):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(self._config, updates)
        self._validate_config()
    
    def get_service_config(self) -> Dict[str, Any]:
        """获取服务配置"""
        return self._config.get('service', {})
    
    def get_queue_config(self) -> Dict[str, Any]:
        """获取队列配置"""
        return self._config.get('queue', {})
    
    def get_scheduler_config(self) -> Dict[str, Any]:
        """获取调度器配置"""
        return self._config.get('scheduler', {})
    
    def get_channels_config(self) -> List[Dict[str, Any]]:
        """获取渠道配置列表"""
        return self._config.get('channels', [])
    
    def get_channel_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定渠道配置
        
        Args:
            name: 渠道名称
            
        Returns:
            Optional[Dict[str, Any]]: 渠道配置
        """
        for channel in self.get_channels_config():
            if channel.get('name') == name:
                return channel
        return None
    
    def add_channel_config(self, channel_config: Dict[str, Any]):
        """添加渠道配置
        
        Args:
            channel_config: 渠道配置
        """
        # 验证配置
        self._validate_channel_config(channel_config, len(self._config.get('channels', [])))
        
        # 添加到配置
        if 'channels' not in self._config:
            self._config['channels'] = []
        
        self._config['channels'].append(channel_config)
        logger.info(f"Channel configuration added: {channel_config.get('name')}")
    
    def remove_channel_config(self, name: str) -> bool:
        """移除渠道配置
        
        Args:
            name: 渠道名称
            
        Returns:
            bool: 是否成功移除
        """
        channels = self._config.get('channels', [])
        for i, channel in enumerate(channels):
            if channel.get('name') == name:
                del channels[i]
                logger.info(f"Channel configuration removed: {name}")
                return True
        return False
    
    def get_templates_config(self) -> Dict[str, Any]:
        """获取模板配置"""
        return self._config.get('templates', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self._config.get('security', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self._config.get('monitoring', {})
    
    def is_debug_enabled(self) -> bool:
        """是否启用调试模式"""
        return self.get('service.debug', False)
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get('service.log_level', 'INFO')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self._config.copy()
    
    def __str__(self) -> str:
        """字符串表示"""
        return json.dumps(self._config, indent=2, ensure_ascii=False)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, NotificationConfig] = {}
        self._default_config: Optional[NotificationConfig] = None
    
    def load_config(self, name: str, config_path: str) -> NotificationConfig:
        """加载配置
        
        Args:
            name: 配置名称
            config_path: 配置文件路径
            
        Returns:
            NotificationConfig: 配置对象
        """
        config = NotificationConfig(config_path=config_path)
        self._configs[name] = config
        
        if self._default_config is None:
            self._default_config = config
        
        return config
    
    def create_config(self, name: str, config_dict: Dict[str, Any]) -> NotificationConfig:
        """创建配置
        
        Args:
            name: 配置名称
            config_dict: 配置字典
            
        Returns:
            NotificationConfig: 配置对象
        """
        config = NotificationConfig(config_dict=config_dict)
        self._configs[name] = config
        
        if self._default_config is None:
            self._default_config = config
        
        return config
    
    def get_config(self, name: Optional[str] = None) -> Optional[NotificationConfig]:
        """获取配置
        
        Args:
            name: 配置名称，如果为None则返回默认配置
            
        Returns:
            Optional[NotificationConfig]: 配置对象
        """
        if name is None:
            return self._default_config
        return self._configs.get(name)
    
    def set_default_config(self, name: str):
        """设置默认配置
        
        Args:
            name: 配置名称
        """
        if name in self._configs:
            self._default_config = self._configs[name]
        else:
            raise ConfigurationError(f"Configuration not found: {name}")
    
    def list_configs(self) -> List[str]:
        """列出所有配置名称
        
        Returns:
            List[str]: 配置名称列表
        """
        return list(self._configs.keys())
    
    def remove_config(self, name: str) -> bool:
        """移除配置
        
        Args:
            name: 配置名称
            
        Returns:
            bool: 是否成功移除
        """
        if name in self._configs:
            config = self._configs[name]
            del self._configs[name]
            
            # 如果移除的是默认配置，重新设置默认配置
            if self._default_config == config:
                self._default_config = next(iter(self._configs.values()), None)
            
            return True
        return False


# 全局配置管理器
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器
    
    Returns:
        ConfigManager: 配置管理器
    """
    return _config_manager


def load_config_from_env() -> NotificationConfig:
    """从环境变量加载配置
    
    Returns:
        NotificationConfig: 配置对象
    """
    config_path = os.getenv('NOTIFICATION_CONFIG_PATH')
    if config_path:
        return NotificationConfig(config_path=config_path)
    else:
        # 使用默认配置
        return NotificationConfig()


def create_sample_config(output_path: str):
    """创建示例配置文件
    
    Args:
        output_path: 输出文件路径
    """
    sample_config = {
        "service": {
            "name": "PMC Notification Service",
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO"
        },
        "queue": {
            "max_size": 1000,
            "batch_size": 10,
            "retry_delay": 5,
            "max_retries": 3,
            "cleanup_interval": 3600,
            "message_ttl": 604800
        },
        "scheduler": {
            "worker_count": 2,
            "health_check_interval": 60,
            "stats_interval": 300
        },
        "channels": [
            {
                "name": "wechat_api_main",
                "type": "wechat_api",
                "enabled": True,
                "settings": {
                    "corp_id": "your_corp_id",
                    "agent_id": "your_agent_id",
                    "secret": "your_secret"
                },
                "rate_limit": 60,
                "timeout": 30
            },
            {
                "name": "wechat_bot_alerts",
                "type": "wechat_bot",
                "enabled": True,
                "settings": {
                    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key",
                    "secret": "your_secret"
                },
                "rate_limit": 20,
                "timeout": 30
            }
        ],
        "security": {
            "encrypt_sensitive_data": True,
            "token_expiry": 3600,
            "rate_limit_enabled": True
        },
        "monitoring": {
            "enabled": True,
            "metrics_endpoint": "/metrics",
            "health_endpoint": "/health"
        }
    }
    
    config = NotificationConfig(config_dict=sample_config)
    config.save_to_file(output_path)
    logger.info(f"Sample configuration created: {output_path}")