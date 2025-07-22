"""Webhook路由处理器

提供FastAPI路由，用于接收各种通知渠道的webhook回调。
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from .wechat_webhook import get_callback_manager, WeChatWebhookHandler
from ..exceptions import WebhookError

logger = logging.getLogger(__name__)

# 创建路由器
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.post("/wechat/{handler_name}")
async def handle_wechat_webhook(handler_name: str, request: Request) -> JSONResponse:
    """处理微信webhook回调
    
    Args:
        handler_name: 处理器名称
        request: FastAPI请求对象
        
    Returns:
        JSON响应
    """
    try:
        # 获取请求头和请求体
        headers = dict(request.headers)
        body = await request.body()
        
        # 获取回调管理器
        callback_manager = get_callback_manager()
        
        # 处理webhook请求
        result = await callback_manager.handle_webhook(handler_name, headers, body)
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except WebhookError as e:
        logger.error(f"Webhook error for handler '{handler_name}': {e}")
        raise HTTPException(
            status_code=e.status_code or 400,
            detail={
                "error": "webhook_error",
                "message": str(e),
                "handler": handler_name
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler '{handler_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Internal server error",
                "handler": handler_name
            }
        )


@webhook_router.get("/wechat/{handler_name}/verify")
async def verify_wechat_webhook(handler_name: str, request: Request) -> JSONResponse:
    """验证微信webhook配置
    
    用于微信开发者验证URL有效性。
    
    Args:
        handler_name: 处理器名称
        request: FastAPI请求对象
        
    Returns:
        验证响应
    """
    try:
        # 获取查询参数
        query_params = dict(request.query_params)
        
        # 微信验证参数
        signature = query_params.get('signature')
        timestamp = query_params.get('timestamp')
        nonce = query_params.get('nonce')
        echostr = query_params.get('echostr')
        
        if not all([signature, timestamp, nonce, echostr]):
            raise HTTPException(
                status_code=400,
                detail="Missing required verification parameters"
            )
        
        # 获取处理器
        callback_manager = get_callback_manager()
        handler = callback_manager.get_handler(handler_name)
        
        if not handler:
            raise HTTPException(
                status_code=404,
                detail=f"Handler '{handler_name}' not found"
            )
        
        # 验证签名
        headers = {
            'signature': signature,
            'timestamp': timestamp,
            'nonce': nonce
        }
        
        if handler.verify_signature(headers, b''):
            # 验证成功，返回echostr
            return JSONResponse(
                status_code=200,
                content=echostr
            )
        else:
            raise HTTPException(
                status_code=403,
                detail="Invalid signature"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in webhook verification for '{handler_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@webhook_router.get("/health")
async def webhook_health_check() -> JSONResponse:
    """Webhook服务健康检查
    
    Returns:
        健康状态
    """
    callback_manager = get_callback_manager()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "handlers": list(callback_manager.handlers.keys()),
            "timestamp": datetime.now().isoformat()
        }
    )


@webhook_router.get("/handlers")
async def list_webhook_handlers() -> JSONResponse:
    """列出所有webhook处理器
    
    Returns:
        处理器列表
    """
    callback_manager = get_callback_manager()
    
    handlers_info = {}
    for name, handler in callback_manager.handlers.items():
        handlers_info[name] = {
            "type": "wechat",
            "has_secret": bool(handler.secret),
            "has_token": bool(handler.token),
            "has_encoding_key": bool(handler.encoding_aes_key)
        }
    
    return JSONResponse(
        status_code=200,
        content={
            "handlers": handlers_info,
            "total": len(handlers_info)
        }
    )


def setup_webhook_handlers():
    """设置默认的webhook处理器"""
    import os
    from ..config import get_notification_config
    
    try:
        config = get_notification_config()
        callback_manager = get_callback_manager()
        
        # 设置企业微信API处理器
        if config and 'channels' in config.config:
            for channel_name, channel_config in config.config['channels'].items():
                if channel_config.get('type') == 'WECHAT_API':
                    settings = channel_config.get('settings', {})
                    
                    handler = WeChatWebhookHandler(
                        token=settings.get('webhook_token'),
                        encoding_aes_key=settings.get('encoding_aes_key')
                    )
                    
                    callback_manager.add_handler(f"api_{channel_name}", handler)
                    logger.info(f"Added WeChat API webhook handler: api_{channel_name}")
                
                elif channel_config.get('type') == 'WECHAT_BOT':
                    settings = channel_config.get('settings', {})
                    
                    handler = WeChatWebhookHandler(
                        secret=settings.get('secret')
                    )
                    
                    callback_manager.add_handler(f"bot_{channel_name}", handler)
                    logger.info(f"Added WeChat Bot webhook handler: bot_{channel_name}")
        
        # 从环境变量设置默认处理器
        wechat_webhook_token = os.getenv('WECHAT_WEBHOOK_TOKEN')
        wechat_webhook_secret = os.getenv('WECHAT_WEBHOOK_SECRET')
        
        if wechat_webhook_token or wechat_webhook_secret:
            default_handler = WeChatWebhookHandler(
                secret=wechat_webhook_secret,
                token=wechat_webhook_token
            )
            callback_manager.add_handler('default', default_handler)
            logger.info("Added default WeChat webhook handler")
            
    except Exception as e:
        logger.error(f"Error setting up webhook handlers: {e}")


# 导入datetime用于健康检查
from datetime import datetime