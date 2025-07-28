#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据初始化脚本

为PMC系统创建完整的测试数据，包括：
- 生产计划数据
- 质量检查数据
- 设备数据
- 维护记录
- 故障记录
"""

import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from typing import List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# 导入Base和所有模型 - 确保所有模型都被注册到Base.metadata
from app.db.database import Base
from app.models.user import User, UserRole, UserStatus
from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority
from app.models.progress import QualityRecord, QualityResult
from app.models.equipment import Equipment, MaintenanceRecord, EquipmentStatus, MaintenanceType, EquipmentType, MaintenanceStatus
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.material import Material, MaterialCategory, MaterialStatus

# 数据库配置
DATABASE_URL = "sqlite:///./pmc_test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_production_plans(db: Session) -> None:
    """创建生产计划测试数据"""
    logger.info("创建生产计划测试数据...")
    
    # 车间和生产线配置
    workshops = ["车间A", "车间B", "车间C", "车间D"]
    production_lines = {
        "车间A": ["生产线A1", "生产线A2"],
        "车间B": ["生产线B1", "生产线B2", "生产线B3"],
        "车间C": ["生产线C1", "生产线C2"],
        "车间D": ["生产线D1"]
    }
    
    products = [
        {"name": "5G基站设备", "model": "AAU5613", "spec": "64T64R 3.5GHz"},
        {"name": "光传输设备", "model": "ZXONE9700", "spec": "400G OTN"},
        {"name": "路由器设备", "model": "NE8000", "spec": "400G核心路由器"},
        {"name": "交换机设备", "model": "S12700", "spec": "48端口千兆交换机"},
        {"name": "服务器设备", "model": "TaiShan200", "spec": "2U机架式服务器"}
    ]
    
    # 创建30个生产计划
    for i in range(30):
        workshop = random.choice(workshops)
        production_line = random.choice(production_lines[workshop])
        product = random.choice(products)
        
        # 随机生成时间
        start_offset = random.randint(-30, 10)  # 开始时间：30天前到10天后
        duration = random.randint(5, 30)  # 持续时间：5-30天
        
        planned_start = datetime.now() + timedelta(days=start_offset)
        planned_end = planned_start + timedelta(days=duration)
        
        # 根据开始时间确定状态
        if planned_start > datetime.now():
            status = PlanStatus.PLANNED
            progress = 0
        elif planned_end < datetime.now():
            status = random.choice([PlanStatus.COMPLETED, PlanStatus.DELAYED])
            progress = 100 if status == PlanStatus.COMPLETED else random.randint(80, 95)
        else:
            status = PlanStatus.IN_PROGRESS
            progress = random.randint(10, 90)
        
        plan = ProductionPlan(
            plan_number=f"PLAN{datetime.now().year}{i+1:04d}",
            plan_name=f"{product['name']}生产计划{i+1}",
            order_id=f"ORD{datetime.now().year}{random.randint(1000, 9999)}",
            product_name=product["name"],
            product_model=product["model"],
            product_spec=product["spec"],
            planned_quantity=random.randint(10, 200),
            unit="台",
            planned_start_date=planned_start.date(),
            planned_end_date=planned_end.date(),
            actual_start_date=planned_start.date() if status != PlanStatus.PLANNED else None,
            actual_end_date=planned_end.date() if status == PlanStatus.COMPLETED else None,
            status=status,
            priority=random.choice(list(PlanPriority)),
            workshop=workshop,
            production_line=production_line,
            responsible_person=random.choice(["张三", "李四", "王五", "赵六", "钱七"]),
            team_members="张三,李四,王五",
            process_flow="下料->加工->装配->测试->包装",
            progress=progress,
            estimated_cost=Decimal(str(random.randint(10000, 100000))),
            actual_cost=Decimal(str(random.randint(8000, 120000))) if status != PlanStatus.PLANNED else None,
            remark=f"生产计划{i+1}备注信息",
            created_by="admin",
            updated_by="admin"
        )
        
        db.add(plan)
    
    db.commit()
    logger.info("生产计划测试数据创建完成")

def create_quality_records(db: Session) -> None:
    """创建质量检查测试数据"""
    logger.info("创建质量检查测试数据...")
    
    # 获取所有生产计划
    plans = db.query(ProductionPlan).all()
    
    defect_types = [
        "外观缺陷", "尺寸偏差", "功能异常", "性能不达标", 
        "材料缺陷", "工艺缺陷", "装配错误", "测试失败"
    ]
    
    inspectors = ["质检员A", "质检员B", "质检员C", "质检员D"]
    
    # 为每个生产计划创建多个质量检查记录
    for plan in plans:
        # 每个计划创建3-8个质量检查记录
        num_records = random.randint(3, 8)
        
        for i in range(num_records):
            # 检查时间在计划期间内
            if plan.actual_start_date:
                start_date = plan.actual_start_date
                end_date = plan.actual_end_date or datetime.now().date()
                
                # 随机生成检查时间
                days_diff = (end_date - start_date).days
                if days_diff > 0:
                    check_offset = random.randint(0, days_diff)
                    check_date = start_date + timedelta(days=check_offset)
                else:
                    check_date = start_date
            else:
                check_date = datetime.now().date()
            
            # 80%的概率通过检查
            result = QualityResult.PASS if random.random() < 0.8 else QualityResult.FAIL
            
            quality_record = QualityRecord(
                plan_id=plan.id,
                product_name=plan.product_name,
                batch_number=f"BATCH{plan.id}{i+1:03d}",
                check_date=check_date,
                check_type=random.choice(["入料检验", "过程检验", "成品检验", "出厂检验"]),
                check_items="外观,尺寸,功能,性能",
                check_quantity=random.randint(5, 50),
                qualified_quantity=random.randint(4, 50) if result == QualityResult.PASS else random.randint(1, 30),
                defect_quantity=random.randint(0, 5) if result == QualityResult.FAIL else 0,
                defect_type=random.choice(defect_types) if result == QualityResult.FAIL else None,
                defect_description=f"发现{random.choice(defect_types)}问题" if result == QualityResult.FAIL else None,
                result=result,
                inspector=random.choice(inspectors),
                check_standard="GB/T 19001-2016",
                remark=f"质量检查记录{i+1}",
                created_by="admin",
                updated_by="admin"
            )
            
            db.add(quality_record)
    
    db.commit()
    logger.info("质量检查测试数据创建完成")

def create_users(db: Session) -> None:
    """创建用户测试数据"""
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
    
    db.commit()
    logger.info("用户测试数据创建完成")

def create_equipment_data(db: Session) -> None:
    """创建设备测试数据"""
    logger.info("创建设备测试数据...")
    
    # 获取用户ID
    operators = db.query(User).filter(User.role == UserRole.OPERATOR, User.department == "生产部").all()
    maintainers = db.query(User).filter(User.role == UserRole.OPERATOR, User.department == "设备部").all()
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    equipment_types = [
        {"category": EquipmentType.PRODUCTION, "names": ["数控车床", "数控铣床", "加工中心", "磨床"]},
        {"category": EquipmentType.PRODUCTION, "names": ["装配线", "焊接机器人", "螺丝机", "压装机"]},
        {"category": EquipmentType.TESTING, "names": ["三坐标测量机", "光学检测仪", "电性能测试仪", "环境试验箱"]},
        {"category": EquipmentType.TRANSPORT, "names": ["AGV小车", "堆垛机", "输送线", "立体库"]}
    ]
    
    manufacturers = ["西门子", "发那科", "哈斯", "马扎克", "德马吉", "海克斯康"]
    workshops = ["车间A", "车间B", "车间C", "车间D"]
    
    # 创建50台设备
    for i in range(50):
        equipment_type = random.choice(equipment_types)
        equipment_name = random.choice(equipment_type["names"])
        
        # 设备状态分布：70%正常，15%维护中，10%故障，5%停用
        status_weights = [0.7, 0.15, 0.1, 0.05]
        status = random.choices(
            [EquipmentStatus.RUNNING, EquipmentStatus.IDLE, EquipmentStatus.MAINTENANCE, EquipmentStatus.BREAKDOWN],
            weights=status_weights
        )[0]
        
        purchase_date = datetime.now().date() - timedelta(days=random.randint(365, 3650))  # 1-10年前购买
        
        equipment = Equipment(
            equipment_code=f"EQ{i+1:04d}",
            equipment_name=f"{equipment_name}{i+1:02d}",
            equipment_type=equipment_type["category"],
            model=f"Model-{random.randint(1000, 9999)}",
            manufacturer=random.choice(manufacturers),
            purchase_date=purchase_date,
            purchase_cost=random.randint(100000, 2000000),
            warranty_expiry=purchase_date + timedelta(days=random.randint(365, 1095)),  # 1-3年保修
            status=status,
            workshop=random.choice(workshops),
            location=f"{random.choice(workshops)}-{random.randint(1, 20):02d}位",
            specifications=f"功率: {random.randint(5, 50)}kW, 精度: ±{random.uniform(0.01, 0.1):.2f}mm",
            total_runtime=random.randint(1000, 50000),  # 总运行时间
            description=f"{equipment_name}设备，用于{equipment_type['category']}",
            remarks=f"设备{i+1}备注信息",
            operator_id=random.choice(operators).id if operators else None,
            maintainer_id=random.choice(maintainers).id if maintainers else None,
            manager_id=admin_user.id if admin_user else None
        )
        
        db.add(equipment)
    
    db.commit()
    logger.info("设备测试数据创建完成")

def create_maintenance_records(db: Session) -> None:
    """创建维护记录测试数据"""
    logger.info("创建维护记录测试数据...")
    
    # 获取所有设备
    equipment_list = db.query(Equipment).all()
    
    maintenance_contents = [
        "日常保养", "润滑油更换", "滤芯更换", "皮带调整", "精度校准",
        "电气检查", "机械检查", "安全检查", "清洁保养", "预防性维护"
    ]
    
    parts_replaced = [
        "润滑油", "滤芯", "皮带", "轴承", "密封件",
        "电机", "传感器", "刀具", "夹具", "导轨"
    ]
    
    maintenance_persons = ["维修工A", "维修工B", "维修工C", "维修工D"]
    
    # 为每台设备创建维护记录
    for equipment in equipment_list:
        # 每台设备创建2-10个维护记录
        num_records = random.randint(2, 10)
        
        for i in range(num_records):
            # 维护时间在设备购买日期之后
            days_since_purchase = (datetime.now().date() - equipment.purchase_date).days
            maintenance_offset = random.randint(30, days_since_purchase)
            maintenance_date = equipment.purchase_date + timedelta(days=maintenance_offset)
            
            # 维护类型分布：60%预防性，25%故障性，15%改进性
            maintenance_type = random.choices(
                [MaintenanceType.PREVENTIVE, MaintenanceType.CORRECTIVE, MaintenanceType.IMPROVEMENT],
                weights=[0.6, 0.25, 0.15]
            )[0]
            
            maintenance_record = MaintenanceRecord(
                maintenance_number=f"MAINT{equipment.id}{i+1:03d}",
                equipment_id=equipment.id,
                maintenance_type=maintenance_type,
                planned_start_time=maintenance_date,
                planned_end_time=maintenance_date + timedelta(hours=random.uniform(0.5, 8.0)),
                actual_start_time=maintenance_date,
                actual_end_time=maintenance_date + timedelta(hours=random.uniform(0.5, 8.0)),
                maintenance_description=random.choice(maintenance_contents),
                parts_replaced=random.choice(parts_replaced) if random.random() < 0.4 else None,
                total_cost=random.randint(500, 10000),
                next_maintenance_date=maintenance_date + timedelta(days=90),
                status=MaintenanceStatus.COMPLETED,
                remarks=f"维护记录{i+1}"
            )
            
            db.add(maintenance_record)
    
    db.commit()
    logger.info("维护记录测试数据创建完成")

def create_orders(db: Session) -> None:
    """创建订单测试数据"""
    logger.info("创建订单测试数据...")
    
    customers = [
        {"name": "华为技术有限公司", "contact": "张先生", "phone": "13800138000"},
        {"name": "中兴通讯股份有限公司", "contact": "李女士", "phone": "13800138001"},
        {"name": "中国移动通信集团", "contact": "王经理", "phone": "13800138002"},
        {"name": "中国电信集团", "contact": "赵总", "phone": "13800138003"},
        {"name": "中国联通集团", "contact": "钱部长", "phone": "13800138004"}
    ]
    
    products = [
        {"name": "5G基站设备", "model": "AAU5613", "spec": "64T64R 3.5GHz", "price": 50000},
        {"name": "光传输设备", "model": "ZXONE9700", "spec": "400G OTN", "price": 80000},
        {"name": "路由器设备", "model": "NE8000", "spec": "400G核心路由器", "price": 120000},
        {"name": "交换机设备", "model": "S12700", "spec": "48端口千兆交换机", "price": 30000},
        {"name": "服务器设备", "model": "TaiShan200", "spec": "2U机架式服务器", "price": 25000}
    ]
    
    # 创建20个订单
    for i in range(20):
        customer = random.choice(customers)
        product = random.choice(products)
        quantity = random.randint(10, 200)
        
        order_date = datetime.now() - timedelta(days=random.randint(1, 60))
        delivery_date = order_date + timedelta(days=random.randint(30, 90))
        
        # 订单状态分布
        if delivery_date < datetime.now():
            status = random.choice([OrderStatus.COMPLETED, OrderStatus.IN_PRODUCTION])
        else:
            status = random.choice([OrderStatus.CONFIRMED, OrderStatus.IN_PRODUCTION])
        
        order = Order(
            order_no=f"ORD{datetime.now().year}{random.randint(1000, 9999)}{i+1:04d}",
            customer_name=customer["name"],
            contact_person=customer["contact"],
            contact_phone=customer["phone"],
            product_name=product["name"],
            product_model=product["model"],
            quantity=quantity,
            unit="台",
            unit_price=product["price"],
            total_amount=quantity * product["price"],
            order_date=order_date,
            delivery_date=delivery_date,
            status=status,
            priority=random.choice(list(OrderPriority)),
            delivery_address=f"{customer['name']}总部",
            technical_requirements=f"符合行业标准，{product['spec']}",
            quality_standards="ISO9001质量标准",
            remark=f"订单{i+1}备注信息",
            created_by="admin",
            updated_by="admin"
        )
        
        db.add(order)
    
    db.commit()
    logger.info("订单测试数据创建完成")

def create_materials(db: Session) -> None:
    """创建物料测试数据"""
    logger.info("创建物料测试数据...")
    
    materials_data = [
        {"category": MaterialCategory.STANDARD_PART, "items": [
            {"name": "射频芯片", "spec": "3.5GHz 64通道", "price": 1200},
            {"name": "基带芯片", "spec": "5G NR", "price": 800},
            {"name": "功放芯片", "spec": "100W", "price": 600},
            {"name": "滤波器", "spec": "3.5GHz", "price": 300}
        ]},
        {"category": MaterialCategory.SEMI_FINISHED, "items": [
            {"name": "散热器", "spec": "铝合金", "price": 150},
            {"name": "外壳", "spec": "压铸铝", "price": 200},
            {"name": "连接器", "spec": "N型", "price": 50},
            {"name": "天线", "spec": "64T64R", "price": 500}
        ]},
        {"category": MaterialCategory.RAW_MATERIAL, "items": [
            {"name": "PCB板", "spec": "8层板 FR4", "price": 800},
            {"name": "电容", "spec": "1000uF", "price": 5},
            {"name": "电阻", "spec": "1K欧", "price": 2},
            {"name": "电感", "spec": "10uH", "price": 8}
        ]}
    ]
    
    suppliers = ["海思半导体", "深南电路", "立讯精密", "富士康", "比亚迪"]
    
    material_count = 1
    for category_data in materials_data:
        for item in category_data["items"]:
            # 使用时间戳确保编码唯一
            timestamp = int(datetime.now().timestamp() * 1000) % 100000
            material = Material(
                material_code=f"MAT{timestamp}{material_count:03d}",
                material_name=item["name"],
                specification=item["spec"],
                unit="片" if "芯片" in item["name"] else "个",
                category=category_data["category"],
                current_stock=random.randint(100, 2000),
                safety_stock=random.randint(50, 200),
                max_stock=random.randint(1000, 5000),
                unit_price=item["price"],
                primary_supplier=random.choice(suppliers),
                status=MaterialStatus.NORMAL,
                remark=f"物料{material_count}备注信息",
                created_by="admin",
                updated_by="admin"
            )
            
            db.add(material)
            material_count += 1
    
    db.commit()
    logger.info("物料测试数据创建完成")

def init_test_data():
    """初始化所有测试数据"""
    logger.info("开始初始化测试数据...")
    
    try:
        # 确保所有模型都被导入
        from app.models import user, equipment, order, material, production_plan, progress
        
        # 创建数据库表
        logger.info("创建数据库表...")
        Base.metadata.create_all(bind=engine)
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建各类测试数据（注意顺序：先创建用户，再创建依赖用户的数据）
            create_users(db)  # 先创建用户
            create_orders(db)
            create_materials(db)
            create_equipment_data(db)  # 设备依赖用户
            create_maintenance_records(db)
            create_production_plans(db)
            create_quality_records(db)
            
            logger.info("测试数据初始化完成")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"测试数据初始化失败: {e}")
        raise

if __name__ == "__main__":
    init_test_data()
    print("测试数据初始化完成！")
    print("\n创建的测试数据包括：")
    print("- 9个用户（1个管理员 + 5个操作员 + 3个维护员）")
    print("- 20个订单")
    print("- 16种物料")
    print("- 50台设备")
    print("- 100-500个维护记录")
    print("- 30个生产计划")
    print("- 90-240个质量检查记录")
    print("\n现在可以测试报表功能了！")