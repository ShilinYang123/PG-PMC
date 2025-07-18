#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Creo COM连接
"""

import win32com.client
import pythoncom

def test_creo_com():
    """测试各种可能的Creo COM接口"""
    
    # 初始化COM
    pythoncom.CoInitialize()
    
    # 可能的COM类名
    com_names = [
        "pfcSession.Application",
        "CreoParametric.Application", 
        "ProE.Application",
        "Creo.Application",
        "ProEngineer.Application",
        "pfcSession",
        "CreoParametric",
        "ProE",
        "Creo"
    ]
    
    print("测试Creo COM接口...")
    
    for com_name in com_names:
        try:
            print(f"尝试连接: {com_name}")
            app = win32com.client.GetActiveObject(com_name)
            print(f"✅ 成功连接到: {com_name}")
            print(f"应用程序对象: {app}")
            
            # 尝试获取一些基本信息
            try:
                print(f"应用程序类型: {type(app)}")
                if hasattr(app, 'Version'):
                    print(f"版本: {app.Version}")
                if hasattr(app, 'Name'):
                    print(f"名称: {app.Name}")
            except Exception as e:
                print(f"获取应用程序信息失败: {e}")
            
            return app, com_name
            
        except Exception as e:
            print(f"❌ 连接失败: {com_name} - {e}")
    
    print("\n所有COM接口连接尝试都失败了")
    return None, None

if __name__ == "__main__":
    app, com_name = test_creo_com()
    
    if app:
        print(f"\n成功连接到Creo COM接口: {com_name}")
    else:
        print("\n无法连接到任何Creo COM接口")
        print("可能的原因:")
        print("1. Creo未启动")
        print("2. Creo COM接口未注册")
        print("3. 需要不同的连接方法")
        print("4. 需要VB API或J-Link")