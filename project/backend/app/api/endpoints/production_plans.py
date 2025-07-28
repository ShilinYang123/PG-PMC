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
from app.services.production_scheduling_service import (
    get_production_scheduling_service, SchedulingStrategy
)
from app.utils.scheduler import ProductionScheduler, ScheduleStrategy
from datetime import datetime, timedelta, date
from typing import Dict, Any
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

@router.post("/scheduling/auto", response_model=ResponseModel[List[Dict[str, Any]]])
async def auto_schedule_plans(
    plan_ids: Optional[List[int]] = None,
    strategy: Optional[str] = Query("balanced", description="排程策略"),
    start_date: Optional[datetime] = Query(None, description="排程开始时间"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """自动排程生产计划"""
    try:
        # 获取排程服务
        scheduling_service = get_production_scheduling_service(db)
        
        # 转换策略
        strategy_map = {
            "earliest_due_date": SchedulingStrategy.EARLIEST_DUE_DATE,
            "shortest_processing_time": SchedulingStrategy.SHORTEST_PROCESSING_TIME,
            "critical_ratio": SchedulingStrategy.CRITICAL_RATIO,
            "priority_first": SchedulingStrategy.PRIORITY_FIRST,
            "balanced": SchedulingStrategy.BALANCED
        }
        
        scheduling_strategy = strategy_map.get(strategy, SchedulingStrategy.BALANCED)
        
        # 执行自动排程
        results = scheduling_service.auto_schedule_plans(
            plan_ids=plan_ids,
            strategy=scheduling_strategy,
            start_date=start_date
        )
        
        # 转换结果为字典格式
        result_data = []
        for result in results:
            result_data.append({
                "plan_id": result.plan_id,
                "scheduled_start_date": result.scheduled_start_date.isoformat(),
                "scheduled_end_date": result.scheduled_end_date.isoformat(),
                "assigned_resources": result.assigned_resources,
                "estimated_duration_hours": result.estimated_duration.total_seconds() / 3600,
                "conflicts": result.conflicts,
                "feasibility_score": result.feasibility_score
            })
        
        return ResponseModel(
            success=True,
            message=f"成功排程 {len(results)} 个生产计划",
            data=result_data
        )
        
    except Exception as e:
        logger.error(f"自动排程失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动排程失败: {str(e)}"
        )

@router.post("/scheduling/manual/{plan_id}", response_model=ResponseModel[Dict[str, Any]])
async def manual_schedule_plan(
    plan_id: int,
    start_date: datetime,
    end_date: datetime,
    workshop: Optional[str] = None,
    production_line: Optional[str] = None,
    responsible_person: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """手动排程单个生产计划"""
    try:
        # 获取排程服务
        scheduling_service = get_production_scheduling_service(db)
        
        # 构建资源分配
        resources = {}
        if workshop:
            resources["workshop"] = workshop
        if production_line:
            resources["production_line"] = production_line
        if responsible_person:
            resources["responsible_person"] = responsible_person
        
        # 执行手动排程
        result = scheduling_service.manual_schedule_plan(
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            resources=resources
        )
        
        # 转换结果
        result_data = {
            "plan_id": result.plan_id,
            "scheduled_start_date": result.scheduled_start_date.isoformat(),
            "scheduled_end_date": result.scheduled_end_date.isoformat(),
            "assigned_resources": result.assigned_resources,
            "estimated_duration_hours": result.estimated_duration.total_seconds() / 3600,
            "conflicts": result.conflicts,
            "feasibility_score": result.feasibility_score
        }
        
        return ResponseModel(
            success=True,
            message="手动排程成功",
            data=result_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"手动排程失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动排程失败: {str(e)}"
        )

@router.post("/scheduling/reschedule/{plan_id}", response_model=ResponseModel[Dict[str, Any]])
async def reschedule_plan(
    plan_id: int,
    new_priority: Optional[PlanPriority] = None,
    new_due_date: Optional[date] = None,
    strategy: Optional[str] = Query("balanced", description="排程策略"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重新排程生产计划"""
    try:
        # 获取排程服务
        scheduling_service = get_production_scheduling_service(db)
        
        # 转换策略
        strategy_map = {
            "earliest_due_date": SchedulingStrategy.EARLIEST_DUE_DATE,
            "shortest_processing_time": SchedulingStrategy.SHORTEST_PROCESSING_TIME,
            "critical_ratio": SchedulingStrategy.CRITICAL_RATIO,
            "priority_first": SchedulingStrategy.PRIORITY_FIRST,
            "balanced": SchedulingStrategy.BALANCED
        }
        
        scheduling_strategy = strategy_map.get(strategy, SchedulingStrategy.BALANCED)
        
        # 执行重新排程
        result = scheduling_service.reschedule_plan(
            plan_id=plan_id,
            new_priority=new_priority,
            new_due_date=new_due_date,
            strategy=scheduling_strategy
        )
        
        # 转换结果
        result_data = {
            "plan_id": result.plan_id,
            "scheduled_start_date": result.scheduled_start_date.isoformat(),
            "scheduled_end_date": result.scheduled_end_date.isoformat(),
            "assigned_resources": result.assigned_resources,
            "estimated_duration_hours": result.estimated_duration.total_seconds() / 3600,
            "conflicts": result.conflicts,
            "feasibility_score": result.feasibility_score
        }
        
        return ResponseModel(
            success=True,
            message="重新排程成功",
            data=result_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"重新排程失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新排程失败: {str(e)}"
        )

@router.get("/scheduling/gantt-data", response_model=ResponseModel[Dict[str, Any]])
async def get_scheduling_gantt_data(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    workshop: Optional[str] = Query(None, description="车间筛选"),
    production_line: Optional[str] = Query(None, description="生产线筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取排程甘特图数据"""
    try:
        # 获取排程服务
        scheduling_service = get_production_scheduling_service(db)
        
        # 获取甘特图数据
        gantt_data = scheduling_service.get_gantt_chart_data(
            start_date=start_date,
            end_date=end_date,
            workshop=workshop,
            production_line=production_line
        )
        
        return ResponseModel(
            success=True,
            message="获取甘特图数据成功",
            data=gantt_data
        )
        
    except Exception as e:
        logger.error(f"获取甘特图数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取甘特图数据失败: {str(e)}"
        )

@router.get("/scheduling/conflicts", response_model=ResponseModel[Dict[str, Any]])
async def analyze_scheduling_conflicts(
    start_date: Optional[date] = Query(None, description="分析开始日期"),
    end_date: Optional[date] = Query(None, description="分析结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分析排程冲突"""
    try:
        # 获取排程服务
        scheduling_service = get_production_scheduling_service(db)
        
        # 分析冲突
        conflicts = scheduling_service.analyze_scheduling_conflicts(
            start_date=start_date,
            end_date=end_date
        )
        
        return ResponseModel(
            success=True,
            message="排程冲突分析完成",
            data=conflicts
        )
        
    except Exception as e:
        logger.error(f"排程冲突分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"排程冲突分析失败: {str(e)}"
        )

@router.post("/schedule", response_model=ResponseModel[List[dict]])
async def schedule_production_plans(
    plan_ids: List[int],
    strategy: ScheduleStrategy = ScheduleStrategy.BALANCED,
    start_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """执行生产计划排程"""
    try:
        scheduler = ProductionScheduler(db)
        results = scheduler.schedule_production_plans(plan_ids, strategy, start_date)
        
        # 更新数据库中的排程结果
        for result in results:
            plan = db.query(ProductionPlan).filter(ProductionPlan.id == result.plan_id).first()
            if plan:
                plan.plan_start_date = result.scheduled_start
                plan.plan_end_date = result.scheduled_end
                plan.workshop = result.assigned_workshop
                plan.production_line = result.assigned_line
                plan.updated_by = current_user.username
                plan.updated_at = datetime.now()
        
        db.commit()
        
        # 转换为响应格式
        schedule_data = []
        for result in results:
            schedule_data.append({
                "plan_id": result.plan_id,
                "scheduled_start": result.scheduled_start.isoformat(),
                "scheduled_end": result.scheduled_end.isoformat(),
                "assigned_workshop": result.assigned_workshop,
                "assigned_line": result.assigned_line,
                "resource_utilization": result.resource_utilization
            })
        
        logger.info(f"Successfully scheduled {len(results)} production plans")
        return ResponseModel(
            code=200,
            message="生产计划排程成功",
            data=schedule_data
        )
        
    except Exception as e:
        logger.error(f"Error scheduling production plans: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"排程失败: {str(e)}"
        )

@router.get("/gantt/{plan_ids}", response_model=ResponseModel[dict])
async def get_gantt_chart_data(
    plan_ids: str,  # 逗号分隔的计划ID列表
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取甘特图数据"""
    try:
        # 解析计划ID列表
        plan_id_list = [int(id.strip()) for id in plan_ids.split(',') if id.strip().isdigit()]
        
        if not plan_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的计划ID列表"
            )
        
        scheduler = ProductionScheduler(db)
        
        # 获取现有的排程结果
        plans = db.query(ProductionPlan).filter(
            ProductionPlan.id.in_(plan_id_list),
            ProductionPlan.plan_start_date.isnot(None),
            ProductionPlan.plan_end_date.isnot(None)
        ).all()
        
        # 构建排程结果
        from app.utils.scheduler import ScheduleResult
        results = []
        for plan in plans:
            result = ScheduleResult(
                plan_id=plan.id,
                scheduled_start=plan.plan_start_date,
                scheduled_end=plan.plan_end_date,
                assigned_workshop=plan.workshop or "默认车间",
                assigned_line=plan.production_line or "默认生产线",
                resource_utilization=0.8  # 默认利用率
            )
            results.append(result)
        
        # 生成甘特图数据
        gantt_data = scheduler.get_gantt_data(results)
        
        logger.info(f"Generated Gantt chart data for {len(results)} plans")
        return ResponseModel(
            code=200,
            message="获取甘特图数据成功",
            data=gantt_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"参数错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting Gantt chart data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取甘特图数据失败: {str(e)}"
        )

@router.post("/optimize-schedule", response_model=ResponseModel[List[dict]])
async def optimize_production_schedule(
    plan_ids: List[int],
    constraints: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """优化生产排程"""
    try:
        scheduler = ProductionScheduler(db)
        
        # 使用平衡策略进行优化排程
        results = scheduler.schedule_production_plans(
            plan_ids, 
            ScheduleStrategy.BALANCED,
            datetime.now()
        )
        
        # 计算优化指标
        optimization_metrics = {
            "total_plans": len(results),
            "avg_utilization": sum(r.resource_utilization for r in results) / len(results) if results else 0,
            "total_duration": 0,
            "resource_distribution": {}
        }
        
        if results:
            start_time = min(r.scheduled_start for r in results)
            end_time = max(r.scheduled_end for r in results)
            optimization_metrics["total_duration"] = (end_time - start_time).days
            
            # 统计资源分布
            for result in results:
                workshop = result.assigned_workshop
                if workshop not in optimization_metrics["resource_distribution"]:
                    optimization_metrics["resource_distribution"][workshop] = 0
                optimization_metrics["resource_distribution"][workshop] += 1
        
        # 转换为响应格式
        schedule_data = []
        for result in results:
            schedule_data.append({
                "plan_id": result.plan_id,
                "scheduled_start": result.scheduled_start.isoformat(),
                "scheduled_end": result.scheduled_end.isoformat(),
                "assigned_workshop": result.assigned_workshop,
                "assigned_line": result.assigned_line,
                "resource_utilization": result.resource_utilization
            })
        
        response_data = {
            "schedule": schedule_data,
            "metrics": optimization_metrics
        }
        
        logger.info(f"Optimized schedule for {len(results)} production plans")
        return ResponseModel(
            code=200,
            message="生产排程优化成功",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error optimizing production schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"排程优化失败: {str(e)}"
        )