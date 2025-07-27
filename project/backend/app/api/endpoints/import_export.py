from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
import pandas as pd
import json
from datetime import datetime

from ...core.deps import get_current_user, get_db
from ...core.permissions import require_permission, Permission
from ...models.user import User
from ...models.order import Order
from ...models.production_plan import ProductionPlan
from ...models.material import Material
from ...schemas.order import OrderCreate, OrderUpdate
from ...schemas.production_plan import ProductionPlanCreate
from ...schemas.material import MaterialCreate
from ...utils.excel_handler import ExcelHandler
from ...utils.data_validator import DataValidator

router = APIRouter()


@router.post("/orders/import")
@require_permission(Permission.ORDER_WRITE)
def import_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入订单数据
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        # 读取Excel文件
        content = file.file.read()
        df = pd.read_excel(BytesIO(content))
        
        # 验证数据格式
        required_columns = ['order_number', 'customer_name', 'product_name', 'quantity', 'delivery_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必要列: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 检查订单是否已存在
                existing_order = db.query(Order).filter(
                    Order.order_number == row['order_number']
                ).first()
                
                if existing_order:
                    errors.append(f"第{index+2}行: 订单号 {row['order_number']} 已存在")
                    continue
                
                # 创建订单
                order_data = {
                    'order_number': row['order_number'],
                    'customer_name': row['customer_name'],
                    'product_name': row['product_name'],
                    'quantity': int(row['quantity']),
                    'delivery_date': pd.to_datetime(row['delivery_date']).date(),
                    'priority': row.get('priority', 'NORMAL'),
                    'status': row.get('status', 'PENDING'),
                    'notes': row.get('notes', '')
                }
                
                order = Order(**order_data)
                db.add(order)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
        
        db.commit()
        
        return {
            "message": f"成功导入 {imported_count} 条订单",
            "imported_count": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/orders/export")
@require_permission(Permission.ORDER_READ)
def export_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出订单数据
    """
    try:
        orders = db.query(Order).all()
        
        # 准备数据
        data = []
        for order in orders:
            data.append({
                '订单号': order.order_number,
                '客户名称': order.customer_name,
                '产品名称': order.product_name,
                '数量': order.quantity,
                '交付日期': order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else '',
                '优先级': order.priority,
                '状态': order.status,
                '备注': order.notes or '',
                '创建时间': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 创建Excel文件
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='订单数据', index=False)
        
        output.seek(0)
        
        # 返回文件
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/production-plans/import")
@require_permission(Permission.PRODUCTION_WRITE)
def import_production_plans(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入生产计划数据
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        content = file.file.read()
        df = pd.read_excel(BytesIO(content))
        
        required_columns = ['plan_number', 'product_name', 'quantity', 'start_date', 'end_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必要列: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                existing_plan = db.query(ProductionPlan).filter(
                    ProductionPlan.plan_number == row['plan_number']
                ).first()
                
                if existing_plan:
                    errors.append(f"第{index+2}行: 计划号 {row['plan_number']} 已存在")
                    continue
                
                plan_data = {
                    'plan_number': row['plan_number'],
                    'product_name': row['product_name'],
                    'quantity': int(row['quantity']),
                    'start_date': pd.to_datetime(row['start_date']).date(),
                    'end_date': pd.to_datetime(row['end_date']).date(),
                    'status': row.get('status', 'PENDING'),
                    'priority': row.get('priority', 'NORMAL'),
                    'notes': row.get('notes', '')
                }
                
                plan = ProductionPlan(**plan_data)
                db.add(plan)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
        
        db.commit()
        
        return {
            "message": f"成功导入 {imported_count} 条生产计划",
            "imported_count": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/production-plans/export")
@require_permission(Permission.PRODUCTION_READ)
def export_production_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出生产计划数据
    """
    try:
        plans = db.query(ProductionPlan).all()
        
        data = []
        for plan in plans:
            data.append({
                '计划号': plan.plan_number,
                '产品名称': plan.product_name,
                '数量': plan.quantity,
                '开始日期': plan.start_date.strftime('%Y-%m-%d') if plan.start_date else '',
                '结束日期': plan.end_date.strftime('%Y-%m-%d') if plan.end_date else '',
                '状态': plan.status,
                '优先级': plan.priority,
                '备注': plan.notes or '',
                '创建时间': plan.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='生产计划', index=False)
        
        output.seek(0)
        
        filename = f"production_plans_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/materials/import")
@require_permission(Permission.MATERIAL_WRITE)
def import_materials(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入物料数据
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        content = file.file.read()
        df = pd.read_excel(BytesIO(content))
        
        required_columns = ['material_code', 'material_name', 'unit', 'stock_quantity']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必要列: {', '.join(missing_columns)}"
            )
        
        imported_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                existing_material = db.query(Material).filter(
                    Material.material_code == row['material_code']
                ).first()
                
                if existing_material:
                    errors.append(f"第{index+2}行: 物料编码 {row['material_code']} 已存在")
                    continue
                
                material_data = {
                    'material_code': row['material_code'],
                    'material_name': row['material_name'],
                    'unit': row['unit'],
                    'stock_quantity': float(row['stock_quantity']),
                    'min_stock': float(row.get('min_stock', 0)),
                    'max_stock': float(row.get('max_stock', 0)),
                    'unit_price': float(row.get('unit_price', 0)),
                    'supplier': row.get('supplier', ''),
                    'category': row.get('category', ''),
                    'description': row.get('description', '')
                }
                
                material = Material(**material_data)
                db.add(material)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
        
        db.commit()
        
        return {
            "message": f"成功导入 {imported_count} 条物料",
            "imported_count": imported_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/materials/export")
@require_permission(Permission.MATERIAL_READ)
def export_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出物料数据
    """
    try:
        materials = db.query(Material).all()
        
        data = []
        for material in materials:
            data.append({
                '物料编码': material.material_code,
                '物料名称': material.material_name,
                '单位': material.unit,
                '库存数量': material.stock_quantity,
                '最小库存': material.min_stock,
                '最大库存': material.max_stock,
                '单价': material.unit_price,
                '供应商': material.supplier or '',
                '分类': material.category or '',
                '描述': material.description or '',
                '创建时间': material.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='物料数据', index=False)
        
        output.seek(0)
        
        filename = f"materials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/template/download")
@require_permission(Permission.SYSTEM_CONFIG)
def download_template(
    template_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    下载导入模板
    """
    templates = {
        'orders': {
            'filename': 'orders_template.xlsx',
            'columns': ['order_number', 'customer_name', 'product_name', 'quantity', 'delivery_date', 'priority', 'status', 'notes'],
            'sheet_name': '订单模板'
        },
        'production_plans': {
            'filename': 'production_plans_template.xlsx',
            'columns': ['plan_number', 'product_name', 'quantity', 'start_date', 'end_date', 'status', 'priority', 'notes'],
            'sheet_name': '生产计划模板'
        },
        'materials': {
            'filename': 'materials_template.xlsx',
            'columns': ['material_code', 'material_name', 'unit', 'stock_quantity', 'min_stock', 'max_stock', 'unit_price', 'supplier', 'category', 'description'],
            'sheet_name': '物料模板'
        }
    }
    
    if template_type not in templates:
        raise HTTPException(status_code=400, detail="不支持的模板类型")
    
    try:
        template = templates[template_type]
        
        # 创建空的DataFrame
        df = pd.DataFrame(columns=template['columns'])
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=template['sheet_name'], index=False)
        
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={template['filename']}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模板生成失败: {str(e)}")