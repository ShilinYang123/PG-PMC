from fastapi import APIRouter
from app.api.endpoints import auth, users, orders, production_plans, materials, progress, scheduling, wechat
from app.api.v1.endpoints import config

api_router = APIRouter()

# 配置管理路由
api_router.include_router(config.router, prefix="/config", tags=["配置管理"])

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# 订单管理路由
api_router.include_router(orders.router, prefix="/orders", tags=["订单管理"])

# 生产计划路由
api_router.include_router(production_plans.router, prefix="/production-plans", tags=["生产计划"])

# 物料管理路由
api_router.include_router(materials.router, prefix="/materials", tags=["物料管理"])

# 进度跟踪路由
api_router.include_router(progress.router, prefix="/progress", tags=["进度跟踪"])

# 排产管理路由
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["排产管理"])

# 微信通知路由
api_router.include_router(wechat.router, prefix="/wechat", tags=["微信通知"])