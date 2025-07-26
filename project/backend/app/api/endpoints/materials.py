from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.material import Material, MaterialCategory, MaterialStatus
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.material import (
    MaterialCreate, MaterialUpdate, MaterialQuery, MaterialDetail,
    MaterialStats, MaterialSummary, MaterialStockAlert
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=PagedResponseModel[MaterialDetail])
async def get_materials(
    query: MaterialQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取物料列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    Material.material_code.contains(query.keyword),
                    Material.material_name.contains(query.keyword),
                    Material.specification.contains(query.keyword),
                    Material.supplier.contains(query.keyword)
                )
            )
        
        if query.category:
            filters.append(Material.category == query.category)
        
        if query.status:
            filters.append(Material.status == query.status)
        
        if query.supplier:
            filters.append(Material.supplier.contains(query.supplier))
        
        if query.warehouse:
            filters.append(Material.warehouse.contains(query.warehouse))
        
        if query.low_stock_only:
            filters.append(Material.current_stock <= Material.min_stock)
        
        if query.out_of_stock_only:
            filters.append(Material.current_stock <= 0)
        
        if query.price_min is not None:
            filters.append(Material.unit_price >= query.price_min)
        
        if query.price_max is not None:
            filters.append(Material.unit_price <= query.price_max)
        
        # 构建基础查询
        base_query = db.query(Material)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(Material, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(Material.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        materials = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        material_details = []
        for material in materials:
            # 计算库存状态
            stock_status = "正常"
            if material.current_stock <= 0:
                stock_status = "缺货"
            elif material.current_stock <= material.min_stock:
                stock_status = "库存不足"
            elif material.current_stock >= material.max_stock:
                stock_status = "库存过多"
            
            material_detail = MaterialDetail(
                id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                category=material.category,
                specification=material.specification,
                unit=material.unit,
                unit_price=material.unit_price,
                current_stock=material.current_stock,
                min_stock=material.min_stock,
                max_stock=material.max_stock,
                safety_stock=material.safety_stock,
                stock_status=stock_status,
                supplier=material.supplier,
                supplier_contact=material.supplier_contact,
                lead_time=material.lead_time,
                warehouse=material.warehouse,
                location=material.location,
                status=material.status,
                last_purchase_date=material.last_purchase_date,
                last_purchase_price=material.last_purchase_price,
                last_usage_date=material.last_usage_date,
                remark=material.remark,
                created_at=material.created_at,
                updated_at=material.updated_at,
                created_by=material.created_by,
                updated_by=material.updated_by
            )
            material_details.append(material_detail)
        
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
            message="获取物料列表成功",
            data=material_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取物料列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取物料列表服务异常"
        )

@router.get("/{material_id}", response_model=ResponseModel[MaterialDetail])
async def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取物料详情"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物料不存在"
            )
        
        # 计算库存状态
        stock_status = "正常"
        if material.current_stock <= 0:
            stock_status = "缺货"
        elif material.current_stock <= material.min_stock:
            stock_status = "库存不足"
        elif material.current_stock >= material.max_stock:
            stock_status = "库存过多"
        
        material_detail = MaterialDetail(
            id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            category=material.category,
            specification=material.specification,
            unit=material.unit,
            unit_price=material.unit_price,
            current_stock=material.current_stock,
            min_stock=material.min_stock,
            max_stock=material.max_stock,
            safety_stock=material.safety_stock,
            stock_status=stock_status,
            supplier=material.supplier,
            supplier_contact=material.supplier_contact,
            lead_time=material.lead_time,
            warehouse=material.warehouse,
            location=material.location,
            status=material.status,
            last_purchase_date=material.last_purchase_date,
            last_purchase_price=material.last_purchase_price,
            last_usage_date=material.last_usage_date,
            remark=material.remark,
            created_at=material.created_at,
            updated_at=material.updated_at,
            created_by=material.created_by,
            updated_by=material.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取物料详情成功",
            data=material_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取物料详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取物料详情服务异常"
        )

@router.post("/", response_model=ResponseModel[MaterialDetail])
async def create_material(
    material_data: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建物料"""
    try:
        # 检查物料编码是否已存在
        existing_material = db.query(Material).filter(Material.material_code == material_data.material_code).first()
        if existing_material:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="物料编码已存在"
            )
        
        # 创建物料
        material = Material(
            material_code=material_data.material_code,
            material_name=material_data.material_name,
            category=material_data.category,
            specification=material_data.specification,
            unit=material_data.unit,
            unit_price=material_data.unit_price,
            current_stock=material_data.current_stock or 0,
            min_stock=material_data.min_stock or 0,
            max_stock=material_data.max_stock,
            safety_stock=material_data.safety_stock or 0,
            supplier=material_data.supplier,
            supplier_contact=material_data.supplier_contact,
            lead_time=material_data.lead_time,
            warehouse=material_data.warehouse,
            location=material_data.location,
            status=material_data.status or MaterialStatus.ACTIVE,
            remark=material_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(material)
        db.commit()
        db.refresh(material)
        
        # 计算库存状态
        stock_status = "正常"
        if material.current_stock <= 0:
            stock_status = "缺货"
        elif material.current_stock <= material.min_stock:
            stock_status = "库存不足"
        elif material.current_stock >= material.max_stock:
            stock_status = "库存过多"
        
        material_detail = MaterialDetail(
            id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            category=material.category,
            specification=material.specification,
            unit=material.unit,
            unit_price=material.unit_price,
            current_stock=material.current_stock,
            min_stock=material.min_stock,
            max_stock=material.max_stock,
            safety_stock=material.safety_stock,
            stock_status=stock_status,
            supplier=material.supplier,
            supplier_contact=material.supplier_contact,
            lead_time=material.lead_time,
            warehouse=material.warehouse,
            location=material.location,
            status=material.status,
            remark=material.remark,
            created_at=material.created_at,
            created_by=material.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建物料成功",
            data=material_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建物料异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建物料服务异常"
        )

@router.put("/{material_id}", response_model=ResponseModel[MaterialDetail])
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新物料"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物料不存在"
            )
        
        # 更新字段
        update_data = material_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(material, field, value)
        
        material.updated_by = current_user.username
        material.updated_at = datetime.now()
        
        db.commit()
        db.refresh(material)
        
        # 计算库存状态
        stock_status = "正常"
        if material.current_stock <= 0:
            stock_status = "缺货"
        elif material.current_stock <= material.min_stock:
            stock_status = "库存不足"
        elif material.current_stock >= material.max_stock:
            stock_status = "库存过多"
        
        material_detail = MaterialDetail(
            id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            category=material.category,
            specification=material.specification,
            unit=material.unit,
            unit_price=material.unit_price,
            current_stock=material.current_stock,
            min_stock=material.min_stock,
            max_stock=material.max_stock,
            safety_stock=material.safety_stock,
            stock_status=stock_status,
            supplier=material.supplier,
            supplier_contact=material.supplier_contact,
            lead_time=material.lead_time,
            warehouse=material.warehouse,
            location=material.location,
            status=material.status,
            last_purchase_date=material.last_purchase_date,
            last_purchase_price=material.last_purchase_price,
            last_usage_date=material.last_usage_date,
            remark=material.remark,
            updated_at=material.updated_at,
            updated_by=material.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新物料成功",
            data=material_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新物料异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新物料服务异常"
        )

@router.delete("/{material_id}", response_model=ResponseModel[dict])
async def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除物料"""
    try:
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物料不存在"
            )
        
        # 检查物料是否可以删除（例如是否有库存、是否被使用等）
        if material.current_stock > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="有库存的物料不能删除"
            )
        
        db.delete(material)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除物料成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除物料异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除物料服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[MaterialStats])
async def get_material_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取物料统计信息"""
    try:
        # 总物料数
        total_materials = db.query(Material).count()
        
        # 各状态物料数
        active_materials = db.query(Material).filter(Material.status == MaterialStatus.ACTIVE).count()
        inactive_materials = db.query(Material).filter(Material.status == MaterialStatus.INACTIVE).count()
        discontinued_materials = db.query(Material).filter(Material.status == MaterialStatus.DISCONTINUED).count()
        
        # 各分类物料数
        raw_materials = db.query(Material).filter(Material.category == MaterialCategory.RAW_MATERIAL).count()
        semi_finished = db.query(Material).filter(Material.category == MaterialCategory.SEMI_FINISHED).count()
        finished_products = db.query(Material).filter(Material.category == MaterialCategory.FINISHED_PRODUCT).count()
        consumables = db.query(Material).filter(Material.category == MaterialCategory.CONSUMABLE).count()
        tools = db.query(Material).filter(Material.category == MaterialCategory.TOOL).count()
        
        # 库存预警
        low_stock_materials = db.query(Material).filter(Material.current_stock <= Material.min_stock).count()
        out_of_stock_materials = db.query(Material).filter(Material.current_stock <= 0).count()
        overstock_materials = db.query(Material).filter(Material.current_stock >= Material.max_stock).count()
        
        # 总库存价值
        total_stock_value_result = db.query(
            db.func.sum(Material.current_stock * Material.unit_price)
        ).scalar()
        total_stock_value = float(total_stock_value_result) if total_stock_value_result else 0.0
        
        # 本月新增物料
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new_materials = db.query(Material).filter(Material.created_at >= current_month_start).count()
        
        material_stats = MaterialStats(
            total_materials=total_materials,
            active_materials=active_materials,
            inactive_materials=inactive_materials,
            discontinued_materials=discontinued_materials,
            raw_materials=raw_materials,
            semi_finished=semi_finished,
            finished_products=finished_products,
            consumables=consumables,
            tools=tools,
            low_stock_materials=low_stock_materials,
            out_of_stock_materials=out_of_stock_materials,
            overstock_materials=overstock_materials,
            total_stock_value=total_stock_value,
            monthly_new_materials=monthly_new_materials
        )
        
        return ResponseModel(
            code=200,
            message="获取物料统计成功",
            data=material_stats
        )
        
    except Exception as e:
        logger.error(f"获取物料统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取物料统计服务异常"
        )

@router.get("/alerts/stock", response_model=ResponseModel[List[MaterialStockAlert]])
async def get_stock_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取库存预警信息"""
    try:
        # 获取库存预警的物料
        alert_materials = db.query(Material).filter(
            or_(
                Material.current_stock <= 0,  # 缺货
                Material.current_stock <= Material.min_stock,  # 库存不足
                Material.current_stock >= Material.max_stock   # 库存过多
            )
        ).all()
        
        alerts = []
        for material in alert_materials:
            alert_type = "正常"
            alert_level = "info"
            
            if material.current_stock <= 0:
                alert_type = "缺货"
                alert_level = "error"
            elif material.current_stock <= material.min_stock:
                alert_type = "库存不足"
                alert_level = "warning"
            elif material.current_stock >= material.max_stock:
                alert_type = "库存过多"
                alert_level = "warning"
            
            alert = MaterialStockAlert(
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                current_stock=material.current_stock,
                min_stock=material.min_stock,
                max_stock=material.max_stock,
                alert_type=alert_type,
                alert_level=alert_level,
                supplier=material.supplier,
                lead_time=material.lead_time
            )
            alerts.append(alert)
        
        return ResponseModel(
            code=200,
            message="获取库存预警成功",
            data=alerts
        )
        
    except Exception as e:
        logger.error(f"获取库存预警异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取库存预警服务异常"
        )