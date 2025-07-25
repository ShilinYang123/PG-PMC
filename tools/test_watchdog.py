#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控功能测试脚本
专门测试watchdog库的基本功能
"""

import sys
import time
import threading
from pathlib import Path

def test_watchdog_import():
    """测试watchdog导入"""
    print("🔍 测试watchdog库导入...")
    try:
        import watchdog
        print(f"✅ watchdog版本: {watchdog.__version__}")
        
        from watchdog.observers import Observer
        print("✅ Observer导入成功")
        
        from watchdog.events import FileSystemEventHandler
        print("✅ FileSystemEventHandler导入成功")
        
        return True
    except Exception as e:
        print(f"❌ watchdog导入失败: {e}")
        return False

def test_basic_monitoring():
    """测试基本监控功能"""
    print("\n🔍 测试基本监控功能...")
    
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class TestHandler(FileSystemEventHandler):
            def __init__(self):
                self.events = []
                
            def on_any_event(self, event):
                self.events.append(event)
                print(f"📁 检测到事件: {event.event_type} - {event.src_path}")
        
        # 创建监控器
        observer = Observer()
        handler = TestHandler()
        
        # 监控当前目录
        watch_path = Path.cwd()
        print(f"📂 开始监控目录: {watch_path}")
        
        observer.schedule(handler, str(watch_path), recursive=False)
        observer.start()
        
        print("⏰ 监控运行5秒...")
        time.sleep(5)
        
        observer.stop()
        observer.join()
        
        print(f"✅ 监控测试完成，检测到 {len(handler.events)} 个事件")
        return True
        
    except Exception as e:
        print(f"❌ 监控测试失败: {e}")
        return False

def test_compliance_monitor():
    """测试合规监控脚本"""
    print("\n🔍 测试合规监控脚本...")
    
    compliance_script = Path("tools/compliance_monitor.py")
    if not compliance_script.exists():
        print(f"❌ 合规监控脚本不存在: {compliance_script}")
        return False
        
    print(f"✅ 合规监控脚本存在: {compliance_script}")
    
    # 尝试导入检查
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.path.append('tools'); import compliance_monitor; print('导入成功')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ 合规监控脚本可以正常导入")
            return True
        else:
            print(f"❌ 合规监控脚本导入失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 合规监控脚本导入超时")
        return False
    except Exception as e:
        print(f"❌ 测试合规监控脚本异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 监控功能测试开始")
    print("=" * 50)
    
    # 测试1: watchdog导入
    test1_success = test_watchdog_import()
    
    # 测试2: 基本监控功能
    test2_success = False
    if test1_success:
        test2_success = test_basic_monitoring()
    else:
        print("⏭️ 跳过基本监控测试（watchdog导入失败）")
    
    # 测试3: 合规监控脚本
    test3_success = test_compliance_monitor()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   watchdog导入: {'✅' if test1_success else '❌'}")
    print(f"   基本监控功能: {'✅' if test2_success else '❌'}")
    print(f"   合规监控脚本: {'✅' if test3_success else '❌'}")
    
    if test1_success and test2_success and test3_success:
        print("\n🎉 所有测试通过！监控功能可以正常使用")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要修复监控功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)