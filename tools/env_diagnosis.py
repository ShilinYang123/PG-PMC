#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简Python环境诊断脚本
用于检测导致Python脚本运行缓慢的根本原因
"""

import time
import sys
import os

def test_basic_python():
    """测试基础Python功能"""
    print("=== 基础Python测试 ===")
    start_time = time.time()
    
    # 测试基本运算
    result = sum(range(1000))
    print(f"基本运算测试: {result}")
    
    # 测试字符串操作
    text = "测试" * 100
    print(f"字符串操作测试: {len(text)}")
    
    end_time = time.time()
    print(f"基础测试耗时: {end_time - start_time:.3f}秒")
    return end_time - start_time

def test_import_speed():
    """测试导入速度"""
    print("\n=== 导入速度测试 ===")
    
    imports_to_test = [
        ('json', 'import json'),
        ('os', 'import os'),
        ('sys', 'import sys'),
        ('time', 'import time'),
        ('datetime', 'import datetime'),
        ('logging', 'import logging'),
        ('yaml', 'import yaml'),
        ('watchdog', 'import watchdog'),
    ]
    
    for name, import_stmt in imports_to_test:
        start_time = time.time()
        try:
            exec(import_stmt)
            end_time = time.time()
            print(f"{name:10} 导入耗时: {end_time - start_time:.3f}秒")
        except ImportError as e:
            print(f"{name:10} 导入失败: {e}")
        except Exception as e:
            print(f"{name:10} 导入异常: {e}")

def test_file_operations():
    """测试文件操作速度"""
    print("\n=== 文件操作测试 ===")
    
    # 测试文件写入
    start_time = time.time()
    test_file = "s:\\PG-PMC\\temp\\speed_test.txt"
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容" * 1000)
        end_time = time.time()
        print(f"文件写入耗时: {end_time - start_time:.3f}秒")
        
        # 测试文件读取
        start_time = time.time()
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        end_time = time.time()
        print(f"文件读取耗时: {end_time - start_time:.3f}秒")
        
        # 清理测试文件
        os.remove(test_file)
        
    except Exception as e:
        print(f"文件操作异常: {e}")

def test_virtual_env():
    """测试虚拟环境状态"""
    print("\n=== 虚拟环境状态 ===")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"虚拟环境: {os.environ.get('VIRTUAL_ENV', '未检测到')}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查site-packages大小
    try:
        site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
        if os.path.exists(site_packages):
            package_count = len([d for d in os.listdir(site_packages) if os.path.isdir(os.path.join(site_packages, d))])
            print(f"已安装包数量: {package_count}")
    except Exception as e:
        print(f"包检查异常: {e}")

def main():
    """主函数"""
    print("Python环境诊断开始...")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_start = time.time()
    
    # 运行各项测试
    basic_time = test_basic_python()
    test_import_speed()
    test_file_operations()
    test_virtual_env()
    
    total_end = time.time()
    total_time = total_end - total_start
    
    print(f"\n=== 诊断总结 ===")
    print(f"总耗时: {total_time:.3f}秒")
    
    # 性能评估
    if total_time > 10:
        print("⚠️  严重性能问题：总耗时超过10秒")
    elif total_time > 5:
        print("⚠️  性能问题：总耗时超过5秒")
    elif basic_time > 1:
        print("⚠️  基础功能缓慢：可能是Python解释器问题")
    else:
        print("✅ 性能正常")
    
    print(f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()