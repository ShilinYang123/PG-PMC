#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的FastAPI应用，用于测试导入导出功能
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import pandas as pd
import io
import os
from datetime import datetime
from typing import List, Dict, Any

# 创建FastAPI应用
app = FastAPI(
    title="PMC导入导出测试API",
    description="用于测试导入导出功能的简化API",
    version="1.0.0"
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟订单数据
orders_data = [
    {
        "id": 1,
        "order_number": "ORD-2024-001",
        "customer_name": "客户A",
        "product_name": "产品A",
        "quantity": 100,
        "unit_price": 50.0,
        "total_amount": 5000.0,
        "order_date": "2024-01-15",
        "delivery_date": "2024-02-15",
        "status": "进行中",
        "priority": "高"
    },
    {
        "id": 2,
        "order_number": "ORD-2024-002",
        "customer_name": "客户B",
        "product_name": "产品B",
        "quantity": 200,
        "unit_price": 30.0,
        "total_amount": 6000.0,
        "order_date": "2024-01-20",
        "delivery_date": "2024-02-20",
        "status": "待开始",
        "priority": "中"
    }
]

@app.get("/")
async def root():
    """根路径"""
    return {"message": "PMC导入导出测试API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.get("/api/v1/orders")
async def get_orders():
    """获取订单列表"""
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "records": orders_data,
            "total": len(orders_data),
            "page": 1,
            "size": 20
        }
    }

@app.post("/api/v1/orders/import")
async def import_orders(file: UploadFile = File(...)):
    """导入订单数据"""
    try:
        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 读取文件内容
        contents = await file.read()
        
        # 根据文件类型解析数据
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # 验证必要的列
        required_columns = ['订单编号', '客户名称', '产品名称', '数量', '单价']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必要的列: {', '.join(missing_columns)}"
            )
        
        # 处理数据
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 这里可以添加数据验证和保存逻辑
                imported_count += 1
            except Exception as e:
                errors.append(f"第{index+1}行: {str(e)}")
        
        return {
            "code": 200,
            "message": "导入完成",
            "data": {
                "imported_count": imported_count,
                "total_rows": len(df),
                "errors": errors
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@app.get("/api/v1/orders/export")
async def export_orders():
    """导出订单数据"""
    try:
        # 创建DataFrame
        df = pd.DataFrame(orders_data)
        
        # 重命名列为中文
        column_mapping = {
            'order_number': '订单编号',
            'customer_name': '客户名称',
            'product_name': '产品名称',
            'quantity': '数量',
            'unit_price': '单价',
            'total_amount': '总金额',
            'order_date': '下单日期',
            'delivery_date': '交货日期',
            'status': '状态',
            'priority': '优先级'
        }
        df = df.rename(columns=column_mapping)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='订单数据', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = f"订单数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 保存到临时文件
        temp_file = f"temp_{filename}"
        with open(temp_file, 'wb') as f:
            f.write(output.getvalue())
        
        return FileResponse(
            path=temp_file,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/api/v1/orders/template")
async def download_template():
    """下载导入模板"""
    try:
        # 创建模板数据
        template_data = {
            '订单编号': ['ORD-2024-001'],
            '客户名称': ['示例客户'],
            '产品名称': ['示例产品'],
            '数量': [100],
            '单价': [50.0],
            '总金额': [5000.0],
            '下单日期': ['2024-01-15'],
            '交货日期': ['2024-02-15'],
            '状态': ['待开始'],
            '优先级': ['中']
        }
        
        df = pd.DataFrame(template_data)
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='订单导入模板', index=False)
        
        output.seek(0)
        
        # 生成文件名
        filename = "订单导入模板.xlsx"
        
        # 保存到临时文件
        temp_file = f"temp_{filename}"
        with open(temp_file, 'wb') as f:
            f.write(output.getvalue())
        
        return FileResponse(
            path=temp_file,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板下载失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )