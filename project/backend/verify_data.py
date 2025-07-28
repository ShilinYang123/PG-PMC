import sqlite3

def verify_data():
    conn = sqlite3.connect('pmc.db')
    cursor = conn.cursor()
    
    tables = [
        'users', 'orders', 'materials', 'equipment', 
        'maintenance_records', 'equipment_operation_logs', 
        'production_plans', 'quality_records'
    ]
    
    print("数据库表记录统计：")
    print("=" * 40)
    
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"{table:25}: {count:>6} 条记录")
        except Exception as e:
            print(f"{table:25}: 错误 - {e}")
    
    conn.close()
    print("=" * 40)
    print("数据验证完成！")

if __name__ == "__main__":
    verify_data()