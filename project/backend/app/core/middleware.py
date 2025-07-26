#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMC系统中间件
提供请求处理、认证、日志记录、CORS等中间件功能
"""

import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from loguru import logger
import json

from .logging import log_access, log_performance, log_error
from .security import verify_token, get_current_user
from .config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录所有HTTP请求的详细信息
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求信息
        logger.bind(request_id=request_id).info(
            f"Request started: {request.method} {request.url} | "
            f"Client: {client_ip} | User-Agent: {user_agent}"
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = (time.time() - start_time) * 1000
            
            # 获取用户信息（如果有）
            user_id = getattr(request.state, 'user_id', None)
            
            # 记录访问日志
            log_access(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                response_time=process_time,
                user_id=user_id
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            
            logger.bind(request_id=request_id).info(
                f"Request completed: {response.status_code} | "
                f"Time: {process_time:.2f}ms"
            )
            
            return response
            
        except Exception as e:
            # 计算错误响应时间
            process_time = (time.time() - start_time) * 1000
            
            # 记录错误
            log_error(e, {
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'client_ip': client_ip,
                'process_time': process_time
            })
            
            logger.bind(request_id=request_id).error(
                f"Request failed: {str(e)} | Time: {process_time:.2f}ms"
            )
            
            # 返回错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "请求处理失败",
                    "request_id": request_id
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{process_time:.2f}ms"
                }
            )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    处理JWT令牌验证和用户认证
    """
    
    # 不需要认证的路径
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/static"
    }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 检查是否需要认证
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # 获取Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            return self._unauthorized_response("缺少认证令牌")
        
        # 验证Bearer令牌格式
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return self._unauthorized_response("无效的认证方案")
        except ValueError:
            return self._unauthorized_response("无效的认证格式")
        
        # 验证令牌
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                return self._unauthorized_response("无效的令牌载荷")
            
            # 将用户信息添加到请求状态
            request.state.user_id = user_id
            request.state.token_payload = payload
            
            # 记录认证成功
            logger.bind(user_id=user_id).debug(f"User authenticated: {user_id}")
            
            return await call_next(request)
            
        except HTTPException as e:
            return self._unauthorized_response(e.detail)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return self._unauthorized_response("认证失败")
    
    def _is_exempt_path(self, path: str) -> bool:
        """检查路径是否免于认证"""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _unauthorized_response(self, message: str) -> JSONResponse:
        """返回未授权响应"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Unauthorized",
                "message": message
            },
            headers={"WWW-Authenticate": "Bearer"}
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    防止API滥用
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的调用次数
        self.period = period  # 时间窗口（秒）
        self.clients = {}  # 客户端请求记录
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取客户端标识
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 检查速率限制
        if self._is_rate_limited(client_id, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"请求过于频繁，请在{self.period}秒后重试"
                },
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.period))
                }
            )
        
        # 记录请求
        self._record_request(client_id, current_time)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        remaining = self._get_remaining_calls(client_id, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户ID
        if hasattr(request.state, 'user_id'):
            return f"user:{request.state.user_id}"
        
        # 使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _cleanup_expired_records(self, current_time: float) -> None:
        """清理过期记录"""
        expired_clients = []
        for client_id, requests in self.clients.items():
            # 移除过期请求
            self.clients[client_id] = [
                req_time for req_time in requests
                if current_time - req_time < self.period
            ]
            # 标记空记录的客户端
            if not self.clients[client_id]:
                expired_clients.append(client_id)
        
        # 删除空记录
        for client_id in expired_clients:
            del self.clients[client_id]
    
    def _is_rate_limited(self, client_id: str, current_time: float) -> bool:
        """检查是否超出速率限制"""
        if client_id not in self.clients:
            return False
        
        # 计算时间窗口内的请求数
        recent_requests = [
            req_time for req_time in self.clients[client_id]
            if current_time - req_time < self.period
        ]
        
        return len(recent_requests) >= self.calls
    
    def _record_request(self, client_id: str, current_time: float) -> None:
        """记录请求"""
        if client_id not in self.clients:
            self.clients[client_id] = []
        
        self.clients[client_id].append(current_time)
    
    def _get_remaining_calls(self, client_id: str, current_time: float) -> int:
        """获取剩余调用次数"""
        if client_id not in self.clients:
            return self.calls
        
        recent_requests = [
            req_time for req_time in self.clients[client_id]
            if current_time - req_time < self.period
        ]
        
        return max(0, self.calls - len(recent_requests))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件
    添加安全相关的HTTP头
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:;"
        )
        
        # 在生产环境中添加HSTS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    错误处理中间件
    统一处理未捕获的异常
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # 重新抛出HTTP异常，让FastAPI处理
            raise
        except Exception as e:
            # 记录未捕获的异常
            request_id = getattr(request.state, 'request_id', 'unknown')
            log_error(e, {
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url)
            })
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "服务器内部错误",
                    "request_id": request_id
                }
            )


def setup_middleware(app):
    """
    设置应用中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 错误处理中间件（最外层）
    app.add_middleware(ErrorHandlingMiddleware)
    
    # 安全头中间件
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 速率限制中间件
    if settings.ENABLE_RATE_LIMIT:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_CALLS,
            period=settings.RATE_LIMIT_PERIOD
        )
    
    # 认证中间件
    if settings.ENABLE_AUTH:
        app.add_middleware(AuthenticationMiddleware)
    
    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # GZIP压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # CORS中间件（最内层）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
    
    logger.info("中间件设置完成")


# 导出主要接口
__all__ = [
    'RequestLoggingMiddleware',
    'AuthenticationMiddleware',
    'RateLimitMiddleware',
    'SecurityHeadersMiddleware',
    'ErrorHandlingMiddleware',
    'setup_middleware'
]