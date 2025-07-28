#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接SQL插入设备数据
避免SQLAlchemy外键检查问题
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def insert_equipment_data():
    """直接使用SQL插入设备数据"""
    conn = sqlite3.connect('pmc.db')
    cursor = conn.cursor()
    
    try:
        # 获取用户ID
        cursor.execute("SELECT id FROM users WHERE role = 'ADMIN' LIMIT 1")
        admin_result = cursor.fetchone()
        if not admin_result:
            print("未找到管理员用户")
            return
        admin_id = admin_result[0]
        
        cursor.execute("SELECT id FROM users WHERE role = 'OPERATOR' LIMIT 5")
        operator_results = cursor.fetchall()
        if not operator_results:
            print("未找到操作员用户")
            return
        operator_ids = [row[0] for row in operator_results]
        
        # 设备数据
        equipment_data = [
            ("EQ001", "注塑机001", "production", "HM-180T", "制造商A", "INJ001", "车间A", "A区01号位"),
            ("EQ002", "注塑机002", "production", "HM-220T", "制造商A", "INJ002", "车间A", "A区02号位"),
            ("EQ003", "冲压机001", "production", "CP-100T", "制造商B", "PRS001", "车间B", "B区01号位"),
            ("EQ004", "冲压机002", "production", "CP-150T", "制造商B", "PRS002", "车间B", "B区02号位"),
            ("EQ005", "装配线001", "production", "ASM-AUTO", "制造商C", "ASM001", "车间C", "C区装配线"),
            ("EQ006", "检测设备001", "testing", "QC-3000", "制造商D", "QC001", "车间D", "D区检测室"),
            ("EQ007", "包装机001", "production", "PKG-AUTO", "制造商E", "PKG001", "车间D", "D区包装线")
        ]
        
        # 插入设备数据
        for eq_code, eq_name, eq_type, model, manufacturer, serial_num, workshop, location in equipment_data:
            # 检查设备是否已存在
            cursor.execute("SELECT id FROM equipment WHERE equipment_code = ?", (eq_code,))
            if cursor.fetchone():
                print(f"设备 {eq_code} 已存在，跳过")
                continue
            
            # 随机选择操作员和维护员
            operator_id = random.choice(operator_ids)
            maintainer_id = random.choice(operator_ids)
            
            # 生成日期
            purchase_date = datetime.now() - timedelta(days=random.randint(30, 365))
            warranty_expiry = datetime.now() + timedelta(days=random.randint(365, 1095))
            
            # 插入设备
            cursor.execute("""
                INSERT INTO equipment (
                    equipment_code, equipment_name, equipment_type, model, manufacturer, 
                    serial_number, workshop, location, status, is_active,
                    operator_id, maintainer_id, manager_id,
                    purchase_date, warranty_expiry, specifications,
                    total_runtime, total_downtime, total_maintenance_time,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eq_code, eq_name, eq_type, model, manufacturer,
                serial_num, workshop, location, 'running', True,
                operator_id, maintainer_id, admin_id,
                purchase_date.isoformat(), warranty_expiry.isoformat(), 
                f"{model}型号设备，适用于{eq_type}作业",
                0.0, 0.0, 0.0,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            equipment_id = cursor.lastrowid
            print(f"创建设备: {eq_name} (ID: {equipment_id})")
            
            # 为每台设备创建维护记录
            for i in range(random.randint(1, 3)):
                maintenance_date = datetime.now() - timedelta(days=random.randint(1, 90))
                maintenance_types = ['preventive', 'corrective', 'emergency']
                
                cursor.execute("""
                    INSERT INTO maintenance_records (
                        maintenance_number, equipment_id, maintenance_type, status,
                        planned_start_time, planned_duration, maintenance_description,
                        total_cost, performed_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"MR{equipment_id:03d}{i+1:02d}", equipment_id, random.choice(maintenance_types), 'completed',
                    maintenance_date.isoformat(), random.randint(1, 8),
                    f"{eq_name}的{random.choice(['日常保养', '故障维修', '预防性维护', '紧急抢修'])}",
                    random.uniform(100, 2000), maintainer_id,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
            
            # 为每台设备创建操作日志
            for i in range(random.randint(5, 10)):
                operation_time = datetime.now() - timedelta(hours=random.randint(1, 168))
                operation_types = ['START', 'STOP', 'PAUSE', 'RESUME', 'MAINTENANCE']
                
                cursor.execute("""
                    INSERT INTO equipment_operation_logs (
                        equipment_id, operation_type, operation_description,
                        operator_id, operation_time
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    equipment_id, random.choice(operation_types),
                    f"{eq_name}的{random.choice(['启动操作', '停止操作', '暂停操作', '恢复操作', '维护操作'])}",
                    random.choice(operator_ids), operation_time.isoformat()
                ))
        
        conn.commit()
        print("\n设备数据插入完成！")
        
        # 统计数据
        cursor.execute("SELECT COUNT(*) FROM equipment")
        equipment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM maintenance_records")
        maintenance_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM equipment_operation_logs")
        log_count = cursor.fetchone()[0]
        
        print(f"\n创建的数据统计：")
        print(f"- 设备数量: {equipment_count}")
        print(f"- 维护记录: {maintenance_count}")
        print(f"- 操作日志: {log_count}")
        
    except Exception as e:
        print(f"插入数据时发生错误: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始插入设备测试数据...")
    insert_equipment_data()
    print("设备测试数据插入完成！")