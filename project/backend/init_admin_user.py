#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化管理员用户脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models.user import User, UserRole, UserStatus
from datetime import datetime

def create_admin_user():
    """创建管理员用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在admin用户
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("Admin用户已存在")
            print(f"用户名: {existing_user.username}")
            print(f"角色: {existing_user.role}")
            print(f"状态: {existing_user.status}")
            return
        
        # 创建admin用户
        admin_user = User(
            username="admin",
            email="admin@example.com",
            phone="13800138000",
            hashed_password="admin123",  # 实际应用中应该加密
            full_name="系统管理员",
            employee_id="ADMIN001",
            department="IT部门",
            position="系统管理员",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            is_superuser=True,
            login_count=0,
            failed_login_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin用户创建成功！")
        print(f"用户名: {admin_user.username}")
        print(f"密码: admin123")
        print(f"角色: {admin_user.role}")
        print(f"状态: {admin_user.status}")
        
    except Exception as e:
        print(f"创建admin用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()