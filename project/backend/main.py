from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.core.database import init_database, close_database
from app.db.database import engine, Base
from app.api.v1.api import api_router

# 设置日志
setup_logging(log_level=settings.LOG_LEVEL, debug=settings.DEBUG)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("PMC系统启动中...")
    
    try:
        # 初始化数据库连接
        await init_database()
        logger.info("数据库连接初始化完成")
        
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    # 根据配置设置日志级别
    if settings.LOG_LEVEL:
        import logging
        logging.getLogger().setLevel(settings.LOG_LEVEL)
    
    # 设置调试模式
    if settings.DEBUG:
        logger.info("调试模式已启用")
    
    logger.info("PMC系统启动完成")
    
    yield
    
    # 关闭时
    logger.info("PMC系统关闭中...")
    
    try:
        # 关闭数据库连接
        await close_database()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"数据库关闭失败: {e}")
    
    logger.info("PMC系统已关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PMC全流程图表界面应用 - 生产管理与控制系统",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# 设置中间件
setup_middleware(app)

# 设置异常处理器
setup_exception_handlers(app)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态文件服务
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # 静态目录不存在时创建
    import os
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("创建静态文件目录")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "PMC全流程管理系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "PMC Backend API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )