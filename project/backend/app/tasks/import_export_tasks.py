"""导入导出任务

实现文件导入导出的后台任务处理：
- 数据导入任务
- 数据导出任务
- 进度跟踪和状态更新
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from loguru import logger

from ..database import SessionLocal
from ..services.file_service import FileService
from ..models.user import User
from ..models.order import Order
from ..models.production_plan import ProductionPlan
from ..models.material import Material
from ..models.equipment import Equipment
from ..models.progress import ProgressRecord
from ..models.quality import QualityRecord
from ..core.celery_app import celery_app
from ..core.exceptions import ValidationException, BusinessException


@celery_app.task(bind=True, name="process_import_data")
def process_import_data_task(self, data_type: str, data: List[Dict[str, Any]], user_id: int):
    """
    处理导入数据的后台任务
    
    Args:
        self: Celery任务实例
        data_type: 数据类型
        data: 导入数据
        user_id: 用户ID
    """
    db = SessionLocal()
    try:
        logger.info(f"开始处理导入任务: {self.request.id}, 数据类型: {data_type}")
        
        total_count = len(data)
        success_count = 0
        error_count = 0
        errors = []
        
        # 更新任务状态为处理中
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 0,
                'message': f'开始处理{total_count}条{data_type}数据',
                'result': {
                    'total_count': total_count,
                    'success_count': 0,
                    'error_count': 0
                }
            }
        )
        
        for i, item in enumerate(data):
            try:
                # 根据数据类型处理数据
                if data_type == "progress":
                    _process_progress_data(item, db)
                elif data_type == "equipment":
                    _process_equipment_data(item, db)
                elif data_type == "material":
                    _process_material_data(item, db)
                elif data_type == "production_plan":
                    _process_production_plan_data(item, db)
                elif data_type == "order":
                    _process_order_data(item, db)
                elif data_type == "user":
                    _process_user_data(item, db)
                elif data_type == "quality":
                    _process_quality_data(item, db)
                elif data_type == "notification":
                    _process_notification_data(item, db)
                else:
                    raise ValidationException(f"不支持的数据类型: {data_type}")
                
                success_count += 1
                
                # 更新进度
                progress = int((i + 1) / total_count * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': progress,
                        'message': f'已处理 {i + 1}/{total_count} 条数据',
                        'result': {
                            'total_count': total_count,
                            'success_count': success_count,
                            'error_count': error_count
                        }
                    }
                )
                
            except Exception as e:
                error_count += 1
                error_msg = f"第{i+1}行数据处理失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # 提交数据库事务
        db.commit()
        
        result = {
            'total_count': total_count,
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # 只返回前10个错误
        }
        
        logger.info(
            f"导入任务完成: {self.request.id}, "
            f"成功: {success_count}, 失败: {error_count}"
        )
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"处理导入任务失败: {self.request.id}, {e}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="process_export_data")
def process_export_data_task(self, data_type: str, request: Dict[str, Any], user_id: int):
    """
    处理导出数据的后台任务
    
    Args:
        self: Celery任务实例
        data_type: 数据类型
        request: 导出请求参数
        user_id: 用户ID
    """
    db = SessionLocal()
    file_service = FileService()
    
    try:
        logger.info(f"开始处理导出任务: {self.request.id}, 数据类型: {data_type}")
        
        # 更新任务状态为处理中
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 10,
                'message': f'开始查询{data_type}数据',
                'result': None
            }
        )
        
        # 查询数据
        data = []
        if data_type == "progress":
            data = _query_progress_data(request, db)
        elif data_type == "equipment":
            data = _query_equipment_data(request, db)
        elif data_type == "material":
            data = _query_material_data(request, db)
        elif data_type == "production_plan":
            data = _query_production_plan_data(request, db)
        elif data_type == "order":
            data = _query_order_data(request, db)
        elif data_type == "user":
            data = _query_user_data(request, db)
        elif data_type == "quality":
            data = _query_quality_data(request, db)
        elif data_type == "notification":
            data = _query_notification_data(request, db)
        else:
            raise ValidationException(f"不支持的数据类型: {data_type}")
        
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': 50,
                'message': f'查询到{len(data)}条数据，开始生成文件',
                'result': None
            }
        )
        
        # 生成导出文件
        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_format = request.get('format', 'xlsx')
        
        file_info = file_service.generate_export_file(
            data=data,
            filename=filename,
            file_format=file_format,
            style_config={
                'header_style': {
                    'font': {'bold': True, 'color': 'FFFFFF'},
                    'fill': {'start_color': '4472C4', 'end_color': '4472C4', 'fill_type': 'solid'},
                    'alignment': {'horizontal': 'center', 'vertical': 'center'}
                }
            }
        )
        
        result = {
            'file_id': file_info['file_id'],
            'filename': file_info['filename'],
            'file_path': file_info['file_path'],
            'file_size': file_info['file_size'],
            'record_count': len(data)
        }
        
        logger.info(
            f"导出任务完成: {self.request.id}, "
            f"文件: {file_info['filename']}, 记录数: {len(data)}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"处理导出任务失败: {self.request.id}, {e}")
        raise
    finally:
        db.close()


# 数据处理函数
def _process_progress_data(item: Dict[str, Any], db: Session):
    """处理进度数据"""
    progress = ProgressRecord(
        project_name=item.get('项目名称'),
        task_name=item.get('任务名称'),
        progress=float(item.get('进度(%)', 0)),
        start_date=datetime.strptime(item.get('开始时间'), '%Y-%m-%d') if item.get('开始时间') else None,
        end_date=datetime.strptime(item.get('结束时间'), '%Y-%m-%d') if item.get('结束时间') else None,
        responsible_person=item.get('负责人'),
        status=item.get('状态', '进行中'),
        remarks=item.get('备注')
    )
    db.add(progress)


def _process_equipment_data(item: Dict[str, Any], db: Session):
    """处理设备数据"""
    equipment = Equipment(
        name=item.get('设备名称'),
        equipment_code=item.get('设备编号'),
        equipment_type=item.get('设备类型'),
        status=item.get('状态', '正常'),
        capacity=float(item.get('产能', 0)),
        location=item.get('位置'),
        responsible_person=item.get('负责人'),
        remarks=item.get('备注')
    )
    db.add(equipment)


def _process_material_data(item: Dict[str, Any], db: Session):
    """处理物料数据"""
    material = Material(
        material_name=item.get('物料名称'),
        material_code=item.get('物料编号'),
        material_type=item.get('物料类型'),
        unit=item.get('单位'),
        current_stock=float(item.get('库存数量', 0)),
        min_stock_level=float(item.get('安全库存', 0)),
        max_stock_level=float(item.get('最大库存', 0)),
        unit_price=float(item.get('单价', 0)),
        supplier=item.get('供应商'),
        remarks=item.get('备注')
    )
    db.add(material)


def _process_production_plan_data(item: Dict[str, Any], db: Session):
    """处理生产计划数据"""
    plan = ProductionPlan(
        plan_name=item.get('计划名称'),
        product_name=item.get('产品名称'),
        planned_quantity=int(item.get('计划数量', 0)),
        start_date=datetime.strptime(item.get('开始时间'), '%Y-%m-%d') if item.get('开始时间') else None,
        end_date=datetime.strptime(item.get('结束时间'), '%Y-%m-%d') if item.get('结束时间') else None,
        priority=item.get('优先级', '中'),
        status=item.get('状态', '计划中'),
        remarks=item.get('备注')
    )
    db.add(plan)


def _process_order_data(item: Dict[str, Any], db: Session):
    """处理订单数据"""
    order = Order(
        order_number=item.get('订单编号'),
        customer_name=item.get('客户名称'),
        product_name=item.get('产品名称'),
        quantity=int(item.get('订单数量', 0)),
        delivery_date=datetime.strptime(item.get('交期'), '%Y-%m-%d') if item.get('交期') else None,
        status=item.get('状态', '待生产'),
        remarks=item.get('备注')
    )
    db.add(order)


def _process_user_data(item: Dict[str, Any], db: Session):
    """处理用户数据"""
    user = User(
        username=item.get('用户名'),
        full_name=item.get('姓名'),
        email=item.get('邮箱'),
        phone=item.get('电话'),
        department=item.get('部门'),
        role=item.get('角色', 'user'),
        is_active=item.get('状态') == '激活'
    )
    db.add(user)


def _process_quality_data(item: Dict[str, Any], db: Session):
    """处理质量数据"""
    quality = QualityRecord(
        product_name=item.get('产品名称'),
        batch_number=item.get('批次号'),
        inspection_date=datetime.strptime(item.get('检验日期'), '%Y-%m-%d') if item.get('检验日期') else None,
        inspector=item.get('检验员'),
        result=item.get('检验结果', '合格'),
        remarks=item.get('备注')
    )
    db.add(quality)


def _process_notification_data(item: Dict[str, Any], db: Session):
    """处理通知数据"""
    # 这里可以根据实际需求实现通知数据处理
    pass


# 数据查询函数
def _query_progress_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询进度数据"""
    query = db.query(ProgressRecord)
    
    # 应用过滤条件
    if request.get('start_date'):
        start_date = datetime.strptime(request['start_date'], '%Y-%m-%d')
        query = query.filter(ProgressRecord.start_date >= start_date)
    
    if request.get('end_date'):
        end_date = datetime.strptime(request['end_date'], '%Y-%m-%d')
        query = query.filter(ProgressRecord.end_date <= end_date)
    
    records = query.all()
    return [
        {
            '项目名称': record.project_name,
            '任务名称': record.task_name,
            '进度(%)': record.progress,
            '开始时间': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
            '结束时间': record.end_date.strftime('%Y-%m-%d') if record.end_date else '',
            '负责人': record.responsible_person,
            '状态': record.status,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_equipment_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询设备数据"""
    query = db.query(Equipment)
    
    if request.get('equipment_type'):
        query = query.filter(Equipment.equipment_type == request['equipment_type'])
    
    if request.get('status'):
        query = query.filter(Equipment.status == request['status'])
    
    records = query.all()
    return [
        {
            '设备名称': record.name,
            '设备编号': record.equipment_code,
            '设备类型': record.equipment_type,
            '状态': record.status,
            '产能': record.capacity,
            '位置': record.location,
            '负责人': record.responsible_person,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_material_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询物料数据"""
    query = db.query(Material)
    
    if request.get('material_type'):
        query = query.filter(Material.material_type == request['material_type'])
    
    records = query.all()
    return [
        {
            '物料名称': record.material_name,
            '物料编号': record.material_code,
            '物料类型': record.material_type,
            '单位': record.unit,
            '库存数量': record.current_stock,
            '安全库存': record.min_stock_level,
            '最大库存': record.max_stock_level,
            '单价': record.unit_price,
            '供应商': record.supplier,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_production_plan_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询生产计划数据"""
    query = db.query(ProductionPlan)
    
    if request.get('status'):
        query = query.filter(ProductionPlan.status == request['status'])
    
    records = query.all()
    return [
        {
            '计划名称': record.plan_name,
            '产品名称': record.product_name,
            '计划数量': record.planned_quantity,
            '开始时间': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
            '结束时间': record.end_date.strftime('%Y-%m-%d') if record.end_date else '',
            '优先级': record.priority,
            '状态': record.status,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_order_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询订单数据"""
    query = db.query(Order)
    
    if request.get('status'):
        query = query.filter(Order.status == request['status'])
    
    records = query.all()
    return [
        {
            '订单编号': record.order_number,
            '客户名称': record.customer_name,
            '产品名称': record.product_name,
            '订单数量': record.quantity,
            '交期': record.delivery_date.strftime('%Y-%m-%d') if record.delivery_date else '',
            '状态': record.status,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_user_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询用户数据"""
    query = db.query(User)
    
    if request.get('department'):
        query = query.filter(User.department == request['department'])
    
    if request.get('role'):
        query = query.filter(User.role == request['role'])
    
    records = query.all()
    return [
        {
            '用户名': record.username,
            '姓名': record.full_name,
            '邮箱': record.email,
            '电话': record.phone,
            '部门': record.department,
            '角色': record.role,
            '状态': '激活' if record.is_active else '禁用'
        }
        for record in records
    ]


def _query_quality_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询质量数据"""
    query = db.query(QualityRecord)
    
    if request.get('result'):
        query = query.filter(QualityRecord.result == request['result'])
    
    records = query.all()
    return [
        {
            '产品名称': record.product_name,
            '批次号': record.batch_number,
            '检验日期': record.inspection_date.strftime('%Y-%m-%d') if record.inspection_date else '',
            '检验员': record.inspector,
            '检验结果': record.result,
            '备注': record.remarks or ''
        }
        for record in records
    ]


def _query_notification_data(request: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """查询通知数据"""
    # 这里可以根据实际需求实现通知数据查询
    return []