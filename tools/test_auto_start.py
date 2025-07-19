#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试start.py自动启动监控系统功能
"""

import subprocess
import time
import psutil
import sys
from pathlib import Path

def kill_compliance_monitors():
    """停止所有合规性监控进程"""
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'compliance_monitor.py' in cmdline:
                    print(f"正在停止监控进程 PID: {proc.info['pid']}")
                    proc.terminate()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if killed_count > 0:
        print(f"已停止 {killed_count} 个监控进程")
        time.sleep(2)  # 等待进程完全停止
    else:
        print("没有发现运行中的监控进程")
    
    return killed_count

def check_monitoring_system():
    """检查监控系统是否运行"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'compliance_monitor.py' in cmdline and '--start' in cmdline:
                    return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None

def main():
    """主测试函数"""
    print("=" * 60)
    print("测试 start.py 自动启动监控系统功能")
    print("=" * 60)
    
    # 1. 停止所有监控进程
    print("\n步骤1: 停止现有监控进程")
    kill_compliance_monitors()
    
    # 2. 确认监控系统已停止
    print("\n步骤2: 确认监控系统状态")
    is_running, pid = check_monitoring_system()
    if is_running:
        print(f"⚠️ 监控系统仍在运行 (PID: {pid})")
        return False
    else:
        print("✅ 监控系统已停止")
    
    # 3. 运行start.py
    print("\n步骤3: 运行 start.py")
    try:
        result = subprocess.run(
            [sys.executable, "s:\\PG-PMC\\tools\\start.py"],
            cwd="s:\\PG-PMC",
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ start.py 执行成功")
            print("输出片段:", result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)
        else:
            print(f"❌ start.py 执行失败，退出码: {result.returncode}")
            print("错误信息:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ start.py 执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行start.py时出错: {e}")
        return False
    
    # 4. 检查监控系统是否已启动
    print("\n步骤4: 检查监控系统是否已自动启动")
    time.sleep(3)  # 等待监控系统启动
    
    is_running, pid = check_monitoring_system()
    if is_running:
        print(f"✅ 监控系统已自动启动 (PID: {pid})")
        return True
    else:
        print("❌ 监控系统未能自动启动")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试通过：start.py 自动启动监控系统功能正常")
    else:
        print("❌ 测试失败：start.py 自动启动监控系统功能异常")
    print("=" * 60)
    sys.exit(0 if success else 1)