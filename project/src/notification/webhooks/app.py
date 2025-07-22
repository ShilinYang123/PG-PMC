"""微信Webhook服务应用

提供微信API回调处理的FastAPI应用。
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .routes import router as webhook_router, setup_webhook_handlers
from .status_handler import get_message_tracker, MessageTracker
from .wechat_webhook import WeChatCallbackManager
from ..exceptions import WebhookError, NotificationError
from ..config import NotificationConfig

logger = logging.getLogger(__name__)

# 全局变量
webhook_manager: Optional[WeChatCallbackManager] = None
message_tracker: Optional[MessageTracker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global webhook_manager, message_tracker
    
    # 启动时初始化
    try:
        logger.info("Starting WeChat webhook service...")
        
        # 初始化配置
        config = NotificationConfig()
        
        # 初始化webhook管理器
        webhook_manager = WeChatCallbackManager()
        
        # 设置webhook处理器
        await setup_webhook_handlers(webhook_manager)
        
        # 初始化消息跟踪器
        message_tracker = get_message_tracker()
        message_tracker.start_tracking()
        
        # 注册状态回调
        _register_status_callbacks(message_tracker)
        
        logger.info("WeChat webhook service started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start webhook service: {e}")
        raise
    
    finally:
        # 关闭时清理
        logger.info("Shutting down WeChat webhook service...")
        
        if message_tracker:
            message_tracker.stop_tracking()
        
        if webhook_manager:
            await webhook_manager.close()
        
        logger.info("WeChat webhook service shut down")


def _register_status_callbacks(tracker: MessageTracker):
    """注册状态回调"""
    from .status_handler import MessageStatusType
    
    # 消息发送成功回调
    async def on_message_sent(status_update):
        logger.info(f"Message {status_update.message_id} sent successfully")
        # 这里可以更新数据库状态
    
    # 消息发送失败回调
    async def on_message_failed(status_update):
        logger.error(f"Message {status_update.message_id} failed: {status_update.error_message}")
        # 这里可以触发重试逻辑
    
    # 用户交互回调
    async def on_user_interaction(interaction):
        logger.info(f"User {interaction.user_id} interacted: {interaction.interaction_type}")
        # 这里可以处理用户回复等
    
    tracker.add_status_callback(MessageStatusType.SENT, on_message_sent)
    tracker.add_status_callback(MessageStatusType.FAILED, on_message_failed)
    tracker.add_interaction_callback(on_user_interaction)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title="PMC WeChat Webhook Service",
        description="微信API回调处理服务",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # 添加中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 信任的主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 生产环境应该限制主机
    )
    
    # 注册路由
    app.include_router(webhook_router, prefix="/api/v1")
    
    # 全局异常处理
    @app.exception_handler(WebhookError)
    async def webhook_error_handler(request: Request, exc: WebhookError):
        """Webhook错误处理"""
        logger.error(f"Webhook error: {exc}")
        return JSONResponse(
            status_code=exc.status_code or 400,
            content={"error": str(exc), "type": "webhook_error"}
        )
    
    @app.exception_handler(NotificationError)
    async def notification_error_handler(request: Request, exc: NotificationError):
        """通知错误处理"""
        logger.error(f"Notification error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "type": "notification_error"}
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        """通用错误处理"""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "type": "internal_error"}
        )
    
    # 健康检查
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "service": "wechat-webhook",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "service": "PMC WeChat Webhook Service",
            "version": "1.0.0",
            "status": "running"
        }
    
    # 获取服务状态
    @app.get("/api/v1/status")
    async def get_service_status():
        """获取服务状态"""
        global webhook_manager, message_tracker
        
        status = {
            "webhook_manager": webhook_manager is not None,
            "message_tracker": message_tracker is not None and message_tracker._tracking_enabled,
            "handlers": []
        }
        
        if webhook_manager:
            status["handlers"] = list(webhook_manager._handlers.keys())
        
        return status
    
    # 获取消息状态
    @app.get("/api/v1/messages/{message_id}/status")
    async def get_message_status(message_id: str):
        """获取消息状态"""
        global message_tracker
        
        if not message_tracker:
            raise HTTPException(status_code=503, detail="Message tracker not available")
        
        status = message_tracker.status_handler.get_message_status(message_id)
        if not status:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return status.to_dict()
    
    # 获取消息历史
    @app.get("/api/v1/messages/{message_id}/history")
    async def get_message_history(message_id: str):
        """获取消息历史"""
        global message_tracker
        
        if not message_tracker:
            raise HTTPException(status_code=503, detail="Message tracker not available")
        
        history = message_tracker.status_handler.get_message_history(message_id)
        return [status.to_dict() for status in history]
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行应用
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )