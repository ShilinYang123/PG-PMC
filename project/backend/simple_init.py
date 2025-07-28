#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的测试数据初始化脚本
只创建用户数据，避免外键依赖问题
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# 只导入用户模型
from app.models.user import User, UserRole, UserStatus
from app.db.database import Base

# 数据库配置
DATABASE_URL = "sqlite:///./pmc.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_users_only(db: Session) -> None:
    """只创建用户测试数据"""
    logger.info("创建用户测试数据...")
    
    # 检查是否已存在管理员用户
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@pgpmc.com",
            phone="13800138000",
            full_name="系统管理员",
            employee_id="ADMIN001",
            department="信息技术部",
            position="系统管理员",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            workshop="总部",
            hashed_password="admin123",
            created_by="system",
            updated_by="system"
        )
        db.add(admin_user)
        logger.info("创建管理员用户: admin")
    
    # 创建操作员用户
    operators = [
        {"username": "operator01", "name": "张操作员", "employee_id": "OP001"},
        {"username": "operator02", "name": "李操作员", "employee_id": "OP002"},
        {"username": "operator03", "name": "王操作员", "employee_id": "OP003"},
        {"username": "operator04", "name": "赵操作员", "employee_id": "OP004"},
        {"username": "operator05", "name": "钱操作员", "employee_id": "OP005"}
    ]
    
    for i, op_data in enumerate(operators):
        existing_user = db.query(User).filter(User.username == op_data["username"]).first()
        if not existing_user:
            user = User(
                username=op_data["username"],
                email=f"{op_data['username']}@pgpmc.com",
                phone=f"1380013800{i+1}",
                full_name=op_data["name"],
                employee_id=op_data["employee_id"],
                department="生产部",
                position="设备操作员",
                role=UserRole.OPERATOR,
                status=UserStatus.ACTIVE,
                is_active=True,
                workshop=f"车间{chr(65+i%4)}",  # 车间A-D
                hashed_password="123456",
                created_by="admin",
                updated_by="admin"
            )
            db.add(user)
            logger.info(f"创建操作员用户: {op_data['username']}")
    
    # 创建维护员用户
    maintainers = [
        {"username": "maintainer01", "name": "维修工A", "employee_id": "MT001"},
        {"username": "maintainer02", "name": "维修工B", "employee_id": "MT002"},
        {"username": "maintainer03", "name": "维修工C", "employee_id": "MT003"}
    ]
    
    for i, mt_data in enumerate(maintainers):
        existing_user = db.query(User).filter(User.username == mt_data["username"]).first()
        if not existing_user:
            user = User(
                username=mt_data["username"],
                email=f"{mt_data['username']}@pgpmc.com",
                phone=f"1380013801{i+1}",
                full_name=mt_data["name"],
                employee_id=mt_data["employee_id"],
                department="设备部",
                position="设备维护员",
                role=UserRole.OPERATOR,
                status=UserStatus.ACTIVE,
                is_active=True,
                workshop="设备部",
                hashed_password="123456",
                created_by="admin",
                updated_by="admin"
            )
            db.add(user)
            logger.info(f"创建维护员用户: {mt_data['username']}")
    
    db.commit()
    logger.info("用户测试数据创建完成")

def init_simple_data():
    """初始化简单测试数据"""
    logger.info("开始初始化用户测试数据...")
    
    try:
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 只创建用户数据
            create_users_only(db)
            
            logger.info("用户测试数据初始化完成")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"测试数据初始化失败: {e}")
        raise

if __name__ == "__main__":
    init_simple_data()
    print("用户测试数据初始化完成！")
    print("\n创建的测试数据包括：")
    print("- 1个管理员用户: admin")
    print("- 5个操作员用户: operator01-05")
    print("- 3个维护员用户: maintainer01-03")