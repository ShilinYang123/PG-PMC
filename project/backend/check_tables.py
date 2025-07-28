#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sqlite3

def check_tables():
    """检查数据库中的表结构"""
    conn = sqlite3.connect('pmc.db')
    cursor = conn.cursor()
    
    try:
        # 检查production_plans表结构
        print("production_plans表结构:")
        cursor.execute("PRAGMA table_info(production_plans)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} {col[2]}")
        
        # 检查quality_records表结构
        print("\nquality_records表结构:")
        cursor.execute("PRAGMA table_info(quality_records)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} {col[2]}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()