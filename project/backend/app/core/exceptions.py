#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统异常处理模块
提供统一的异常处理和错误响应机制
"""

import traceback
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from redis.exceptions import RedisError
from pydantic import ValidationError

from .logging import get_logger, log_error

logger = get_logger(__name__)


class PMCException(Exception):
    """
    PMC系统基础异常类
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "PMC_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class BusinessException(PMCException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ValidationException(PMCException):
    """数据验证异常"""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        if field:
            details = details or {}
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationException(PMCException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationException(PMCException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ResourceNotFoundException(PMCException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, resource_id: Union[str, int] = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource}未找到"
        if resource_id:
            message += f"(ID: {resource_id})"
        
        if resource_id:
            details = details or {}
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ResourceConflictException(PMCException):
    """资源冲突异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RESOURCE_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class DatabaseException(PMCException):
    """数据库异常"""
    
    def __init__(self, message: str = "数据库操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ExternalServiceException(PMCException):
    """外部服务异常"""
    
    def __init__(self, service: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        message = message or f"{service}服务不可用"
        details = details or {}
        details["service"] = service
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class RateLimitException(PMCException):
    """速率限制异常"""
    
    def __init__(self, message: str = "请求过于频繁", retry_after: int = None, details: Optional[Dict[str, Any]] = None):
        if retry_after:
            details = details or {}
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ConfigurationException(PMCException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: str = None, details: Optional[Dict[str, Any]] = None):
        if config_key:
            details = details or {}
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# 异常处理器
async def pmc_exception_handler(request: Request, exc: PMCException) -> JSONResponse:
    """
    PMC异常处理器
    
    Args:
        request: 请求对象
        exc: PMC异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 记录异常
    log_error(exc, {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "error_code": exc.error_code
    })
    
    # 构建响应
    response_data = exc.to_dict()
    response_data["request_id"] = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP异常处理器
    
    Args:
        request: 请求对象
        exc: HTTP异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 记录异常
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    请求验证异常处理器
    
    Args:
        request: 请求对象
        exc: 验证异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 提取验证错误详情
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # 记录异常
    logger.warning(f"请求验证失败: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "请求数据验证失败",
            "details": {"errors": errors},
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    SQLAlchemy异常处理器
    
    Args:
        request: 请求对象
        exc: SQLAlchemy异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 记录异常
    log_error(exc, {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "url": str(request.url)
    })
    
    # 根据异常类型返回不同的错误信息
    if isinstance(exc, IntegrityError):
        message = "数据完整性约束违反"
        error_code = "INTEGRITY_ERROR"
    elif isinstance(exc, DataError):
        message = "数据格式错误"
        error_code = "DATA_ERROR"
    else:
        message = "数据库操作失败"
        error_code = "DATABASE_ERROR"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_code,
            "message": message,
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


async def redis_exception_handler(request: Request, exc: RedisError) -> JSONResponse:
    """
    Redis异常处理器
    
    Args:
        request: 请求对象
        exc: Redis异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 记录异常
    log_error(exc, {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "url": str(request.url)
    })
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "CACHE_ERROR",
            "message": "缓存服务不可用",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器
    
    Args:
        request: 请求对象
        exc: 异常
        
    Returns:
        JSONResponse: 错误响应
    """
    # 记录异常
    log_error(exc, {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "traceback": traceback.format_exc()
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


def setup_exception_handlers(app):
    """
    设置异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # PMC自定义异常
    app.add_exception_handler(PMCException, pmc_exception_handler)
    
    # HTTP异常
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # 验证异常
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # 数据库异常
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Redis异常
    app.add_exception_handler(RedisError, redis_exception_handler)
    
    # 通用异常（最后注册）
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("异常处理器设置完成")


# 异常装饰器
def handle_exceptions(reraise: bool = False, default_return=None):
    """
    异常处理装饰器
    
    Args:
        reraise: 是否重新抛出异常
        default_return: 异常时的默认返回值
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except PMCException:
                if reraise:
                    raise
                return default_return
            except Exception as e:
                log_error(e, {"function": func.__name__})
                if reraise:
                    raise PMCException(f"函数执行失败: {func.__name__}")
                return default_return
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PMCException:
                if reraise:
                    raise
                return default_return
            except Exception as e:
                log_error(e, {"function": func.__name__})
                if reraise:
                    raise PMCException(f"函数执行失败: {func.__name__}")
                return default_return
        
        # 检查是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 便捷函数
def raise_business_error(message: str, details: Optional[Dict[str, Any]] = None):
    """抛出业务异常"""
    raise BusinessException(message, details)


def raise_validation_error(message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
    """抛出验证异常"""
    raise ValidationException(message, field, details)


def raise_not_found_error(resource: str, resource_id: Union[str, int] = None, details: Optional[Dict[str, Any]] = None):
    """抛出资源未找到异常"""
    raise ResourceNotFoundException(resource, resource_id, details)


def raise_auth_error(message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
    """抛出认证异常"""
    raise AuthenticationException(message, details)


def raise_permission_error(message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
    """抛出权限异常"""
    raise AuthorizationException(message, details)


def raise_conflict_error(message: str, details: Optional[Dict[str, Any]] = None):
    """抛出冲突异常"""
    raise ResourceConflictException(message, details)


def raise_rate_limit_error(message: str = "请求过于频繁", retry_after: int = None, details: Optional[Dict[str, Any]] = None):
    """抛出速率限制异常"""
    raise RateLimitException(message, retry_after, details)


# 导出主要接口
__all__ = [
    'PMCException',
    'BusinessException',
    'ValidationException',
    'AuthenticationException',
    'AuthorizationException',
    'ResourceNotFoundException',
    'ResourceConflictException',
    'DatabaseException',
    'ExternalServiceException',
    'RateLimitException',
    'ConfigurationException',
    'setup_exception_handlers',
    'handle_exceptions',
    'raise_business_error',
    'raise_validation_error',
    'raise_not_found_error',
    'raise_auth_error',
    'raise_permission_error',
    'raise_conflict_error',
    'raise_rate_limit_error'
]