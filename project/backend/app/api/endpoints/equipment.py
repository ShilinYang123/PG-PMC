from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.equipment import Equipment, MaintenanceRecord, EquipmentStatus, MaintenanceType
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.equipment import (
    EquipmentCreate, EquipmentUpdate, EquipmentQuery, EquipmentDetail,
    MaintenanceRecordCreate, MaintenanceRecordUpdate, MaintenanceRecordDetail,
    EquipmentStats, EquipmentSummary, EquipmentStatusUpdate
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=PagedResponseModel[EquipmentDetail])
async def get_equipment_list(
    query: EquipmentQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取设备列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    Equipment.equipment_code.contains(query.keyword),
                    Equipment.equipment_name.contains(query.keyword),
                    Equipment.model.contains(query.keyword),
                    Equipment.manufacturer.contains(query.keyword)
                )
            )
        
        if query.status:
            filters.append(Equipment.status == query.status)
        
        if query.category:
            filters.append(Equipment.category.contains(query.category))
        
        if query.workshop:
            filters.append(Equipment.workshop.contains(query.workshop))
        
        if query.responsible_person:
            filters.append(Equipment.responsible_person.contains(query.responsible_person))
        
        if query.manufacturer:
            filters.append(Equipment.manufacturer.contains(query.manufacturer))
        
        if query.purchase_date_start:
            filters.append(Equipment.purchase_date >= query.purchase_date_start)
        
        if query.purchase_date_end:
            filters.append(Equipment.purchase_date <= query.purchase_date_end)
        
        if query.warranty_expiry_start:
            filters.append(Equipment.warranty_expiry >= query.warranty_expiry_start)
        
        if query.warranty_expiry_end:
            filters.append(Equipment.warranty_expiry <= query.warranty_expiry_end)
        
        if query.price_min is not None:
            filters.append(Equipment.purchase_price >= query.price_min)
        
        if query.price_max is not None:
            filters.append(Equipment.purchase_price <= query.price_max)
        
        if query.maintenance_due:
            # 查询需要维护的设备（下次维护日期在指定天数内）
            due_date = datetime.now().date() + timedelta(days=query.maintenance_due)
            filters.append(Equipment.next_maintenance_date <= due_date)
        
        if query.warranty_expiring:
            # 查询保修即将到期的设备（保修到期日期在指定天数内）
            expiry_date = datetime.now().date() + timedelta(days=query.warranty_expiring)
            filters.append(
                and_(
                    Equipment.warranty_expiry <= expiry_date,
                    Equipment.warranty_expiry >= datetime.now().date()
                )
            )
        
        # 构建基础查询
        base_query = db.query(Equipment)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(Equipment, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(Equipment.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        equipment_list = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        equipment_details = []
        for equipment in equipment_list:
            # 计算设备状态指标
            total_maintenance = db.query(MaintenanceRecord).filter(MaintenanceRecord.equipment_id == equipment.id).count()
            recent_maintenance = db.query(MaintenanceRecord).filter(
                and_(
                    MaintenanceRecord.equipment_id == equipment.id,
                    MaintenanceRecord.maintenance_date >= datetime.now().date() - timedelta(days=30)
                )
            ).count()
            
            # 计算使用年限
            usage_years = (datetime.now().date() - equipment.purchase_date).days / 365.25 if equipment.purchase_date else 0
            
            # 判断维护状态
            maintenance_status = "normal"
            if equipment.next_maintenance_date:
                days_to_maintenance = (equipment.next_maintenance_date - datetime.now().date()).days
                if days_to_maintenance <= 0:
                    maintenance_status = "overdue"
                elif days_to_maintenance <= 7:
                    maintenance_status = "due_soon"
            
            # 判断保修状态
            warranty_status = "valid"
            if equipment.warranty_expiry:
                days_to_expiry = (equipment.warranty_expiry - datetime.now().date()).days
                if days_to_expiry <= 0:
                    warranty_status = "expired"
                elif days_to_expiry <= 30:
                    warranty_status = "expiring_soon"
            
            equipment_detail = EquipmentDetail(
                id=equipment.id,
                equipment_code=equipment.equipment_code,
                equipment_name=equipment.equipment_name,
                category=equipment.category,
                model=equipment.model,
                manufacturer=equipment.manufacturer,
                purchase_date=equipment.purchase_date,
                purchase_price=equipment.purchase_price,
                warranty_expiry=equipment.warranty_expiry,
                status=equipment.status,
                workshop=equipment.workshop,
                location=equipment.location,
                responsible_person=equipment.responsible_person,
                specifications=equipment.specifications,
                operating_parameters=equipment.operating_parameters,
                maintenance_cycle=equipment.maintenance_cycle,
                last_maintenance_date=equipment.last_maintenance_date,
                next_maintenance_date=equipment.next_maintenance_date,
                total_runtime=equipment.total_runtime,
                description=equipment.description,
                remark=equipment.remark,
                usage_years=round(usage_years, 1),
                maintenance_status=maintenance_status,
                warranty_status=warranty_status,
                total_maintenance_count=total_maintenance,
                recent_maintenance_count=recent_maintenance,
                created_at=equipment.created_at,
                updated_at=equipment.updated_at,
                created_by=equipment.created_by,
                updated_by=equipment.updated_by
            )
            equipment_details.append(equipment_detail)
        
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
            message="获取设备列表成功",
            data=equipment_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取设备列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备列表服务异常"
        )

@router.get("/{equipment_id}", response_model=ResponseModel[EquipmentDetail])
async def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取设备详情"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 获取维护记录
        maintenance_records = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.equipment_id == equipment_id
        ).order_by(MaintenanceRecord.maintenance_date.desc()).all()
        
        maintenance_details = []
        for record in maintenance_records:
            maintenance_detail = MaintenanceRecordDetail(
                id=record.id,
                equipment_id=record.equipment_id,
                maintenance_type=record.maintenance_type,
                maintenance_date=record.maintenance_date,
                maintenance_person=record.maintenance_person,
                maintenance_content=record.maintenance_content,
                parts_replaced=record.parts_replaced,
                cost=record.cost,
                duration_hours=record.duration_hours,
                next_maintenance_date=record.next_maintenance_date,
                status=record.status,
                remark=record.remark,
                created_at=record.created_at,
                created_by=record.created_by
            )
            maintenance_details.append(maintenance_detail)
        
        # 计算设备状态指标
        usage_years = (datetime.now().date() - equipment.purchase_date).days / 365.25 if equipment.purchase_date else 0
        
        # 判断维护状态
        maintenance_status = "normal"
        if equipment.next_maintenance_date:
            days_to_maintenance = (equipment.next_maintenance_date - datetime.now().date()).days
            if days_to_maintenance <= 0:
                maintenance_status = "overdue"
            elif days_to_maintenance <= 7:
                maintenance_status = "due_soon"
        
        # 判断保修状态
        warranty_status = "valid"
        if equipment.warranty_expiry:
            days_to_expiry = (equipment.warranty_expiry - datetime.now().date()).days
            if days_to_expiry <= 0:
                warranty_status = "expired"
            elif days_to_expiry <= 30:
                warranty_status = "expiring_soon"
        
        equipment_detail = EquipmentDetail(
            id=equipment.id,
            equipment_code=equipment.equipment_code,
            equipment_name=equipment.equipment_name,
            category=equipment.category,
            model=equipment.model,
            manufacturer=equipment.manufacturer,
            purchase_date=equipment.purchase_date,
            purchase_price=equipment.purchase_price,
            warranty_expiry=equipment.warranty_expiry,
            status=equipment.status,
            workshop=equipment.workshop,
            location=equipment.location,
            responsible_person=equipment.responsible_person,
            specifications=equipment.specifications,
            operating_parameters=equipment.operating_parameters,
            maintenance_cycle=equipment.maintenance_cycle,
            last_maintenance_date=equipment.last_maintenance_date,
            next_maintenance_date=equipment.next_maintenance_date,
            total_runtime=equipment.total_runtime,
            description=equipment.description,
            remark=equipment.remark,
            usage_years=round(usage_years, 1),
            maintenance_status=maintenance_status,
            warranty_status=warranty_status,
            total_maintenance_count=len(maintenance_details),
            recent_maintenance_count=len([r for r in maintenance_details if (datetime.now().date() - r.maintenance_date).days <= 30]),
            maintenance_records=maintenance_details,
            created_at=equipment.created_at,
            updated_at=equipment.updated_at,
            created_by=equipment.created_by,
            updated_by=equipment.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取设备详情成功",
            data=equipment_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备详情服务异常"
        )

@router.post("/", response_model=ResponseModel[EquipmentDetail])
async def create_equipment(
    equipment_data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager"]))
):
    """创建设备"""
    try:
        # 检查设备编号是否已存在
        existing_equipment = db.query(Equipment).filter(Equipment.equipment_code == equipment_data.equipment_code).first()
        if existing_equipment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设备编号已存在"
            )
        
        # 创建设备
        equipment = Equipment(
            equipment_code=equipment_data.equipment_code,
            equipment_name=equipment_data.equipment_name,
            category=equipment_data.category,
            model=equipment_data.model,
            manufacturer=equipment_data.manufacturer,
            purchase_date=equipment_data.purchase_date,
            purchase_price=equipment_data.purchase_price,
            warranty_expiry=equipment_data.warranty_expiry,
            status=equipment_data.status or EquipmentStatus.NORMAL,
            workshop=equipment_data.workshop,
            location=equipment_data.location,
            responsible_person=equipment_data.responsible_person,
            specifications=equipment_data.specifications,
            operating_parameters=equipment_data.operating_parameters,
            maintenance_cycle=equipment_data.maintenance_cycle,
            description=equipment_data.description,
            remark=equipment_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        # 计算下次维护日期
        if equipment_data.maintenance_cycle and equipment_data.purchase_date:
            equipment.next_maintenance_date = equipment_data.purchase_date + timedelta(days=equipment_data.maintenance_cycle)
        
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        
        equipment_detail = EquipmentDetail(
            id=equipment.id,
            equipment_code=equipment.equipment_code,
            equipment_name=equipment.equipment_name,
            category=equipment.category,
            model=equipment.model,
            manufacturer=equipment.manufacturer,
            purchase_date=equipment.purchase_date,
            purchase_price=equipment.purchase_price,
            warranty_expiry=equipment.warranty_expiry,
            status=equipment.status,
            workshop=equipment.workshop,
            location=equipment.location,
            responsible_person=equipment.responsible_person,
            specifications=equipment.specifications,
            operating_parameters=equipment.operating_parameters,
            maintenance_cycle=equipment.maintenance_cycle,
            next_maintenance_date=equipment.next_maintenance_date,
            description=equipment.description,
            remark=equipment.remark,
            created_at=equipment.created_at,
            created_by=equipment.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建设备成功",
            data=equipment_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建设备异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建设备服务异常"
        )

@router.put("/{equipment_id}", response_model=ResponseModel[EquipmentDetail])
async def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager"]))
):
    """更新设备"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 检查设备编号是否已被其他设备使用
        if equipment_data.equipment_code and equipment_data.equipment_code != equipment.equipment_code:
            existing_equipment = db.query(Equipment).filter(
                and_(
                    Equipment.equipment_code == equipment_data.equipment_code,
                    Equipment.id != equipment_id
                )
            ).first()
            if existing_equipment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="设备编号已存在"
                )
        
        # 更新字段
        update_data = equipment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)
        
        equipment.updated_by = current_user.username
        equipment.updated_at = datetime.now()
        
        # 重新计算下次维护日期（如果维护周期有变化）
        if equipment_data.maintenance_cycle is not None and equipment.last_maintenance_date:
            equipment.next_maintenance_date = equipment.last_maintenance_date + timedelta(days=equipment_data.maintenance_cycle)
        
        db.commit()
        db.refresh(equipment)
        
        equipment_detail = EquipmentDetail(
            id=equipment.id,
            equipment_code=equipment.equipment_code,
            equipment_name=equipment.equipment_name,
            category=equipment.category,
            model=equipment.model,
            manufacturer=equipment.manufacturer,
            purchase_date=equipment.purchase_date,
            purchase_price=equipment.purchase_price,
            warranty_expiry=equipment.warranty_expiry,
            status=equipment.status,
            workshop=equipment.workshop,
            location=equipment.location,
            responsible_person=equipment.responsible_person,
            specifications=equipment.specifications,
            operating_parameters=equipment.operating_parameters,
            maintenance_cycle=equipment.maintenance_cycle,
            last_maintenance_date=equipment.last_maintenance_date,
            next_maintenance_date=equipment.next_maintenance_date,
            total_runtime=equipment.total_runtime,
            description=equipment.description,
            remark=equipment.remark,
            updated_at=equipment.updated_at,
            updated_by=equipment.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新设备成功",
            data=equipment_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新设备服务异常"
        )

@router.delete("/{equipment_id}", response_model=ResponseModel[dict])
async def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin"]))
):
    """删除设备"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 检查设备是否正在使用
        if equipment.status == EquipmentStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设备正在运行中，无法删除"
            )
        
        # 删除关联的维护记录
        db.query(MaintenanceRecord).filter(MaintenanceRecord.equipment_id == equipment_id).delete()
        
        # 删除设备
        db.delete(equipment)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除设备成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除设备异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除设备服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[EquipmentStats])
async def get_equipment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取设备统计信息"""
    try:
        # 总设备数
        total_equipment = db.query(Equipment).count()
        
        # 各状态设备数
        normal_equipment = db.query(Equipment).filter(Equipment.status == EquipmentStatus.NORMAL).count()
        running_equipment = db.query(Equipment).filter(Equipment.status == EquipmentStatus.RUNNING).count()
        maintenance_equipment = db.query(Equipment).filter(Equipment.status == EquipmentStatus.MAINTENANCE).count()
        fault_equipment = db.query(Equipment).filter(Equipment.status == EquipmentStatus.FAULT).count()
        retired_equipment = db.query(Equipment).filter(Equipment.status == EquipmentStatus.RETIRED).count()
        
        # 需要维护的设备（下次维护日期在7天内）
        maintenance_due_date = datetime.now().date() + timedelta(days=7)
        maintenance_due_equipment = db.query(Equipment).filter(
            and_(
                Equipment.next_maintenance_date <= maintenance_due_date,
                Equipment.status != EquipmentStatus.RETIRED
            )
        ).count()
        
        # 保修即将到期的设备（保修到期日期在30天内）
        warranty_expiry_date = datetime.now().date() + timedelta(days=30)
        warranty_expiring_equipment = db.query(Equipment).filter(
            and_(
                Equipment.warranty_expiry <= warranty_expiry_date,
                Equipment.warranty_expiry >= datetime.now().date(),
                Equipment.status != EquipmentStatus.RETIRED
            )
        ).count()
        
        # 总设备价值
        total_value_result = db.query(db.func.sum(Equipment.purchase_price)).filter(
            Equipment.status != EquipmentStatus.RETIRED
        ).scalar()
        total_equipment_value = float(total_value_result) if total_value_result else 0.0
        
        # 本月新增设备
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new_equipment = db.query(Equipment).filter(Equipment.created_at >= current_month_start).count()
        
        # 本月维护记录
        monthly_maintenance_records = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.maintenance_date >= current_month_start.date()
        ).count()
        
        # 本月维护费用
        monthly_maintenance_cost_result = db.query(db.func.sum(MaintenanceRecord.cost)).filter(
            MaintenanceRecord.maintenance_date >= current_month_start.date()
        ).scalar()
        monthly_maintenance_cost = float(monthly_maintenance_cost_result) if monthly_maintenance_cost_result else 0.0
        
        # 设备利用率（运行设备数 / 可用设备数）
        available_equipment = total_equipment - retired_equipment - fault_equipment
        utilization_rate = (running_equipment / available_equipment * 100) if available_equipment > 0 else 0.0
        
        equipment_stats = EquipmentStats(
            total_equipment=total_equipment,
            normal_equipment=normal_equipment,
            running_equipment=running_equipment,
            maintenance_equipment=maintenance_equipment,
            fault_equipment=fault_equipment,
            retired_equipment=retired_equipment,
            maintenance_due_equipment=maintenance_due_equipment,
            warranty_expiring_equipment=warranty_expiring_equipment,
            total_equipment_value=total_equipment_value,
            utilization_rate=round(utilization_rate, 2),
            monthly_new_equipment=monthly_new_equipment,
            monthly_maintenance_records=monthly_maintenance_records,
            monthly_maintenance_cost=monthly_maintenance_cost
        )
        
        return ResponseModel(
            code=200,
            message="获取设备统计成功",
            data=equipment_stats
        )
        
    except Exception as e:
        logger.error(f"获取设备统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备统计服务异常"
        )

@router.post("/{equipment_id}/maintenance", response_model=ResponseModel[MaintenanceRecordDetail])
async def create_maintenance_record(
    equipment_id: int,
    maintenance_data: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建维护记录"""
    try:
        # 检查设备是否存在
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 创建维护记录
        maintenance_record = MaintenanceRecord(
            equipment_id=equipment_id,
            maintenance_type=maintenance_data.maintenance_type,
            maintenance_date=maintenance_data.maintenance_date,
            maintenance_person=maintenance_data.maintenance_person,
            maintenance_content=maintenance_data.maintenance_content,
            parts_replaced=maintenance_data.parts_replaced,
            cost=maintenance_data.cost,
            duration_hours=maintenance_data.duration_hours,
            next_maintenance_date=maintenance_data.next_maintenance_date,
            status=maintenance_data.status or "completed",
            remark=maintenance_data.remark,
            created_by=current_user.username
        )
        
        db.add(maintenance_record)
        
        # 更新设备的维护信息
        equipment.last_maintenance_date = maintenance_data.maintenance_date
        if maintenance_data.next_maintenance_date:
            equipment.next_maintenance_date = maintenance_data.next_maintenance_date
        elif equipment.maintenance_cycle:
            equipment.next_maintenance_date = maintenance_data.maintenance_date + timedelta(days=equipment.maintenance_cycle)
        
        # 如果是故障维修且维修完成，更新设备状态
        if maintenance_data.maintenance_type == MaintenanceType.REPAIR and maintenance_data.status == "completed":
            if equipment.status == EquipmentStatus.FAULT:
                equipment.status = EquipmentStatus.NORMAL
        
        equipment.updated_by = current_user.username
        equipment.updated_at = datetime.now()
        
        db.commit()
        db.refresh(maintenance_record)
        
        maintenance_detail = MaintenanceRecordDetail(
            id=maintenance_record.id,
            equipment_id=maintenance_record.equipment_id,
            maintenance_type=maintenance_record.maintenance_type,
            maintenance_date=maintenance_record.maintenance_date,
            maintenance_person=maintenance_record.maintenance_person,
            maintenance_content=maintenance_record.maintenance_content,
            parts_replaced=maintenance_record.parts_replaced,
            cost=maintenance_record.cost,
            duration_hours=maintenance_record.duration_hours,
            next_maintenance_date=maintenance_record.next_maintenance_date,
            status=maintenance_record.status,
            remark=maintenance_record.remark,
            created_at=maintenance_record.created_at,
            created_by=maintenance_record.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建维护记录成功",
            data=maintenance_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建维护记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建维护记录服务异常"
        )

@router.put("/{equipment_id}/status", response_model=ResponseModel[EquipmentDetail])
async def update_equipment_status(
    equipment_id: int,
    status_data: EquipmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新设备状态"""
    try:
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备不存在"
            )
        
        # 更新设备状态
        equipment.status = status_data.status
        if status_data.remark:
            equipment.remark = status_data.remark
        
        equipment.updated_by = current_user.username
        equipment.updated_at = datetime.now()
        
        db.commit()
        db.refresh(equipment)
        
        equipment_detail = EquipmentDetail(
            id=equipment.id,
            equipment_code=equipment.equipment_code,
            equipment_name=equipment.equipment_name,
            status=equipment.status,
            workshop=equipment.workshop,
            location=equipment.location,
            responsible_person=equipment.responsible_person,
            remark=equipment.remark,
            updated_at=equipment.updated_at,
            updated_by=equipment.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新设备状态成功",
            data=equipment_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备状态异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新设备状态服务异常"
        )

@router.get("/maintenance/alerts", response_model=ResponseModel[List[EquipmentSummary]])
async def get_maintenance_alerts(
    days: int = Query(7, description="提前天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取维护提醒"""
    try:
        alert_date = datetime.now().date() + timedelta(days=days)
        
        equipment_list = db.query(Equipment).filter(
            and_(
                Equipment.next_maintenance_date <= alert_date,
                Equipment.status != EquipmentStatus.RETIRED
            )
        ).order_by(Equipment.next_maintenance_date.asc()).all()
        
        alerts = []
        for equipment in equipment_list:
            days_to_maintenance = (equipment.next_maintenance_date - datetime.now().date()).days if equipment.next_maintenance_date else 0
            
            alert = EquipmentSummary(
                id=equipment.id,
                equipment_code=equipment.equipment_code,
                equipment_name=equipment.equipment_name,
                category=equipment.category,
                status=equipment.status,
                workshop=equipment.workshop,
                responsible_person=equipment.responsible_person,
                next_maintenance_date=equipment.next_maintenance_date,
                days_to_maintenance=days_to_maintenance,
                created_at=equipment.created_at
            )
            alerts.append(alert)
        
        return ResponseModel(
            code=200,
            message="获取维护提醒成功",
            data=alerts
        )
        
    except Exception as e:
        logger.error(f"获取维护提醒异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取维护提醒服务异常"
        )