#!/usr/bin/env python3
"""
备份API测试脚本

测试备份相关API接口的基本功能
"""

import requests
import json
from datetime import datetime
import time

# API基础URL
BASE_URL = "http://localhost:8000/api/backup"

# 测试用户认证信息（需要根据实际情况调整）
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

def get_auth_token():
    """获取认证令牌"""
    try:
        auth_url = "http://localhost:8000/api/auth/login"
        # 使用form-data格式发送登录请求
        response = requests.post(auth_url, data=TEST_USER)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("access_token")
        else:
            print(f"认证失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"认证请求失败: {e}")
        return None

def test_backup_health():
    """测试备份服务健康检查"""
    print("\n=== 测试备份服务健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_create_backup(token):
    """测试创建备份"""
    print("\n=== 测试创建备份 ===")
    headers = {"Authorization": f"Bearer {token}"}
    backup_data = {
        "backup_type": "database",
        "description": "API测试备份",
        "include_files": False,
        "include_config": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/create", json=backup_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            return response.json().get("backup_id")
        return None
    except Exception as e:
        print(f"创建备份失败: {e}")
        return None

def test_list_backups(token):
    """测试获取备份列表"""
    print("\n=== 测试获取备份列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/list?limit=10", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取备份列表失败: {e}")
        return False

def test_backup_statistics(token):
    """测试获取备份统计"""
    print("\n=== 测试获取备份统计 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/statistics", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取备份统计失败: {e}")
        return False

def test_verify_backup(token, backup_id):
    """测试验证备份"""
    if not backup_id:
        print("\n=== 跳过备份验证测试（无备份ID） ===")
        return False
        
    print("\n=== 测试验证备份 ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/verify/{backup_id}?deep_check=false", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"验证备份失败: {e}")
        return False

def test_search_backups(token):
    """测试搜索备份"""
    print("\n=== 测试搜索备份 ===")
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "backup_type": "database",
        "limit": 5
    }
    
    try:
        response = requests.get(f"{BASE_URL}/search", params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"搜索备份失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始备份API测试...")
    print(f"测试时间: {datetime.now()}")
    
    # 测试健康检查（无需认证）
    health_ok = test_backup_health()
    
    # 获取认证令牌
    print("\n=== 获取认证令牌 ===")
    token = get_auth_token()
    if not token:
        print("无法获取认证令牌，跳过需要认证的测试")
        return
    
    print(f"认证令牌获取成功: {token[:20]}...")
    
    # 执行各项测试
    tests = [
        ("备份统计", lambda: test_backup_statistics(token)),
        ("备份列表", lambda: test_list_backups(token)),
        ("搜索备份", lambda: test_search_backups(token)),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"测试 {test_name} 异常: {e}")
            results[test_name] = False
    
    # 测试创建备份（可能需要更长时间）
    backup_id = test_create_backup(token)
    results["创建备份"] = backup_id is not None
    
    # 如果创建成功，测试验证
    if backup_id:
        time.sleep(2)  # 等待备份完成
        results["验证备份"] = test_verify_backup(token, backup_id)
    
    # 输出测试结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if health_ok:
        print("\n✅ 备份服务基本功能正常")
    else:
        print("\n❌ 备份服务存在问题")

if __name__ == "__main__":
    main()