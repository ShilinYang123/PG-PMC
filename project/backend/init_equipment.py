#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备数据初始化脚本
在用户数据已存在的基础上创建设备相关数据
"""

import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# 导入模型
from app.models.user import User, UserRole
from app.models.equipment import Equipment, EquipmentStatus, EquipmentType, MaintenanceRecord, MaintenanceType, EquipmentOperationLog
from app.db.database import Base

# 数据库配置
DATABASE_URL = "sqlite:///./pmc.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_equipment_data(db: Session) -> None:
    """创建设备测试数据"""
    logger.info("创建设备测试数据...")
    
    # 获取用户数据
    operators = db.query(User).filter(User.role == UserRole.OPERATOR).all()
    admin_user = db.query(User).filter(User.role == UserRole.ADMIN).first()
    
    if not operators or not admin_user:
        logger.error("未找到足够的用户数据，请先运行用户初始化脚本")
        return
    
    # 设备数据
    equipment_data = [
        {
            "name": "注塑机001",
            "model": "HM-180T",
            "serial_number": "INJ001",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间A",
            "location": "A区01号位"
        },
        {
            "name": "注塑机002",
            "model": "HM-220T",
            "serial_number": "INJ002",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间A",
            "location": "A区02号位"
        },
        {
            "name": "冲压机001",
            "model": "CP-100T",
            "serial_number": "PRS001",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间B",
            "location": "B区01号位"
        },
        {
            "name": "冲压机002",
            "model": "CP-150T",
            "serial_number": "PRS002",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间B",
            "location": "B区02号位"
        },
        {
            "name": "装配线001",
            "model": "ASM-AUTO",
            "serial_number": "ASM001",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间C",
            "location": "C区装配线"
        },
        {
            "name": "检测设备001",
            "model": "QC-3000",
            "serial_number": "QC001",
            "type": EquipmentType.TESTING,
            "workshop": "车间D",
            "location": "D区检测室"
        },
        {
            "name": "包装机001",
            "model": "PKG-AUTO",
            "serial_number": "PKG001",
            "type": EquipmentType.PRODUCTION,
            "workshop": "车间D",
            "location": "D区包装线"
        }
    ]
    
    created_equipment = []
    
    for eq_data in equipment_data:
        # 检查设备是否已存在
        existing_eq = db.query(Equipment).filter(Equipment.serial_number == eq_data["serial_number"]).first()
        if not existing_eq:
            # 随机分配操作员、维护员和管理员
            operator = random.choice(operators)
            maintainer = random.choice(operators)
            manager = admin_user
            
            equipment = Equipment(
                equipment_name=eq_data["name"],
                model=eq_data["model"],
                serial_number=eq_data["serial_number"],
                equipment_type=eq_data["type"],
                status=EquipmentStatus.RUNNING,
                workshop=eq_data["workshop"],
                location=eq_data["location"],
                operator_id=operator.id,
                maintainer_id=maintainer.id,
                manager_id=manager.id,
                purchase_date=datetime.now() - timedelta(days=random.randint(30, 365)),
                warranty_expiry=datetime.now() + timedelta(days=random.randint(365, 1095)),
                specifications=f"{eq_data['model']}型号设备，适用于{eq_data['type'].value}作业"
            )
            
            db.add(equipment)
            created_equipment.append(equipment)
            logger.info(f"创建设备: {eq_data['name']} ({eq_data['serial_number']})")
    
    # 提交设备数据
    db.commit()
    
    # 刷新设备对象以获取ID
    for eq in created_equipment:
        db.refresh(eq)
    
    logger.info(f"设备数据创建完成，共创建 {len(created_equipment)} 台设备")
    
    # 创建维护记录
    create_maintenance_records(db, created_equipment, admin_user)
    
    # 创建操作日志
    create_operation_logs(db, created_equipment, operators, admin_user)

def create_maintenance_records(db: Session, equipment_list: list, admin_user: User) -> None:
    """创建维护记录"""
    logger.info("创建维护记录...")
    
    maintenance_types = [MaintenanceType.PREVENTIVE, MaintenanceType.CORRECTIVE, MaintenanceType.EMERGENCY]
    
    for equipment in equipment_list:
        # 为每台设备创建1-3条维护记录
        num_records = random.randint(1, 3)
        
        for i in range(num_records):
            maintenance_date = datetime.now() - timedelta(days=random.randint(1, 90))
            
            record = MaintenanceRecord(
                equipment_id=equipment.id,
                maintenance_type=random.choice(maintenance_types),
                maintenance_description=f"{equipment.equipment_name}的{random.choice(['日常保养', '故障维修', '预防性维护', '紧急抢修'])}",
                planned_start_time=maintenance_date,
                planned_duration=random.randint(1, 8),
                total_cost=random.uniform(100, 2000),
                parts_replaced=random.choice([None, "轴承", "密封圈", "滤芯", "传感器"]),
                next_maintenance_date=maintenance_date + timedelta(days=random.randint(30, 90)),
                performed_by=equipment.maintainer_id
            )
            
            db.add(record)
    
    db.commit()
    logger.info("维护记录创建完成")

def create_operation_logs(db: Session, equipment_list: list, operators: list, admin_user: User) -> None:
    """创建操作日志"""
    logger.info("创建操作日志...")
    
    operation_types = ["START", "STOP", "PAUSE", "RESUME", "MAINTENANCE"]
    
    for equipment in equipment_list:
        # 为每台设备创建5-10条操作日志
        num_logs = random.randint(5, 10)
        
        for i in range(num_logs):
            operation_time = datetime.now() - timedelta(hours=random.randint(1, 168))  # 过去一周内
            
            log = EquipmentOperationLog(
                equipment_id=equipment.id,
                operation_type=random.choice(operation_types),
                operation_description=f"{equipment.equipment_name}的{random.choice(['启动操作', '停止操作', '暂停操作', '恢复操作', '维护操作'])}",
                operation_time=operation_time,
                operator_id=random.choice(operators).id,
                duration=random.randint(5, 480) / 60.0  # 转换为小时
            )
            
            db.add(log)
    
    db.commit()
    logger.info("操作日志创建完成")

def init_equipment_data():
    """初始化设备测试数据"""
    logger.info("开始初始化设备测试数据...")
    
    try:
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建设备相关数据
            create_equipment_data(db)
            
            logger.info("设备测试数据初始化完成")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"设备测试数据初始化失败: {e}")
        raise

if __name__ == "__main__":
    init_equipment_data()
    print("设备测试数据初始化完成！")
    print("\n创建的测试数据包括：")
    print("- 7台设备（注塑机、冲压机、装配线、检测设备、包装机）")
    print("- 每台设备的维护记录")
    print("- 每台设备的操作日志")