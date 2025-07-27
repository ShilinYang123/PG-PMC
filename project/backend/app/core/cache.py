#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统缓存管理模块
提供Redis缓存的统一管理和操作接口
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager
import redis.asyncio as redis
from redis.exceptions import RedisError

from .config import settings
from .logging import get_logger, log_error, log_performance
from .exceptions import ExternalServiceException
from .database import get_redis

logger = get_logger(__name__)

T = TypeVar('T')


class CacheKeyBuilder:
    """
    缓存键构建器
    """
    
    def __init__(self, prefix: str = "pmc"):
        self.prefix = prefix
    
    def build(self, *parts: str, **kwargs) -> str:
        """
        构建缓存键
        
        Args:
            *parts: 键的组成部分
            **kwargs: 额外的键值对
            
        Returns:
            str: 构建的缓存键
        """
        key_parts = [self.prefix]
        key_parts.extend(str(part) for part in parts)
        
        if kwargs:
            # 对kwargs进行排序以确保一致性
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)
    
    def user_key(self, user_id: int, *parts: str) -> str:
        """构建用户相关的缓存键"""
        return self.build("user", str(user_id), *parts)
    
    def order_key(self, order_id: int, *parts: str) -> str:
        """构建订单相关的缓存键"""
        return self.build("order", str(order_id), *parts)
    
    def material_key(self, material_id: int, *parts: str) -> str:
        """构建物料相关的缓存键"""
        return self.build("material", str(material_id), *parts)
    
    def production_key(self, production_id: int, *parts: str) -> str:
        """构建生产相关的缓存键"""
        return self.build("production", str(production_id), *parts)
    
    def session_key(self, session_id: str) -> str:
        """构建会话缓存键"""
        return self.build("session", session_id)
    
    def api_key(self, endpoint: str, *args, **kwargs) -> str:
        """构建API缓存键"""
        # 创建参数的哈希值以避免键过长
        if args or kwargs:
            params_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return self.build("api", endpoint, params_hash)
        return self.build("api", endpoint)


class CacheSerializer:
    """
    缓存序列化器
    """
    
    @staticmethod
    def serialize(data: Any, method: str = "json") -> bytes:
        """
        序列化数据
        
        Args:
            data: 要序列化的数据
            method: 序列化方法 (json/pickle)
            
        Returns:
            bytes: 序列化后的数据
        """
        try:
            if method == "json":
                return json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
            elif method == "pickle":
                return pickle.dumps(data)
            else:
                raise ValueError(f"不支持的序列化方法: {method}")
        except Exception as e:
            logger.error(f"数据序列化失败: {e}")
            raise
    
    @staticmethod
    def deserialize(data: bytes, method: str = "json") -> Any:
        """
        反序列化数据
        
        Args:
            data: 要反序列化的数据
            method: 反序列化方法 (json/pickle)
            
        Returns:
            Any: 反序列化后的数据
        """
        try:
            if method == "json":
                return json.loads(data.decode('utf-8'))
            elif method == "pickle":
                return pickle.loads(data)
            else:
                raise ValueError(f"不支持的反序列化方法: {method}")
        except Exception as e:
            logger.error(f"数据反序列化失败: {e}")
            raise


class CacheManager:
    """
    缓存管理器
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.key_builder = CacheKeyBuilder()
        self.serializer = CacheSerializer()
        self.default_ttl = settings.CACHE_DEFAULT_TTL
    
    async def _get_redis(self) -> redis.Redis:
        """获取Redis客户端"""
        if self.redis_client:
            return self.redis_client
        return await get_redis()
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            serialize_method: 序列化方法
            
        Returns:
            bool: 是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            
            # 序列化数据
            serialized_data = self.serializer.serialize(value, serialize_method)
            
            # 设置缓存
            ttl = ttl or self.default_ttl
            result = await redis_client.setex(key, ttl, serialized_data)
            
            logger.debug(f"缓存设置成功: {key}, TTL: {ttl}")
            return bool(result)
            
        except Exception as e:
            log_error(e, {"operation": "cache_set", "key": key})
            return False
    
    async def get(
        self,
        key: str,
        default: Any = None,
        serialize_method: str = "json"
    ) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            default: 默认值
            serialize_method: 反序列化方法
            
        Returns:
            Any: 缓存值或默认值
        """
        try:
            redis_client = await self._get_redis()
            
            # 获取缓存数据
            data = await redis_client.get(key)
            if data is None:
                logger.debug(f"缓存未命中: {key}")
                return default
            
            # 反序列化数据
            result = self.serializer.deserialize(data, serialize_method)
            logger.debug(f"缓存命中: {key}")
            return result
            
        except Exception as e:
            log_error(e, {"operation": "cache_get", "key": key})
            return default
    
    async def delete(self, *keys: str) -> int:
        """
        删除缓存
        
        Args:
            *keys: 要删除的缓存键
            
        Returns:
            int: 删除的键数量
        """
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(*keys)
            logger.debug(f"缓存删除: {keys}, 删除数量: {result}")
            return result
            
        except Exception as e:
            log_error(e, {"operation": "cache_delete", "keys": keys})
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        try:
            redis_client = await self._get_redis()
            result = await redis_client.exists(key)
            return bool(result)
            
        except Exception as e:
            log_error(e, {"operation": "cache_exists", "key": key})
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            result = await redis_client.expire(key, ttl)
            return bool(result)
            
        except Exception as e:
            log_error(e, {"operation": "cache_expire", "key": key})
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取缓存剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余时间（秒），-1表示永不过期，-2表示不存在
        """
        try:
            redis_client = await self._get_redis()
            return await redis_client.ttl(key)
            
        except Exception as e:
            log_error(e, {"operation": "cache_ttl", "key": key})
            return -2
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        递增缓存值
        
        Args:
            key: 缓存键
            amount: 递增量
            ttl: 过期时间（秒）
            
        Returns:
            int: 递增后的值
        """
        try:
            redis_client = await self._get_redis()
            
            # 使用管道确保原子性
            async with redis_client.pipeline() as pipe:
                await pipe.incrby(key, amount)
                if ttl:
                    await pipe.expire(key, ttl)
                results = await pipe.execute()
                
            return results[0]
            
        except Exception as e:
            log_error(e, {"operation": "cache_increment", "key": key})
            return 0
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> Any:
        """
        获取缓存，如果不存在则通过工厂函数生成并设置
        
        Args:
            key: 缓存键
            factory: 工厂函数
            ttl: 过期时间（秒）
            serialize_method: 序列化方法
            
        Returns:
            Any: 缓存值
        """
        # 先尝试获取缓存
        value = await self.get(key, serialize_method=serialize_method)
        if value is not None:
            return value
        
        # 缓存不存在，通过工厂函数生成
        try:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            
            # 设置缓存
            await self.set(key, value, ttl, serialize_method)
            return value
            
        except Exception as e:
            log_error(e, {"operation": "cache_get_or_set", "key": key})
            raise
    
    async def mget(self, keys: List[str], serialize_method: str = "json") -> Dict[str, Any]:
        """
        批量获取缓存
        
        Args:
            keys: 缓存键列表
            serialize_method: 反序列化方法
            
        Returns:
            Dict[str, Any]: 键值对字典
        """
        try:
            redis_client = await self._get_redis()
            
            # 批量获取
            values = await redis_client.mget(keys)
            
            # 构建结果字典
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = self.serializer.deserialize(value, serialize_method)
                    except Exception as e:
                        logger.warning(f"反序列化失败: {key}, {e}")
                        result[key] = None
                else:
                    result[key] = None
            
            return result
            
        except Exception as e:
            log_error(e, {"operation": "cache_mget", "keys": keys})
            return {key: None for key in keys}
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None, serialize_method: str = "json") -> bool:
        """
        批量设置缓存
        
        Args:
            mapping: 键值对字典
            ttl: 过期时间（秒）
            serialize_method: 序列化方法
            
        Returns:
            bool: 是否设置成功
        """
        try:
            redis_client = await self._get_redis()
            
            # 序列化所有值
            serialized_mapping = {}
            for key, value in mapping.items():
                serialized_mapping[key] = self.serializer.serialize(value, serialize_method)
            
            # 使用管道批量设置
            async with redis_client.pipeline() as pipe:
                await pipe.mset(serialized_mapping)
                
                # 如果指定了TTL，为每个键设置过期时间
                if ttl:
                    for key in mapping.keys():
                        await pipe.expire(key, ttl)
                
                await pipe.execute()
            
            return True
            
        except Exception as e:
            log_error(e, {"operation": "cache_mset", "keys": list(mapping.keys())})
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        根据模式清除缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            int: 删除的键数量
        """
        try:
            redis_client = await self._get_redis()
            
            # 查找匹配的键
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # 批量删除
            if keys:
                deleted_count = await redis_client.delete(*keys)
                logger.info(f"清除缓存模式 {pattern}: 删除 {deleted_count} 个键")
                return deleted_count
            
            return 0
            
        except Exception as e:
            log_error(e, {"operation": "cache_clear_pattern", "pattern": pattern})
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            log_error(e, {"operation": "cache_stats"})
            return {}


# 全局缓存管理器实例
cache_manager = CacheManager()


# 缓存装饰器
def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    serialize_method: str = "json",
    skip_cache: Callable = None
):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间（秒）
        key_prefix: 键前缀
        serialize_method: 序列化方法
        skip_cache: 跳过缓存的条件函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查是否跳过缓存
            if skip_cache and skip_cache(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            # 构建缓存键
            cache_key = cache_manager.key_builder.api_key(
                f"{key_prefix}{func.__name__}",
                *args,
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(
                cache_key,
                serialize_method=serialize_method
            )
            
            if cached_result is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return cached_result
            
            # 执行函数
            with log_performance(f"cache_miss_{func.__name__}"):
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
            
            # 设置缓存
            await cache_manager.set(
                cache_key,
                result,
                ttl or cache_manager.default_ttl,
                serialize_method
            )
            
            logger.debug(f"缓存设置: {func.__name__}")
            return result
        
        return wrapper
    return decorator


# 缓存失效装饰器
def cache_invalidate(patterns: List[str]):
    """
    缓存失效装饰器
    
    Args:
        patterns: 要失效的缓存模式列表
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 失效相关缓存
            for pattern in patterns:
                await cache_manager.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# 便捷函数
async def get_cache(key: str, default: Any = None) -> Any:
    """获取缓存"""
    return await cache_manager.get(key, default)


async def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """设置缓存"""
    return await cache_manager.set(key, value, ttl)


async def delete_cache(*keys: str) -> int:
    """删除缓存"""
    return await cache_manager.delete(*keys)


async def clear_cache_pattern(pattern: str) -> int:
    """清除匹配模式的缓存"""
    return await cache_manager.clear_pattern(pattern)


# 导入asyncio（如果需要）
import asyncio


# 导出主要接口
__all__ = [
    'CacheManager',
    'CacheKeyBuilder',
    'CacheSerializer',
    'cache_manager',
    'cached',
    'cache_invalidate',
    'get_cache',
    'set_cache',
    'delete_cache',
    'clear_cache_pattern'
]