#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统数据库连接模块
提供数据库连接池和会话管理功能
"""

import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy import text
import redis.asyncio as redis
from redis.exceptions import RedisError

from .config import settings
from .logging import get_logger, log_error, log_performance
from .exceptions import DatabaseException, ExternalServiceException

logger = get_logger(__name__)

# 全局变量
async_engine: Optional[AsyncEngine] = None
sync_engine = None
AsyncSessionLocal: Optional[async_sessionmaker] = None
SessionLocal = None
redis_client: Optional[redis.Redis] = None


class DatabaseManager:
    """
    数据库管理器
    """
    
    def __init__(self):
        self.async_engine: Optional[AsyncEngine] = None
        self.sync_engine = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        self.sync_session_factory = None
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self):
        """
        初始化数据库连接
        """
        if self._initialized:
            return
        
        try:
            # 初始化PostgreSQL连接
            await self._init_postgresql()
            
            # 初始化Redis连接
            await self._init_redis()
            
            self._initialized = True
            logger.info("数据库连接初始化完成")
            
        except Exception as e:
            log_error(e, {"component": "database_manager"})
            raise DatabaseException(f"数据库初始化失败: {str(e)}")
    
    async def _init_postgresql(self):
        """
        初始化PostgreSQL连接
        """
        # 异步引擎配置
        async_engine_kwargs = {
            "echo": settings.DEBUG,
            "echo_pool": settings.DEBUG,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }
        
        # 根据数据库类型选择连接池
        if settings.DATABASE_URL.startswith("sqlite"):
            async_engine_kwargs["poolclass"] = NullPool
            async_engine_kwargs.pop("pool_size", None)
            async_engine_kwargs.pop("max_overflow", None)
            async_engine_kwargs.pop("pool_timeout", None)
            async_engine_kwargs.pop("pool_recycle", None)
        else:
            async_engine_kwargs["poolclass"] = QueuePool
        
        # 创建异步引擎
        self.async_engine = create_async_engine(
            settings.DATABASE_URL,
            **async_engine_kwargs
        )
        
        # 创建同步引擎（用于某些特殊场景）
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        sync_url = sync_url.replace("sqlite+aiosqlite://", "sqlite://")
        
        sync_engine_kwargs = async_engine_kwargs.copy()
        sync_engine_kwargs.pop("echo_pool", None)
        
        self.sync_engine = create_engine(sync_url, **sync_engine_kwargs)
        
        # 创建会话工厂
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            autoflush=True,
            autocommit=False
        )
        
        # 设置事件监听器
        self._setup_engine_events()
        
        # 测试连接
        await self._test_postgresql_connection()
        
        logger.info(f"PostgreSQL连接初始化完成: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    async def _init_redis(self):
        """
        初始化Redis连接
        """
        if not settings.REDIS_URL:
            logger.warning("Redis URL未配置，跳过Redis初始化")
            return
        
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self._test_redis_connection()
            
            logger.info(f"Redis连接初始化完成: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            log_error(e, {"component": "redis_init"})
            raise ExternalServiceException("Redis", f"Redis连接失败: {str(e)}")
    
    def _setup_engine_events(self):
        """
        设置数据库引擎事件监听器
        """
        @event.listens_for(self.async_engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """设置SQLite pragma"""
            if settings.DATABASE_URL.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=1000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(self.async_engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出事件"""
            logger.debug("数据库连接检出")
        
        @event.listens_for(self.async_engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入事件"""
            logger.debug("数据库连接检入")
        
        @event.listens_for(self.async_engine.sync_engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            """连接失效事件"""
            logger.warning(f"数据库连接失效: {exception}")
    
    async def _test_postgresql_connection(self):
        """
        测试PostgreSQL连接
        """
        try:
            async with self.async_session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()
                logger.info("PostgreSQL连接测试成功")
        except Exception as e:
            log_error(e, {"component": "postgresql_test"})
            raise DatabaseException(f"PostgreSQL连接测试失败: {str(e)}")
    
    async def _test_redis_connection(self):
        """
        测试Redis连接
        """
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.ping()
            logger.info("Redis连接测试成功")
        except Exception as e:
            log_error(e, {"component": "redis_test"})
            raise ExternalServiceException("Redis", f"Redis连接测试失败: {str(e)}")
    
    async def close(self):
        """
        关闭数据库连接
        """
        try:
            if self.async_engine:
                await self.async_engine.dispose()
                logger.info("异步数据库引擎已关闭")
            
            if self.sync_engine:
                self.sync_engine.dispose()
                logger.info("同步数据库引擎已关闭")
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis连接已关闭")
            
            self._initialized = False
            
        except Exception as e:
            log_error(e, {"component": "database_close"})
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话
        
        Yields:
            AsyncSession: 异步数据库会话
        """
        if not self._initialized:
            await self.initialize()
        
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log_error(e, {"component": "async_session"})
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def get_sync_session(self) -> Session:
        """
        获取同步数据库会话
        
        Yields:
            Session: 同步数据库会话
        """
        if not self._initialized:
            await self.initialize()
        
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error(e, {"component": "sync_session"})
            raise
        finally:
            session.close()
    
    async def get_redis(self) -> redis.Redis:
        """
        获取Redis客户端
        
        Returns:
            redis.Redis: Redis客户端
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.redis_client:
            raise ExternalServiceException("Redis", "Redis客户端未初始化")
        
        return self.redis_client
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        health_status = {
            "postgresql": {"status": "unknown", "details": {}},
            "redis": {"status": "unknown", "details": {}}
        }
        
        # 检查PostgreSQL
        try:
            start_time = asyncio.get_event_loop().time()
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            health_status["postgresql"] = {
                "status": "healthy",
                "details": {
                    "response_time_ms": round(response_time, 2),
                    "pool_size": self.async_engine.pool.size() if hasattr(self.async_engine.pool, 'size') else "N/A",
                    "checked_out": self.async_engine.pool.checkedout() if hasattr(self.async_engine.pool, 'checkedout') else "N/A"
                }
            }
        except Exception as e:
            health_status["postgresql"] = {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
        
        # 检查Redis
        if self.redis_client:
            try:
                start_time = asyncio.get_event_loop().time()
                await self.redis_client.ping()
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                info = await self.redis_client.info()
                health_status["redis"] = {
                    "status": "healthy",
                    "details": {
                        "response_time_ms": round(response_time, 2),
                        "connected_clients": info.get("connected_clients", "N/A"),
                        "used_memory_human": info.get("used_memory_human", "N/A")
                    }
                }
            except Exception as e:
                health_status["redis"] = {
                    "status": "unhealthy",
                    "details": {"error": str(e)}
                }
        else:
            health_status["redis"] = {
                "status": "disabled",
                "details": {"message": "Redis未配置"}
            }
        
        return health_status


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的依赖注入函数
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with db_manager.get_async_session() as session:
        yield session


async def get_redis() -> redis.Redis:
    """
    获取Redis客户端的依赖注入函数
    
    Returns:
        redis.Redis: Redis客户端
    """
    return await db_manager.get_redis()


# 数据库操作装饰器
def with_db_session(auto_commit: bool = True, reraise: bool = True):
    """
    数据库会话装饰器
    
    Args:
        auto_commit: 是否自动提交
        reraise: 是否重新抛出异常
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async with db_manager.get_async_session() as session:
                    # 将session作为第一个参数传递
                    result = await func(session, *args, **kwargs)
                    
                    if auto_commit:
                        await session.commit()
                    
                    return result
            except Exception as e:
                if reraise:
                    raise
                log_error(e, {"function": func.__name__})
                return None
        
        return wrapper
    return decorator


# 事务装饰器
def with_transaction(isolation_level: str = None):
    """
    事务装饰器
    
    Args:
        isolation_level: 事务隔离级别
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with db_manager.get_async_session() as session:
                if isolation_level:
                    await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                
                try:
                    result = await func(session, *args, **kwargs)
                    await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    log_error(e, {"function": func.__name__, "transaction": True})
                    raise
        
        return wrapper
    return decorator


# 性能监控装饰器
def monitor_db_performance(operation_name: str = None):
    """
    数据库性能监控装饰器
    
    Args:
        operation_name: 操作名称
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            
            with log_performance(f"db_operation_{operation}"):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 初始化和清理函数
async def init_database():
    """
    初始化数据库连接
    """
    await db_manager.initialize()
    logger.info("数据库连接池初始化完成")


async def close_database():
    """
    关闭数据库连接
    """
    await db_manager.close()
    logger.info("数据库连接池已关闭")


# 兼容性函数（保持向后兼容）
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（兼容性函数）
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with db_manager.get_async_session() as session:
        yield session


# 导出主要接口
__all__ = [
    'DatabaseManager',
    'db_manager',
    'get_async_db',
    'get_redis',
    'get_db',
    'init_database',
    'close_database',
    'with_db_session',
    'with_transaction',
    'monitor_db_performance'
]