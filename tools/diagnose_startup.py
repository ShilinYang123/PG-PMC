#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本诊断工具
逐步测试各个组件，找出卡顿原因
作者：雨俊（技术负责人）
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def test_basic_imports():
    """测试基础库导入"""
    print("🔍 测试基础库导入...")
    
    try:
        import json
        print("   ✅ json - OK")
    except Exception as e:
        print(f"   ❌ json - 失败: {e}")
        return False
        
    try:
        import yaml
        print("   ✅ yaml - OK")
    except Exception as e:
        print(f"   ❌ yaml - 失败: {e}")
        return False
        
    try:
        import logging
        print("   ✅ logging - OK")
    except Exception as e:
        print(f"   ❌ logging - 失败: {e}")
        return False
        
    try:
        from datetime import datetime
        print("   ✅ datetime - OK")
    except Exception as e:
        print(f"   ❌ datetime - 失败: {e}")
        return False
        
    return True

def test_watchdog_import():
    """测试watchdog库导入"""
    print("\n🔍 测试watchdog库导入...")
    
    try:
        print("   测试基础watchdog导入...")
        import watchdog
        print(f"   ✅ watchdog版本: {watchdog.__version__}")
        
        print("   测试Observer导入...")
        from watchdog.observers import Observer
        print("   ✅ Observer - OK")
        
        print("   测试事件处理器导入...")
        from watchdog.events import FileSystemEventHandler
        print("   ✅ FileSystemEventHandler - OK")
        
        return True
        
    except Exception as e:
        print(f"   ❌ watchdog导入失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    print("\n🔍 测试文件操作...")
    
    try:
        project_root = Path(os.getcwd())
        print(f"   项目根目录: {project_root}")
        
        docs_dir = project_root / "docs"
        if docs_dir.exists():
            print("   ✅ docs目录存在")
        else:
            print("   ❌ docs目录不存在")
            return False
            
        tools_dir = project_root / "tools"
        if tools_dir.exists():
            print("   ✅ tools目录存在")
        else:
            print("   ❌ tools目录不存在")
            return False
            
        # 测试读取一个小文件
        test_file = docs_dir / "01-设计" / "开发任务书.md"
        if test_file.exists():
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read(100)  # 只读前100个字符
            print("   ✅ 文件读取测试通过")
        else:
            print("   ⚠️ 测试文件不存在，跳过读取测试")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 文件操作失败: {e}")
        return False

def test_subprocess():
    """测试子进程操作"""
    print("\n🔍 测试子进程操作...")
    
    try:
        # 测试简单的subprocess调用
        result = subprocess.run(
            [sys.executable, "-c", "print('subprocess测试成功')"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("   ✅ subprocess基础测试通过")
            print(f"   输出: {result.stdout.strip()}")
        else:
            print(f"   ❌ subprocess测试失败: {result.stderr}")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print("   ❌ subprocess测试超时")
        return False
    except Exception as e:
        print(f"   ❌ subprocess测试异常: {e}")
        return False

def test_logging_setup():
    """测试日志设置"""
    print("\n🔍 测试日志设置...")
    
    try:
        import logging
        from datetime import datetime
        
        # 创建临时日志文件
        logs_dir = Path(os.getcwd()) / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / f"diagnose_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("日志测试消息")
        
        print("   ✅ 日志设置测试通过")
        print(f"   日志文件: {log_file}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 日志设置失败: {e}")
        return False

def test_yaml_loading():
    """测试YAML文件加载"""
    print("\n🔍 测试YAML文件加载...")
    
    try:
        import yaml
        
        project_root = Path(os.getcwd())
        yaml_file = project_root / "docs" / "03-管理" / "project_config.yaml"
        
        if yaml_file.exists():
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            print("   ✅ YAML文件加载测试通过")
            print(f"   加载的键: {list(content.keys()) if isinstance(content, dict) else 'non-dict'}")
        else:
            print("   ⚠️ YAML测试文件不存在，跳过测试")
            
        return True
        
    except Exception as e:
        print(f"   ❌ YAML加载失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("🚀 启动脚本诊断开始")
    print("=" * 50)
    
    tests = [
        ("基础库导入", test_basic_imports),
        ("watchdog库导入", test_watchdog_import),
        ("文件操作", test_file_operations),
        ("子进程操作", test_subprocess),
        ("日志设置", test_logging_setup),
        ("YAML文件加载", test_yaml_loading)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        start_time = time.time()
        
        try:
            result = test_func()
            end_time = time.time()
            duration = end_time - start_time
            
            results[test_name] = {
                'success': result,
                'duration': duration
            }
            
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {status} (耗时: {duration:.2f}秒)")
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            results[test_name] = {
                'success': False,
                'duration': duration,
                'error': str(e)
            }
            
            print(f"   ❌ 异常: {e} (耗时: {duration:.2f}秒)")
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 诊断结果总结:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        duration = result['duration']
        print(f"{status} {test_name}: {duration:.2f}秒")
        
        if not result['success'] and 'error' in result:
            print(f"   错误: {result['error']}")
    
    # 分析可能的问题
    print("\n🔍 问题分析:")
    
    slow_tests = [name for name, result in results.items() if result['duration'] > 5.0]
    if slow_tests:
        print(f"⚠️ 耗时较长的测试: {', '.join(slow_tests)}")
    
    failed_tests = [name for name, result in results.items() if not result['success']]
    if failed_tests:
        print(f"❌ 失败的测试: {', '.join(failed_tests)}")
    
    if not failed_tests and not slow_tests:
        print("✅ 所有测试都正常，问题可能在于脚本逻辑或环境配置")
    
    print("\n🎯 建议:")
    if 'watchdog库导入' in failed_tests:
        print("- 重新安装watchdog库: pip install watchdog")
    if slow_tests:
        print("- 检查系统资源使用情况")
        print("- 考虑添加更多的超时和进度显示")
    
    print("\n诊断完成！")

if __name__ == "__main__":
    main()