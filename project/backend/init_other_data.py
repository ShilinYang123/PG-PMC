#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化其他测试数据（生产计划、质量记录等）
"""

import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('zh_CN')

def insert_other_data():
    """插入其他测试数据"""
    conn = sqlite3.connect('pmc.db')
    cursor = conn.cursor()
    
    try:
        # 获取用户ID列表
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # 获取设备ID列表
        cursor.execute("SELECT id FROM equipment")
        equipment_ids = [row[0] for row in cursor.fetchall()]
        
        # 获取订单ID列表
        cursor.execute("SELECT id FROM orders")
        order_ids = [row[0] for row in cursor.fetchall()]
        
        print("开始插入生产计划数据...")
        
        # 插入生产计划数据
        plan_statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
        
        for i in range(20):
            plan_number = f"PLAN{datetime.now().strftime('%Y%m%d')}{i+1:03d}"
            start_date = fake.date_between(start_date='-30d', end_date='+30d')
            end_date = start_date + timedelta(days=random.randint(1, 15))
            
            cursor.execute("""
                INSERT INTO production_plans (
                    plan_no, plan_name, order_id, product_name, product_model,
                    quantity, unit, plan_start_date, plan_end_date, actual_start_date, 
                    actual_end_date, status, priority, workshop, production_line,
                    responsible_person, created_by, created_at, updated_at, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan_number,
                f"生产计划{i+1:03d}",
                random.choice(order_ids) if order_ids else None,
                f"产品{i+1:03d}",
                f"型号{random.choice(['A', 'B', 'C'])}{i+1:02d}",
                random.randint(100, 1000),
                random.choice(['个', '件', '套', 'kg', 'm']),
                start_date.isoformat(),
                end_date.isoformat(),
                start_date.isoformat() if random.choice([True, False]) else None,
                end_date.isoformat() if random.choice([True, False]) else None,
                random.choice(plan_statuses),
                random.choice(priorities),
                f"车间{random.randint(1, 3)}",
                f"生产线{random.randint(1, 5)}",
                f"负责人{random.randint(1, 10)}",
                f"创建者{random.randint(1, 10)}",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                f"备注信息{i+1}"
            ))
            
            plan_id = cursor.lastrowid
            print(f"创建生产计划: {plan_number} (ID: {plan_id})")
        
        print("\n开始插入质量记录数据...")
        
        # 插入质量记录数据
        quality_statuses = ['PASS', 'FAIL', 'REWORK']
        test_types = ['INCOMING', 'IN_PROCESS', 'FINAL', 'OUTGOING']
        
        for i in range(30):
            record_number = f"QC{datetime.now().strftime('%Y%m%d')}{i+1:03d}"
            test_date = fake.date_time_between(start_date='-30d', end_date='now')
            
            cursor.execute("""
                INSERT INTO quality_records (
                    check_no, order_id, order_no, stage_name, check_date, check_type,
                    check_items, check_standards, check_result, quality_score,
                    pass_rate, defect_count, defect_types, defect_description,
                    corrective_actions, inspector, reviewer, created_by,
                    created_at, updated_at, remark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_number,
                random.choice(order_ids) if order_ids else None,
                f"ORDER{datetime.now().strftime('%Y%m%d')}{i+1:03d}",
                f"检验阶段{i+1:02d}",
                test_date.isoformat(),
                random.choice(test_types),
                f"检验项目{i+1}",
                f"检验标准{i+1}",
                random.choice(quality_statuses),
                random.uniform(80.0, 100.0),
                random.uniform(85.0, 100.0),
                random.randint(0, 10),
                f"缺陷类型{i+1}" if random.choice([True, False]) else None,
                f"缺陷描述{i+1}" if random.choice([True, False]) else None,
                f"纠正措施{i+1}" if random.choice([True, False]) else None,
                f"检验员{random.randint(1, 10)}",
                f"审核员{random.randint(1, 10)}",
                f"创建者{random.randint(1, 10)}",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                f"质量记录{i+1}的备注"
            ))
            
            record_id = cursor.lastrowid
            print(f"创建质量记录: {record_number} (ID: {record_id})")
        
        conn.commit()
        print("\n其他数据插入完成！")
        
        # 统计数据
        cursor.execute("SELECT COUNT(*) FROM production_plans")
        plan_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quality_records")
        quality_count = cursor.fetchone()[0]
        
        print(f"\n创建的数据统计：")
        print(f"- 生产计划: {plan_count}")
        print(f"- 质量记录: {quality_count}")
        
    except Exception as e:
        print(f"插入数据时发生错误: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    insert_other_data()
    print("其他测试数据初始化完成！")