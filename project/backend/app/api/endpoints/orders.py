from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.order import Order, OrderStatus, OrderPriority
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.order import OrderCreate, OrderUpdate, OrderQuery, OrderDetail, OrderSummary, OrderStats
from datetime import datetime, timedelta
import logging
from fastapi import UploadFile, File
from io import BytesIO
from app.utils.bd400_importer import BD400OrderImporter

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=PagedResponseModel[OrderDetail])
async def get_orders(
    query: OrderQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取订单列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    Order.order_number.contains(query.keyword),
                    Order.customer_name.contains(query.keyword),
                    Order.product_name.contains(query.keyword),
                    Order.product_model.contains(query.keyword)
                )
            )
        
        if query.status:
            filters.append(Order.status == query.status)
        
        if query.priority:
            filters.append(Order.priority == query.priority)
        
        if query.customer_name:
            filters.append(Order.customer_name.contains(query.customer_name))
        
        if query.product_name:
            filters.append(Order.product_name.contains(query.product_name))
        
        if query.order_date_start:
            filters.append(Order.order_date >= query.order_date_start)
        
        if query.order_date_end:
            filters.append(Order.order_date <= query.order_date_end)
        
        if query.delivery_date_start:
            filters.append(Order.delivery_date >= query.delivery_date_start)
        
        if query.delivery_date_end:
            filters.append(Order.delivery_date <= query.delivery_date_end)
        
        if query.urgent_only:
            filters.append(Order.priority == OrderPriority.URGENT)
        
        # 构建基础查询
        base_query = db.query(Order)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(Order, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(Order.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        orders = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        order_details = []
        for order in orders:
            order_detail = OrderDetail(
                id=order.id,
                order_number=order.order_number,
                customer_name=order.customer_name,
                customer_code=order.customer_code,
                product_name=order.product_name,
                product_model=order.product_model,
                product_spec=order.product_spec,
                quantity=order.quantity,
                unit=order.unit,
                unit_price=order.unit_price,
                total_amount=order.total_amount,
                currency=order.currency,
                order_date=order.order_date,
                delivery_date=order.delivery_date,
                status=order.status,
                priority=order.priority,
                contact_person=order.contact_person,
                contact_phone=order.contact_phone,
                contact_email=order.contact_email,
                delivery_address=order.delivery_address,
                technical_requirements=order.technical_requirements,
                quality_standards=order.quality_standards,
                remark=order.remark,
                created_at=order.created_at,
                updated_at=order.updated_at,
                created_by=order.created_by,
                updated_by=order.updated_by
            )
            order_details.append(order_detail)
        
        # 分页信息
        total_pages = (total + query.page_size - 1) // query.page_size
        page_info = PageInfo(
            page=query.page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
            has_next=query.page < total_pages,
            has_prev=query.page > 1
        )
        
        return PagedResponseModel(
            code=200,
            message="获取订单列表成功",
            data=order_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取订单列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单列表服务异常"
        )

@router.get("/{order_id}", response_model=ResponseModel[OrderDetail])
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取订单详情"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        order_detail = OrderDetail(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer_name,
            customer_code=order.customer_code,
            product_name=order.product_name,
            product_model=order.product_model,
            product_spec=order.product_spec,
            quantity=order.quantity,
            unit=order.unit,
            unit_price=order.unit_price,
            total_amount=order.total_amount,
            currency=order.currency,
            order_date=order.order_date,
            delivery_date=order.delivery_date,
            status=order.status,
            priority=order.priority,
            contact_person=order.contact_person,
            contact_phone=order.contact_phone,
            contact_email=order.contact_email,
            delivery_address=order.delivery_address,
            technical_requirements=order.technical_requirements,
            quality_standards=order.quality_standards,
            remark=order.remark,
            created_at=order.created_at,
            updated_at=order.updated_at,
            created_by=order.created_by,
            updated_by=order.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取订单详情成功",
            data=order_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单详情服务异常"
        )

@router.post("/", response_model=ResponseModel[OrderDetail])
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建订单"""
    try:
        # 检查订单号是否已存在
        existing_order = db.query(Order).filter(Order.order_number == order_data.order_number).first()
        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订单号已存在"
            )
        
        # 创建订单
        order = Order(
            order_number=order_data.order_number,
            customer_name=order_data.customer_name,
            customer_code=order_data.customer_code,
            product_name=order_data.product_name,
            product_model=order_data.product_model,
            product_spec=order_data.product_spec,
            quantity=order_data.quantity,
            unit=order_data.unit,
            unit_price=order_data.unit_price,
            total_amount=order_data.total_amount,
            currency=order_data.currency or "CNY",
            order_date=order_data.order_date,
            delivery_date=order_data.delivery_date,
            status=order_data.status or OrderStatus.PENDING,
            priority=order_data.priority or OrderPriority.MEDIUM,
            contact_person=order_data.contact_person,
            contact_phone=order_data.contact_phone,
            contact_email=order_data.contact_email,
            delivery_address=order_data.delivery_address,
            technical_requirements=order_data.technical_requirements,
            quality_standards=order_data.quality_standards,
            remark=order_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        order_detail = OrderDetail(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer_name,
            customer_code=order.customer_code,
            product_name=order.product_name,
            product_model=order.product_model,
            product_spec=order.product_spec,
            quantity=order.quantity,
            unit=order.unit,
            unit_price=order.unit_price,
            total_amount=order.total_amount,
            currency=order.currency,
            order_date=order.order_date,
            delivery_date=order.delivery_date,
            status=order.status,
            priority=order.priority,
            created_at=order.created_at,
            created_by=order.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建订单成功",
            data=order_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建订单异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建订单服务异常"
        )

@router.put("/{order_id}", response_model=ResponseModel[OrderDetail])
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新订单"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 更新字段
        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        order.updated_by = current_user.username
        order.updated_at = datetime.now()
        
        db.commit()
        db.refresh(order)
        
        order_detail = OrderDetail(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer_name,
            customer_code=order.customer_code,
            product_name=order.product_name,
            product_model=order.product_model,
            product_spec=order.product_spec,
            quantity=order.quantity,
            unit=order.unit,
            unit_price=order.unit_price,
            total_amount=order.total_amount,
            currency=order.currency,
            order_date=order.order_date,
            delivery_date=order.delivery_date,
            status=order.status,
            priority=order.priority,
            updated_at=order.updated_at,
            updated_by=order.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新订单成功",
            data=order_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新订单异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订单服务异常"
        )

@router.delete("/{order_id}", response_model=ResponseModel[dict])
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除订单"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="订单不存在"
            )
        
        # 检查订单状态，只有待确认状态的订单才能删除
        if order.status not in [OrderStatus.PENDING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有待确认状态的订单才能删除"
            )
        
        db.delete(order)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除订单成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除订单异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除订单服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[OrderStats])
async def get_order_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取订单统计信息"""
    try:
        # 总订单数
        total_orders = db.query(Order).count()
        
        # 各状态订单数
        pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
        confirmed_orders = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED).count()
        in_production_orders = db.query(Order).filter(Order.status == OrderStatus.IN_PRODUCTION).count()
        completed_orders = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).count()
        cancelled_orders = db.query(Order).filter(Order.status == OrderStatus.CANCELLED).count()
        
        # 紧急订单数
        urgent_orders = db.query(Order).filter(Order.priority == OrderPriority.URGENT).count()
        
        # 本月新增订单
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new_orders = db.query(Order).filter(Order.created_at >= current_month_start).count()
        
        # 本月完成订单
        monthly_completed_orders = db.query(Order).filter(
            and_(
                Order.status == OrderStatus.COMPLETED,
                Order.updated_at >= current_month_start
            )
        ).count()
        
        # 逾期订单（交期已过但未完成）
        today = datetime.now().date()
        overdue_orders = db.query(Order).filter(
            and_(
                Order.delivery_date < today,
                Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PRODUCTION])
            )
        ).count()
        
        # 总金额
        total_amount_result = db.query(db.func.sum(Order.total_amount)).scalar()
        total_amount = float(total_amount_result) if total_amount_result else 0.0
        
        # 本月金额
        monthly_amount_result = db.query(db.func.sum(Order.total_amount)).filter(
            Order.created_at >= current_month_start
        ).scalar()
        monthly_amount = float(monthly_amount_result) if monthly_amount_result else 0.0
        
        order_stats = OrderStats(
            total_orders=total_orders,
            pending_orders=pending_orders,
            confirmed_orders=confirmed_orders,
            in_production_orders=in_production_orders,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
            urgent_orders=urgent_orders,
            overdue_orders=overdue_orders,
            monthly_new_orders=monthly_new_orders,
            monthly_completed_orders=monthly_completed_orders,
            total_amount=total_amount,
            monthly_amount=monthly_amount
        )
        
        return ResponseModel(
            code=200,
            message="获取订单统计成功",
            data=order_stats
        )
        
    except Exception as e:
        logger.error(f"获取订单统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订单统计服务异常"
        )

@router.post("/import/bd400", response_model=ResponseModel[dict])
async def import_bd400_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """导入BD400订单表"""
    try:
        # 验证文件格式
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            return ResponseModel(
                success=False,
                message="只支持Excel文件格式(.xlsx, .xls)",
                data=None
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 创建BD400导入器
        importer = BD400OrderImporter(db)
        
        # 执行导入
        result = importer.import_from_excel(file_content)
        
        if result['success']:
            logger.info(f"用户 {current_user.username} 成功导入BD400订单: {result['imported_count']}条")
            return ResponseModel(
                success=True,
                message=result['message'],
                data={
                    'imported_count': result['imported_count'],
                    'skipped_count': result.get('skipped_count', 0),
                    'errors': result.get('errors', []),
                    'warnings': result.get('warnings', [])
                }
            )
        else:
            return ResponseModel(
                success=False,
                message=result['message'],
                data={
                    'errors': result.get('errors', []),
                    'imported_count': result.get('imported_count', 0)
                }
            )
             
    except Exception as e:
        logger.error(f"BD400订单导入失败: {str(e)}")
        return ResponseModel(
            success=False,
            message=f"导入失败: {str(e)}",
            data=None
        )

@router.get("/export/template", response_model=ResponseModel[dict])
async def get_order_template(
    current_user: User = Depends(get_current_active_user)
):
    """获取订单导入模板"""
    try:
        template_data = {
            'filename': 'BD400订单导入模板.xlsx',
            'columns': [
                {'field': 'order_number', 'title': '订单号', 'required': True, 'example': 'ORD20240101001'},
                {'field': 'customer_name', 'title': '客户名称', 'required': True, 'example': '某某公司'},
                {'field': 'customer_code', 'title': '客户代码', 'required': False, 'example': 'CUST001'},
                {'field': 'product_name', 'title': '产品名称', 'required': True, 'example': '某某产品'},
                {'field': 'product_model', 'title': '产品型号', 'required': False, 'example': 'MODEL-001'},
                {'field': 'product_spec', 'title': '产品规格', 'required': False, 'example': '100*200*300'},
                {'field': 'quantity', 'title': '数量', 'required': True, 'example': '100'},
                {'field': 'unit', 'title': '单位', 'required': False, 'example': '件'},
                {'field': 'unit_price', 'title': '单价', 'required': False, 'example': '10.50'},
                {'field': 'total_amount', 'title': '总金额', 'required': False, 'example': '1050.00'},
                {'field': 'currency', 'title': '币种', 'required': False, 'example': 'CNY'},
                {'field': 'order_date', 'title': '下单日期', 'required': False, 'example': '2024-01-01'},
                {'field': 'delivery_date', 'title': '交货日期', 'required': True, 'example': '2024-02-01'},
                {'field': 'priority', 'title': '优先级', 'required': False, 'example': '中'},
                {'field': 'contact_person', 'title': '联系人', 'required': False, 'example': '张三'},
                {'field': 'contact_phone', 'title': '联系电话', 'required': False, 'example': '13800138000'},
                {'field': 'contact_email', 'title': '联系邮箱', 'required': False, 'example': 'zhangsan@example.com'},
                {'field': 'delivery_address', 'title': '交货地址', 'required': False, 'example': '某某市某某区某某街道'},
                {'field': 'technical_requirements', 'title': '技术要求', 'required': False, 'example': '按图纸要求'},
                {'field': 'quality_standards', 'title': '质量标准', 'required': False, 'example': 'GB/T标准'},
                {'field': 'remark', 'title': '备注', 'required': False, 'example': '特殊要求'}
            ],
            'notes': [
                '1. 标记为"必填"的字段不能为空',
                '2. 订单号必须唯一，重复的订单号将被跳过',
                '3. 日期格式支持: 2024-01-01, 2024/01/01等',
                '4. 优先级可选值: 低、中、高、紧急',
                '5. 数量必须为正整数',
                '6. 单价和总金额为数值格式'
            ]
        }
        
        return ResponseModel(
             success=True,
             message="获取模板信息成功",
             data=template_data
         )
        
    except Exception as e:
         logger.error(f"获取订单模板失败: {str(e)}")
         return ResponseModel(
             success=False,
             message=f"获取模板失败: {str(e)}",
             data=None
         )