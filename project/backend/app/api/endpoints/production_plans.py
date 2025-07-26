from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority
from app.models.order import Order
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.production_plan import (
    ProductionPlanCreate, ProductionPlanUpdate, ProductionPlanQuery, ProductionPlanDetail,
    ProductionStageCreate, ProductionStageUpdate, ProductionStageDetail,
    ProductionPlanStats, ProductionPlanSummary
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=PagedResponseModel[ProductionPlanDetail])
async def get_production_plans(
    query: ProductionPlanQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产计划列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    ProductionPlan.plan_number.contains(query.keyword),
                    ProductionPlan.plan_name.contains(query.keyword),
                    ProductionPlan.product_name.contains(query.keyword),
                    ProductionPlan.product_model.contains(query.keyword)
                )
            )
        
        if query.status:
            filters.append(ProductionPlan.status == query.status)
        
        if query.priority:
            filters.append(ProductionPlan.priority == query.priority)
        
        if query.workshop:
            filters.append(ProductionPlan.workshop.contains(query.workshop))
        
        if query.production_line:
            filters.append(ProductionPlan.production_line.contains(query.production_line))
        
        if query.responsible_person:
            filters.append(ProductionPlan.responsible_person.contains(query.responsible_person))
        
        if query.planned_start_date_start:
            filters.append(ProductionPlan.planned_start_date >= query.planned_start_date_start)
        
        if query.planned_start_date_end:
            filters.append(ProductionPlan.planned_start_date <= query.planned_start_date_end)
        
        if query.planned_end_date_start:
            filters.append(ProductionPlan.planned_end_date >= query.planned_end_date_start)
        
        if query.planned_end_date_end:
            filters.append(ProductionPlan.planned_end_date <= query.planned_end_date_end)
        
        if query.order_id:
            filters.append(ProductionPlan.order_id == query.order_id)
        
        # 构建基础查询
        base_query = db.query(ProductionPlan)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(ProductionPlan, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(ProductionPlan.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        plans = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        plan_details = []
        for plan in plans:
            # 获取关联订单信息
            order = db.query(Order).filter(Order.id == plan.order_id).first() if plan.order_id else None
            
            plan_detail = ProductionPlanDetail(
                id=plan.id,
                plan_number=plan.plan_number,
                plan_name=plan.plan_name,
                order_id=plan.order_id,
                order_number=order.order_number if order else None,
                product_name=plan.product_name,
                product_model=plan.product_model,
                product_spec=plan.product_spec,
                planned_quantity=plan.planned_quantity,
                actual_quantity=plan.actual_quantity,
                unit=plan.unit,
                planned_start_date=plan.planned_start_date,
                planned_end_date=plan.planned_end_date,
                actual_start_date=plan.actual_start_date,
                actual_end_date=plan.actual_end_date,
                status=plan.status,
                priority=plan.priority,
                progress=plan.progress,
                workshop=plan.workshop,
                production_line=plan.production_line,
                responsible_person=plan.responsible_person,
                team_members=plan.team_members,
                process_flow=plan.process_flow,
                estimated_cost=plan.estimated_cost,
                actual_cost=plan.actual_cost,
                remark=plan.remark,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
                created_by=plan.created_by,
                updated_by=plan.updated_by
            )
            plan_details.append(plan_detail)
        
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
            message="获取生产计划列表成功",
            data=plan_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取生产计划列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取生产计划列表服务异常"
        )

@router.get("/{plan_id}", response_model=ResponseModel[ProductionPlanDetail])
async def get_production_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产计划详情"""
    try:
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生产计划不存在"
            )
        
        # 获取关联订单信息
        order = db.query(Order).filter(Order.id == plan.order_id).first() if plan.order_id else None
        
        # 获取生产阶段
        stages = db.query(ProductionStage).filter(ProductionStage.plan_id == plan_id).order_by(ProductionStage.stage_sequence).all()
        stage_details = []
        for stage in stages:
            stage_detail = ProductionStageDetail(
                id=stage.id,
                plan_id=stage.plan_id,
                stage_number=stage.stage_number,
                stage_name=stage.stage_name,
                stage_sequence=stage.stage_sequence,
                description=stage.description,
                planned_start_date=stage.planned_start_date,
                planned_end_date=stage.planned_end_date,
                actual_start_date=stage.actual_start_date,
                actual_end_date=stage.actual_end_date,
                status=stage.status,
                progress=stage.progress,
                workshop=stage.workshop,
                production_line=stage.production_line,
                responsible_person=stage.responsible_person,
                team_members=stage.team_members,
                quality_checkpoints=stage.quality_checkpoints,
                remark=stage.remark,
                created_at=stage.created_at,
                updated_at=stage.updated_at
            )
            stage_details.append(stage_detail)
        
        plan_detail = ProductionPlanDetail(
            id=plan.id,
            plan_number=plan.plan_number,
            plan_name=plan.plan_name,
            order_id=plan.order_id,
            order_number=order.order_number if order else None,
            product_name=plan.product_name,
            product_model=plan.product_model,
            product_spec=plan.product_spec,
            planned_quantity=plan.planned_quantity,
            actual_quantity=plan.actual_quantity,
            unit=plan.unit,
            planned_start_date=plan.planned_start_date,
            planned_end_date=plan.planned_end_date,
            actual_start_date=plan.actual_start_date,
            actual_end_date=plan.actual_end_date,
            status=plan.status,
            priority=plan.priority,
            progress=plan.progress,
            workshop=plan.workshop,
            production_line=plan.production_line,
            responsible_person=plan.responsible_person,
            team_members=plan.team_members,
            process_flow=plan.process_flow,
            estimated_cost=plan.estimated_cost,
            actual_cost=plan.actual_cost,
            remark=plan.remark,
            stages=stage_details,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            created_by=plan.created_by,
            updated_by=plan.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取生产计划详情成功",
            data=plan_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取生产计划详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取生产计划详情服务异常"
        )

@router.post("/", response_model=ResponseModel[ProductionPlanDetail])
async def create_production_plan(
    plan_data: ProductionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建生产计划"""
    try:
        # 检查计划编号是否已存在
        existing_plan = db.query(ProductionPlan).filter(ProductionPlan.plan_number == plan_data.plan_number).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="计划编号已存在"
            )
        
        # 检查关联订单是否存在
        if plan_data.order_id:
            order = db.query(Order).filter(Order.id == plan_data.order_id).first()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="关联订单不存在"
                )
        
        # 创建生产计划
        plan = ProductionPlan(
            plan_number=plan_data.plan_number,
            plan_name=plan_data.plan_name,
            order_id=plan_data.order_id,
            product_name=plan_data.product_name,
            product_model=plan_data.product_model,
            product_spec=plan_data.product_spec,
            planned_quantity=plan_data.planned_quantity,
            unit=plan_data.unit,
            planned_start_date=plan_data.planned_start_date,
            planned_end_date=plan_data.planned_end_date,
            status=plan_data.status or PlanStatus.DRAFT,
            priority=plan_data.priority or PlanPriority.MEDIUM,
            workshop=plan_data.workshop,
            production_line=plan_data.production_line,
            responsible_person=plan_data.responsible_person,
            team_members=plan_data.team_members,
            process_flow=plan_data.process_flow,
            estimated_cost=plan_data.estimated_cost,
            remark=plan_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # 创建生产阶段
        if plan_data.stages:
            for stage_data in plan_data.stages:
                stage = ProductionStage(
                    plan_id=plan.id,
                    stage_number=stage_data.stage_number,
                    stage_name=stage_data.stage_name,
                    stage_sequence=stage_data.stage_sequence,
                    description=stage_data.description,
                    planned_start_date=stage_data.planned_start_date,
                    planned_end_date=stage_data.planned_end_date,
                    workshop=stage_data.workshop,
                    production_line=stage_data.production_line,
                    responsible_person=stage_data.responsible_person,
                    team_members=stage_data.team_members,
                    quality_checkpoints=stage_data.quality_checkpoints,
                    remark=stage_data.remark,
                    created_by=current_user.username,
                    updated_by=current_user.username
                )
                db.add(stage)
            
            db.commit()
        
        # 获取完整的计划详情
        plan_detail = ProductionPlanDetail(
            id=plan.id,
            plan_number=plan.plan_number,
            plan_name=plan.plan_name,
            order_id=plan.order_id,
            product_name=plan.product_name,
            product_model=plan.product_model,
            product_spec=plan.product_spec,
            planned_quantity=plan.planned_quantity,
            unit=plan.unit,
            planned_start_date=plan.planned_start_date,
            planned_end_date=plan.planned_end_date,
            status=plan.status,
            priority=plan.priority,
            workshop=plan.workshop,
            production_line=plan.production_line,
            responsible_person=plan.responsible_person,
            team_members=plan.team_members,
            process_flow=plan.process_flow,
            estimated_cost=plan.estimated_cost,
            remark=plan.remark,
            created_at=plan.created_at,
            created_by=plan.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建生产计划成功",
            data=plan_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建生产计划异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建生产计划服务异常"
        )

@router.put("/{plan_id}", response_model=ResponseModel[ProductionPlanDetail])
async def update_production_plan(
    plan_id: int,
    plan_data: ProductionPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新生产计划"""
    try:
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生产计划不存在"
            )
        
        # 更新字段
        update_data = plan_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)
        
        plan.updated_by = current_user.username
        plan.updated_at = datetime.now()
        
        db.commit()
        db.refresh(plan)
        
        plan_detail = ProductionPlanDetail(
            id=plan.id,
            plan_number=plan.plan_number,
            plan_name=plan.plan_name,
            order_id=plan.order_id,
            product_name=plan.product_name,
            product_model=plan.product_model,
            product_spec=plan.product_spec,
            planned_quantity=plan.planned_quantity,
            actual_quantity=plan.actual_quantity,
            unit=plan.unit,
            planned_start_date=plan.planned_start_date,
            planned_end_date=plan.planned_end_date,
            actual_start_date=plan.actual_start_date,
            actual_end_date=plan.actual_end_date,
            status=plan.status,
            priority=plan.priority,
            progress=plan.progress,
            workshop=plan.workshop,
            production_line=plan.production_line,
            responsible_person=plan.responsible_person,
            team_members=plan.team_members,
            process_flow=plan.process_flow,
            estimated_cost=plan.estimated_cost,
            actual_cost=plan.actual_cost,
            remark=plan.remark,
            updated_at=plan.updated_at,
            updated_by=plan.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新生产计划成功",
            data=plan_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新生产计划异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新生产计划服务异常"
        )

@router.delete("/{plan_id}", response_model=ResponseModel[dict])
async def delete_production_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除生产计划"""
    try:
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="生产计划不存在"
            )
        
        # 检查计划状态，只有草稿状态的计划才能删除
        if plan.status not in [PlanStatus.DRAFT]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有草稿状态的计划才能删除"
            )
        
        # 删除关联的生产阶段
        db.query(ProductionStage).filter(ProductionStage.plan_id == plan_id).delete()
        
        # 删除生产计划
        db.delete(plan)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除生产计划成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除生产计划异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除生产计划服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[ProductionPlanStats])
async def get_production_plan_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取生产计划统计信息"""
    try:
        # 总计划数
        total_plans = db.query(ProductionPlan).count()
        
        # 各状态计划数
        draft_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.DRAFT).count()
        confirmed_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.CONFIRMED).count()
        in_progress_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.IN_PROGRESS).count()
        completed_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.COMPLETED).count()
        cancelled_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.CANCELLED).count()
        paused_plans = db.query(ProductionPlan).filter(ProductionPlan.status == PlanStatus.PAUSED).count()
        
        # 本月新增计划
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new_plans = db.query(ProductionPlan).filter(ProductionPlan.created_at >= current_month_start).count()
        
        # 本月完成计划
        monthly_completed_plans = db.query(ProductionPlan).filter(
            and_(
                ProductionPlan.status == PlanStatus.COMPLETED,
                ProductionPlan.updated_at >= current_month_start
            )
        ).count()
        
        # 逾期计划（计划结束日期已过但未完成）
        today = datetime.now().date()
        overdue_plans = db.query(ProductionPlan).filter(
            and_(
                ProductionPlan.planned_end_date < today,
                ProductionPlan.status.in_([PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS])
            )
        ).count()
        
        # 平均进度
        avg_progress_result = db.query(db.func.avg(ProductionPlan.progress)).filter(
            ProductionPlan.status.in_([PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS])
        ).scalar()
        avg_progress = float(avg_progress_result) if avg_progress_result else 0.0
        
        plan_stats = ProductionPlanStats(
            total_plans=total_plans,
            draft_plans=draft_plans,
            confirmed_plans=confirmed_plans,
            in_progress_plans=in_progress_plans,
            completed_plans=completed_plans,
            cancelled_plans=cancelled_plans,
            paused_plans=paused_plans,
            overdue_plans=overdue_plans,
            monthly_new_plans=monthly_new_plans,
            monthly_completed_plans=monthly_completed_plans,
            avg_progress=avg_progress
        )
        
        return ResponseModel(
            code=200,
            message="获取生产计划统计成功",
            data=plan_stats
        )
        
    except Exception as e:
        logger.error(f"获取生产计划统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取生产计划统计服务异常"
        )