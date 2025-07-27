from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from pathlib import Path

# 获取数据库文件路径
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "pmc.db"

# 数据库URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    poolclass=StaticPool,
    echo=False  # 设置为True可以看到SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_database_url() -> str:
    """
    获取数据库URL
    """
    return SQLALCHEMY_DATABASE_URL


def create_database():
    """
    创建数据库表
    """
    from .models import user, order, production_plan, material, progress, equipment, quality
    Base.metadata.create_all(bind=engine)


def drop_database():
    """
    删除数据库表
    """
    Base.metadata.drop_all(bind=engine)


def reset_database():
    """
    重置数据库
    """
    drop_database()
    create_database()


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    """
    # 创建表
    create_database()
    
    # 创建默认用户
    from .models.user import User
    from .core.deps import get_password_hash
    
    db = SessionLocal()
    try:
        # 检查是否已有管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 创建默认管理员用户
            admin_user = User(
                username="admin",
                email="admin@pmc.com",
                full_name="系统管理员",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                role="ADMIN"
            )
            db.add(admin_user)
            db.commit()
            print("默认管理员用户已创建: admin/admin123")
        
    except Exception as e:
        print(f"初始化数据库失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 如果直接运行此文件，则初始化数据库
    init_db()
    print(f"数据库已初始化: {DATABASE_PATH}")