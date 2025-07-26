from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

# 导入路由模块
from app.api.api import api_router
from app.core.config import settings
from app.db.database import engine, Base
from app.core.logging import setup_logging

# 设置日志
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("PMC应用启动中...")
    
    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    yield
    
    logger.info("PMC应用关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="PMC全流程管理系统后端API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

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