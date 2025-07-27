#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统日志配置
提供结构化日志记录功能
"""

import sys
import os
from pathlib import Path
from loguru import logger
from typing import Dict, Any

# 确保日志目录存在
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志配置
LOG_CONFIG = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            "level": "INFO",
            "colorize": True,
        },
        {
            "sink": LOG_DIR / "pmc.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "level": "INFO",
            "rotation": "10 MB",
            "retention": "30 days",
            "compression": "zip",
            "encoding": "utf-8",
        },
        {
            "sink": LOG_DIR / "error.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
            "level": "ERROR",
            "rotation": "5 MB",
            "retention": "60 days",
            "compression": "zip",
            "encoding": "utf-8",
        },
        {
            "sink": LOG_DIR / "access.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {message}",
            "level": "INFO",
            "rotation": "1 day",
            "retention": "7 days",
            "filter": lambda record: "access" in record["extra"],
            "encoding": "utf-8",
        },
        {
            "sink": LOG_DIR / "performance.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {message}",
            "level": "INFO",
            "rotation": "1 day",
            "retention": "30 days",
            "filter": lambda record: "performance" in record["extra"],
            "encoding": "utf-8",
        },
    ]
}


def setup_logging(log_level: str = "INFO", debug: bool = False) -> None:
    """
    设置日志配置
    
    Args:
        log_level: 日志级别
        debug: 是否为调试模式
    """
    # 移除默认处理器
    logger.remove()
    
    # 根据环境调整日志级别
    if debug:
        log_level = "DEBUG"
    
    # 控制台输出
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=debug,
        diagnose=debug,
    )
    
    # 文件输出 - 主日志
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    logger.add(
        LOG_DIR / "pmc.log",
        format=file_format,
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        backtrace=debug,
        diagnose=debug,
    )
    
    # 错误日志
    error_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message} | "
        "{extra}"
    )
    
    logger.add(
        LOG_DIR / "error.log",
        format=error_format,
        level="ERROR",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    # 访问日志
    logger.add(
        LOG_DIR / "access.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="7 days",
        filter=lambda record: "access" in record["extra"],
        encoding="utf-8",
    )
    
    # 性能日志
    logger.add(
        LOG_DIR / "performance.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        filter=lambda record: "performance" in record["extra"],
        encoding="utf-8",
    )
    
    logger.info(f"日志系统初始化完成，日志级别: {log_level}")


def get_logger(name: str = None) -> logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logger: 日志记录器实例
    """
    if name:
        return logger.bind(name=name)
    return logger


def log_access(method: str, url: str, status_code: int, response_time: float, user_id: str = None) -> None:
    """
    记录访问日志
    
    Args:
        method: HTTP方法
        url: 请求URL
        status_code: 状态码
        response_time: 响应时间（毫秒）
        user_id: 用户ID
    """
    user_info = f" | User: {user_id}" if user_id else ""
    message = f"{method} {url} | Status: {status_code} | Time: {response_time:.2f}ms{user_info}"
    logger.bind(access=True).info(message)


def log_performance(operation: str, duration: float, details: Dict[str, Any] = None) -> None:
    """
    记录性能日志
    
    Args:
        operation: 操作名称
        duration: 执行时间（毫秒）
        details: 详细信息
    """
    details_str = f" | Details: {details}" if details else ""
    message = f"Operation: {operation} | Duration: {duration:.2f}ms{details_str}"
    logger.bind(performance=True).info(message)


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    记录错误日志
    
    Args:
        error: 异常对象
        context: 上下文信息
    """
    context_info = context or {}
    logger.bind(**context_info).error(f"Error occurred: {str(error)}", exc_info=error)


def log_business_event(event_type: str, event_data: Dict[str, Any], user_id: str = None) -> None:
    """
    记录业务事件日志
    
    Args:
        event_type: 事件类型
        event_data: 事件数据
        user_id: 用户ID
    """
    user_info = f" | User: {user_id}" if user_id else ""
    logger.info(f"Business Event: {event_type} | Data: {event_data}{user_info}")


class LoggerMixin:
    """
    日志记录器混入类
    为类提供日志记录功能
    """
    
    @property
    def logger(self):
        """获取类专用的日志记录器"""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, error: Exception = None, **kwargs) -> None:
        """记录错误日志"""
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=error, **kwargs)
        else:
            self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self.logger.debug(message, **kwargs)


# 性能监控装饰器
def log_execution_time(operation_name: str = None):
    """
    记录函数执行时间的装饰器
    
    Args:
        operation_name: 操作名称，默认使用函数名
    """
    def decorator(func):
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # 转换为毫秒
                op_name = operation_name or func.__name__
                log_performance(op_name, duration)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                op_name = operation_name or func.__name__
                log_performance(f"{op_name} (ERROR)", duration)
                raise
        
        return wrapper
    return decorator


# 异常捕获装饰器
def log_exceptions(reraise: bool = True):
    """
    记录异常的装饰器
    
    Args:
        reraise: 是否重新抛出异常
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # 限制长度
                    'kwargs': str(kwargs)[:200]
                }
                log_error(e, context)
                if reraise:
                    raise
                return None
        
        return wrapper
    return decorator


# 导出主要接口
__all__ = [
    'setup_logging',
    'get_logger',
    'log_access',
    'log_performance',
    'log_error',
    'log_business_event',
    'LoggerMixin',
    'log_execution_time',
    'log_exceptions',
    'logger'
]