-- PMC全流程管理系统数据库初始化脚本
-- 创建时间: 2025-01-26
-- 版本: 1.0.0

-- 创建数据库（如果不存在）
-- CREATE DATABASE pmc_db;

-- 连接到数据库
\c pmc_db;

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建枚举类型
CREATE TYPE order_status AS ENUM (
    'pending',      -- 待处理
    'confirmed',    -- 已确认
    'in_production', -- 生产中
    'completed',    -- 已完成
    'cancelled',    -- 已取消
    'on_hold'       -- 暂停
);

CREATE TYPE production_status AS ENUM (
    'planned',      -- 已计划
    'in_progress',  -- 进行中
    'completed',    -- 已完成
    'delayed',      -- 延期
    'cancelled'     -- 已取消
);

CREATE TYPE material_status AS ENUM (
    'available',    -- 可用
    'reserved',     -- 已预留
    'out_of_stock', -- 缺货
    'ordered',      -- 已订购
    'discontinued'  -- 停产
);

CREATE TYPE user_role AS ENUM (
    'admin',        -- 管理员
    'manager',      -- 经理
    'operator',     -- 操作员
    'viewer'        -- 查看者
);

CREATE TYPE notification_type AS ENUM (
    'email',        -- 邮件
    'wechat',       -- 微信
    'sms',          -- 短信
    'system'        -- 系统通知
);

-- 创建序列
CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1000;
CREATE SEQUENCE IF NOT EXISTS production_plan_seq START 1;
CREATE SEQUENCE IF NOT EXISTS material_code_seq START 1;

-- 创建函数：生成订单号
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TEXT AS $$
BEGIN
    RETURN 'ORD' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD(nextval('order_number_seq')::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- 创建函数：更新时间戳
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建索引函数
CREATE OR REPLACE FUNCTION create_indexes()
RETURNS VOID AS $$
BEGIN
    -- 订单表索引
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_name);
    CREATE INDEX IF NOT EXISTS idx_orders_delivery_date ON orders(delivery_date);
    CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
    
    -- 生产计划表索引
    CREATE INDEX IF NOT EXISTS idx_production_plans_status ON production_plans(status);
    CREATE INDEX IF NOT EXISTS idx_production_plans_order_id ON production_plans(order_id);
    CREATE INDEX IF NOT EXISTS idx_production_plans_start_date ON production_plans(planned_start_date);
    
    -- 物料表索引
    CREATE INDEX IF NOT EXISTS idx_materials_code ON materials(material_code);
    CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(material_name);
    CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);
    
    -- 用户表索引
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    
    -- 全文搜索索引
    CREATE INDEX IF NOT EXISTS idx_orders_search ON orders USING gin(to_tsvector('chinese', customer_name || ' ' || product_name));
    CREATE INDEX IF NOT EXISTS idx_materials_search ON materials USING gin(to_tsvector('chinese', material_name || ' ' || description));
END;
$$ LANGUAGE plpgsql;

-- 创建视图：订单概览
CREATE OR REPLACE VIEW order_overview AS
SELECT 
    o.id,
    o.order_number,
    o.customer_name,
    o.product_name,
    o.quantity,
    o.status,
    o.delivery_date,
    o.created_at,
    pp.status as production_status,
    pp.planned_start_date,
    pp.planned_end_date,
    pp.actual_start_date,
    pp.actual_end_date,
    CASE 
        WHEN o.delivery_date < CURRENT_DATE AND o.status != 'completed' THEN true
        ELSE false
    END as is_overdue
FROM orders o
LEFT JOIN production_plans pp ON o.id = pp.order_id;

-- 创建视图：物料库存概览
CREATE OR REPLACE VIEW material_inventory AS
SELECT 
    m.id,
    m.material_code,
    m.material_name,
    m.current_stock,
    m.min_stock_level,
    m.max_stock_level,
    m.status,
    CASE 
        WHEN m.current_stock <= m.min_stock_level THEN 'low'
        WHEN m.current_stock >= m.max_stock_level THEN 'high'
        ELSE 'normal'
    END as stock_level,
    m.unit_price,
    m.current_stock * m.unit_price as total_value
FROM materials m;

-- 创建初始数据插入函数
CREATE OR REPLACE FUNCTION insert_initial_data()
RETURNS VOID AS $$
BEGIN
    -- 插入默认管理员用户（如果不存在）
    INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
    VALUES ('admin', 'admin@pmc.local', '$2b$12$LQv3c1yqBwEHxPiLBPPo.eUHoD/KVQOQVsd9iyil.okepmyeWxlIq', '系统管理员', 'admin', true)
    ON CONFLICT (username) DO NOTHING;
    
    -- 插入示例物料数据
    INSERT INTO materials (material_code, material_name, description, unit, current_stock, min_stock_level, max_stock_level, unit_price, status)
    VALUES 
        ('MAT001', '钢板A', '厚度5mm钢板', '张', 100, 20, 500, 150.00, 'available'),
        ('MAT002', '螺栓M8', 'M8*20螺栓', '个', 1000, 100, 5000, 0.50, 'available'),
        ('MAT003', '焊条3.2', '3.2mm焊条', '根', 500, 50, 2000, 2.00, 'available')
    ON CONFLICT (material_code) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- 执行索引创建
SELECT create_indexes();

-- 执行初始数据插入
SELECT insert_initial_data();

-- 创建触发器（在表创建后执行）
-- 这些触发器将在SQLAlchemy模型创建表后自动添加

COMMIT;