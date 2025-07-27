from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.models import Base
from app.models.user import User, UserRole, UserStatus
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority
from app.models.material import Material, BOM, BOMItem, PurchaseOrder, PurchaseOrderItem, MaterialCategory, MaterialStatus, PurchaseStatus
from app.models.progress import ProgressRecord, StageRecord, QualityRecord, ProgressUpdate, ProgressStatus, QualityResult
from app.models.scheduling import ProductionOrder, Equipment, Material as SchedulingMaterial, ScheduleLog, ScheduleRule, ScheduleOptimization
from app.models.wechat import WeChatMessage, WeChatConfig, NotificationRule, MessageTemplate, MessageQueue, DeliveryLog, MessageStats
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """创建所有数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise

def init_admin_user(db: Session):
    """初始化管理员用户"""
    try:
        # 检查是否已存在管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            logger.info("管理员用户已存在")
            return admin_user
        
        # 创建管理员用户
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
            is_superuser=True,
            workshop="总部",
            timezone="Asia/Shanghai",
            language="zh-CN",
            theme="light",
            created_by="system",
            updated_by="system"
        )
        
        # 设置默认密码 (实际应用中应该使用加密)
        admin_user.hashed_password = "admin123"  # 这里应该使用bcrypt等加密
        admin_user.password_changed_at = datetime.now()
        admin_user.password_expires_at = datetime.now() + timedelta(days=90)
        
        # 设置管理员权限
        admin_permissions = [
            "user:create", "user:read", "user:update", "user:delete",
            "order:create", "order:read", "order:update", "order:delete",
            "plan:create", "plan:read", "plan:update", "plan:delete",
            "material:create", "material:read", "material:update", "material:delete",
            "progress:create", "progress:read", "progress:update", "progress:delete",
            "system:config", "system:backup", "system:monitor"
        ]
        admin_user.set_permissions(admin_permissions)
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"管理员用户创建成功: {admin_user.username}")
        return admin_user
        
    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        db.rollback()
        raise

def init_sample_users(db: Session):
    """初始化示例用户"""
    try:
        sample_users = [
            {
                "username": "manager01",
                "email": "manager01@pgpmc.com",
                "phone": "13800138001",
                "full_name": "张经理",
                "employee_id": "MGR001",
                "department": "生产部",
                "position": "生产经理",
                "role": UserRole.MANAGER,
                "workshop": "第一车间"
            },
            {
                "username": "supervisor01",
                "email": "supervisor01@pgpmc.com",
                "phone": "13800138002",
                "full_name": "李主管",
                "employee_id": "SUP001",
                "department": "生产部",
                "position": "车间主管",
                "role": UserRole.SUPERVISOR,
                "workshop": "第一车间"
            },
            {
                "username": "operator01",
                "email": "operator01@pgpmc.com",
                "phone": "13800138003",
                "full_name": "王操作员",
                "employee_id": "OPR001",
                "department": "生产部",
                "position": "设备操作员",
                "role": UserRole.OPERATOR,
                "workshop": "第一车间"
            }
        ]
        
        for user_data in sample_users:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if existing_user:
                continue
            
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                phone=user_data["phone"],
                full_name=user_data["full_name"],
                employee_id=user_data["employee_id"],
                department=user_data["department"],
                position=user_data["position"],
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                is_active=True,
                workshop=user_data["workshop"],
                timezone="Asia/Shanghai",
                language="zh-CN",
                theme="light",
                created_by="admin",
                updated_by="admin"
            )
            
            # 设置默认密码
            user.hashed_password = "123456"  # 实际应用中应该使用加密
            user.password_changed_at = datetime.now()
            user.password_expires_at = datetime.now() + timedelta(days=90)
            
            # 设置权限
            if user.role == UserRole.MANAGER:
                permissions = [
                    "order:read", "order:update", "plan:create", "plan:read", "plan:update",
                    "material:read", "progress:read", "progress:update"
                ]
            elif user.role == UserRole.SUPERVISOR:
                permissions = [
                    "order:read", "plan:read", "plan:update", "material:read",
                    "progress:create", "progress:read", "progress:update"
                ]
            else:  # OPERATOR
                permissions = [
                    "order:read", "plan:read", "material:read", "progress:read", "progress:update"
                ]
            
            user.set_permissions(permissions)
            
            db.add(user)
        
        db.commit()
        logger.info("示例用户创建成功")
        
    except Exception as e:
        logger.error(f"创建示例用户失败: {e}")
        db.rollback()
        raise

def init_sample_data(db: Session):
    """初始化示例数据"""
    try:
        # 创建示例订单
        sample_orders = [
            {
                "order_no": "ORD202401001",
                "customer_name": "华为技术有限公司",
                "customer_contact": "张先生",
                "customer_phone": "13800138000",
                "product_name": "5G基站设备",
                "product_model": "AAU5613",
                "product_spec": "64T64R 3.5GHz",
                "quantity": 100,
                "unit": "台",
                "unit_price": 50000.00,
                "total_amount": 5000000.00,
                "order_date": datetime.now() - timedelta(days=10),
                "delivery_date": datetime.now() + timedelta(days=30),
                "status": OrderStatus.IN_PRODUCTION,
                "priority": OrderPriority.HIGH,
                "delivery_address": "深圳市南山区华为总部",
                "technical_requirements": "符合3GPP R15标准，支持SA/NSA双模",
                "quality_standards": "ISO9001质量标准",
                "created_by": "admin"
            },
            {
                "order_no": "ORD202401002",
                "customer_name": "中兴通讯股份有限公司",
                "customer_contact": "李女士",
                "customer_phone": "13800138001",
                "product_name": "光传输设备",
                "product_model": "ZXONE9700",
                "product_spec": "400G OTN",
                "quantity": 50,
                "unit": "套",
                "unit_price": 80000.00,
                "total_amount": 4000000.00,
                "order_date": datetime.now() - timedelta(days=5),
                "delivery_date": datetime.now() + timedelta(days=45),
                "status": OrderStatus.CONFIRMED,
                "priority": OrderPriority.MEDIUM,
                "delivery_address": "深圳市南山区中兴通讯大厦",
                "technical_requirements": "支持400G传输，低时延",
                "quality_standards": "电信级可靠性标准",
                "created_by": "admin"
            }
        ]
        
        for order_data in sample_orders:
            existing_order = db.query(Order).filter(Order.order_no == order_data["order_no"]).first()
            if existing_order:
                continue
            
            order = Order(**order_data)
            db.add(order)
        
        db.commit()
        logger.info("示例订单创建成功")
        
        # 创建示例物料
        sample_materials = [
            {
                "material_code": "MAT001",
                "material_name": "射频芯片",
                "specification": "3.5GHz 64通道",
                "unit": "片",
                "category": MaterialCategory.ELECTRONIC,
                "current_stock": 500,
                "min_stock": 100,
                "max_stock": 1000,
                "unit_price": 1200.00,
                "supplier_name": "海思半导体",
                "supplier_contact": "王经理",
                "supplier_phone": "13800138010",
                "status": MaterialStatus.NORMAL,
                "created_by": "admin"
            },
            {
                "material_code": "MAT002",
                "material_name": "PCB电路板",
                "specification": "8层板 FR4材质",
                "unit": "片",
                "category": MaterialCategory.ELECTRONIC,
                "current_stock": 200,
                "min_stock": 50,
                "max_stock": 500,
                "unit_price": 800.00,
                "supplier_name": "深南电路",
                "supplier_contact": "刘经理",
                "supplier_phone": "13800138011",
                "status": MaterialStatus.NORMAL,
                "created_by": "admin"
            }
        ]
        
        for material_data in sample_materials:
            existing_material = db.query(Material).filter(Material.material_code == material_data["material_code"]).first()
            if existing_material:
                continue
            
            material = Material(**material_data)
            db.add(material)
        
        db.commit()
        logger.info("示例物料创建成功")
        
    except Exception as e:
        logger.error(f"创建示例数据失败: {e}")
        db.rollback()
        raise

def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    try:
        # 创建表
        create_tables()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 初始化管理员用户
            init_admin_user(db)
            
            # 初始化示例用户
            init_sample_users(db)
            
            # 初始化示例数据
            init_sample_data(db)
            
            logger.info("数据库初始化完成")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

if __name__ == "__main__":
    init_database()