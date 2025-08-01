from fastapi import APIRouter
from app.api.endpoints import auth, users, orders, production_plans, materials, bom, progress, scheduling, wechat, notifications, reminder, reminder_notifications, import_export, reports, backup
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

# BOM管理路由
api_router.include_router(bom.router, prefix="/bom", tags=["BOM管理"])

# 进度跟踪路由
api_router.include_router(progress.router, prefix="/progress", tags=["进度跟踪"])

# 排产管理路由
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["排产管理"])

# 微信通知路由
api_router.include_router(wechat.router, prefix="/wechat", tags=["微信通知"])

# 通知系统路由
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知系统"])

# 催办管理路由
api_router.include_router(reminder.router, prefix="/reminders", tags=["催办管理"])

# 催办通知路由
api_router.include_router(reminder_notifications.router, prefix="/reminder-notifications", tags=["催办通知"])

# 导入导出路由
api_router.include_router(import_export.router, prefix="/import-export", tags=["数据导入导出"])

# 报表生成路由
api_router.include_router(reports.router, prefix="/reports", tags=["报表生成"])

# 数据备份恢复路由
api_router.include_router(backup.router, prefix="/backup", tags=["数据备份恢复"])