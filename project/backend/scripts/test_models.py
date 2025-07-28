#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模型导入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = "sqlite:///./pmc_test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("开始导入模型...")

try:
    # 先导入Base
    from app.models import Base
    print("✓ Base导入成功")
    
    # 导入User模型
    from app.models.user import User
    print("✓ User模型导入成功")
    
    # 导入其他模型
    from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority
    print("✓ 生产计划模型导入成功")
    
    from app.models.progress import QualityRecord, QualityResult
    print("✓ 质量记录模型导入成功")
    
    from app.models.equipment import Equipment, MaintenanceRecord, EquipmentStatus, MaintenanceType
    print("✓ 设备模型导入成功")
    
    from app.models.order import Order, OrderStatus, OrderPriority
    print("✓ 订单模型导入成功")
    
    from app.models.material import Material, MaterialCategory, MaterialStatus
    print("✓ 物料模型导入成功")
    
    print("\n所有模型导入成功！")
    
    # 尝试创建数据库表
    print("\n开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建成功")
    
except Exception as e:
    print(f"❌ 模型导入失败: {e}")
    import traceback
    traceback.print_exc()