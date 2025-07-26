from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.progress import ProgressRecord, StageRecord, QualityRecord, ProgressUpdate, ProgressStatus, QualityResult
from app.models.production_plan import ProductionPlan
from app.models.order import Order
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.progress import (
    ProgressRecordCreate, ProgressRecordUpdate, ProgressRecordQuery, ProgressRecordDetail,
    StageRecordCreate, StageRecordUpdate, StageRecordDetail,
    QualityRecordCreate, QualityRecordUpdate, QualityRecordDetail,
    ProgressUpdateCreate, ProgressUpdateDetail,
    ProgressStats, ProgressSummary
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=PagedResponseModel[ProgressRecordDetail])
async def get_progress_records(
    query: ProgressRecordQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取进度记录列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    ProgressRecord.record_number.contains(query.keyword),
                    ProgressRecord.task_name.contains(query.keyword),
                    ProgressRecord.responsible_person.contains(query.keyword)
                )
            )
        
        if query.status:
            filters.append(ProgressRecord.status == query.status)
        
        if query.plan_id:
            filters.append(ProgressRecord.plan_id == query.plan_id)
        
        if query.order_id:
            filters.append(ProgressRecord.order_id == query.order_id)
        
        if query.responsible_person:
            filters.append(ProgressRecord.responsible_person.contains(query.responsible_person))
        
        if query.start_date_start:
            filters.append(ProgressRecord.start_date >= query.start_date_start)
        
        if query.start_date_end:
            filters.append(ProgressRecord.start_date <= query.start_date_end)
        
        if query.end_date_start:
            filters.append(ProgressRecord.end_date >= query.end_date_start)
        
        if query.end_date_end:
            filters.append(ProgressRecord.end_date <= query.end_date_end)
        
        if query.progress_min is not None:
            filters.append(ProgressRecord.progress >= query.progress_min)
        
        if query.progress_max is not None:
            filters.append(ProgressRecord.progress <= query.progress_max)
        
        # 构建基础查询
        base_query = db.query(ProgressRecord)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(ProgressRecord, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(ProgressRecord.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        records = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        record_details = []
        for record in records:
            # 获取关联信息
            plan = db.query(ProductionPlan).filter(ProductionPlan.id == record.plan_id).first() if record.plan_id else None
            order = db.query(Order).filter(Order.id == record.order_id).first() if record.order_id else None
            
            # 获取阶段记录
            stages = db.query(StageRecord).filter(StageRecord.progress_id == record.id).order_by(StageRecord.stage_sequence).all()
            stage_details = []
            for stage in stages:
                stage_detail = StageRecordDetail(
                    id=stage.id,
                    progress_id=stage.progress_id,
                    stage_name=stage.stage_name,
                    stage_sequence=stage.stage_sequence,
                    planned_start_date=stage.planned_start_date,
                    planned_end_date=stage.planned_end_date,
                    actual_start_date=stage.actual_start_date,
                    actual_end_date=stage.actual_end_date,
                    status=stage.status,
                    progress=stage.progress,
                    responsible_person=stage.responsible_person,
                    remark=stage.remark,
                    created_at=stage.created_at,
                    updated_at=stage.updated_at
                )
                stage_details.append(stage_detail)
            
            # 获取质量记录
            quality_records = db.query(QualityRecord).filter(QualityRecord.progress_id == record.id).all()
            quality_details = []
            for quality in quality_records:
                quality_detail = QualityRecordDetail(
                    id=quality.id,
                    progress_id=quality.progress_id,
                    checkpoint_name=quality.checkpoint_name,
                    check_date=quality.check_date,
                    checker=quality.checker,
                    check_result=quality.check_result,
                    check_details=quality.check_details,
                    defect_quantity=quality.defect_quantity,
                    rework_quantity=quality.rework_quantity,
                    scrap_quantity=quality.scrap_quantity,
                    remark=quality.remark,
                    created_at=quality.created_at
                )
                quality_details.append(quality_detail)
            
            record_detail = ProgressRecordDetail(
                id=record.id,
                record_number=record.record_number,
                task_name=record.task_name,
                plan_id=record.plan_id,
                plan_number=plan.plan_number if plan else None,
                order_id=record.order_id,
                order_number=order.order_number if order else None,
                start_date=record.start_date,
                end_date=record.end_date,
                planned_duration=record.planned_duration,
                actual_duration=record.actual_duration,
                status=record.status,
                progress=record.progress,
                responsible_person=record.responsible_person,
                team_members=record.team_members,
                description=record.description,
                achievements=record.achievements,
                issues=record.issues,
                next_steps=record.next_steps,
                remark=record.remark,
                stages=stage_details,
                quality_records=quality_details,
                created_at=record.created_at,
                updated_at=record.updated_at,
                created_by=record.created_by,
                updated_by=record.updated_by
            )
            record_details.append(record_detail)
        
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
            message="获取进度记录列表成功",
            data=record_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取进度记录列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取进度记录列表服务异常"
        )

@router.get("/{record_id}", response_model=ResponseModel[ProgressRecordDetail])
async def get_progress_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取进度记录详情"""
    try:
        record = db.query(ProgressRecord).filter(ProgressRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="进度记录不存在"
            )
        
        # 获取关联信息
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == record.plan_id).first() if record.plan_id else None
        order = db.query(Order).filter(Order.id == record.order_id).first() if record.order_id else None
        
        # 获取阶段记录
        stages = db.query(StageRecord).filter(StageRecord.progress_id == record_id).order_by(StageRecord.stage_sequence).all()
        stage_details = []
        for stage in stages:
            stage_detail = StageRecordDetail(
                id=stage.id,
                progress_id=stage.progress_id,
                stage_name=stage.stage_name,
                stage_sequence=stage.stage_sequence,
                planned_start_date=stage.planned_start_date,
                planned_end_date=stage.planned_end_date,
                actual_start_date=stage.actual_start_date,
                actual_end_date=stage.actual_end_date,
                status=stage.status,
                progress=stage.progress,
                responsible_person=stage.responsible_person,
                remark=stage.remark,
                created_at=stage.created_at,
                updated_at=stage.updated_at
            )
            stage_details.append(stage_detail)
        
        # 获取质量记录
        quality_records = db.query(QualityRecord).filter(QualityRecord.progress_id == record_id).all()
        quality_details = []
        for quality in quality_records:
            quality_detail = QualityRecordDetail(
                id=quality.id,
                progress_id=quality.progress_id,
                checkpoint_name=quality.checkpoint_name,
                check_date=quality.check_date,
                checker=quality.checker,
                check_result=quality.check_result,
                check_details=quality.check_details,
                defect_quantity=quality.defect_quantity,
                rework_quantity=quality.rework_quantity,
                scrap_quantity=quality.scrap_quantity,
                remark=quality.remark,
                created_at=quality.created_at
            )
            quality_details.append(quality_detail)
        
        # 获取进度更新记录
        updates = db.query(ProgressUpdate).filter(ProgressUpdate.progress_id == record_id).order_by(ProgressUpdate.created_at.desc()).all()
        update_details = []
        for update in updates:
            update_detail = ProgressUpdateDetail(
                id=update.id,
                progress_id=update.progress_id,
                update_date=update.update_date,
                previous_progress=update.previous_progress,
                current_progress=update.current_progress,
                update_content=update.update_content,
                achievements=update.achievements,
                issues=update.issues,
                next_steps=update.next_steps,
                attachments=update.attachments,
                updater=update.updater,
                created_at=update.created_at
            )
            update_details.append(update_detail)
        
        record_detail = ProgressRecordDetail(
            id=record.id,
            record_number=record.record_number,
            task_name=record.task_name,
            plan_id=record.plan_id,
            plan_number=plan.plan_number if plan else None,
            order_id=record.order_id,
            order_number=order.order_number if order else None,
            start_date=record.start_date,
            end_date=record.end_date,
            planned_duration=record.planned_duration,
            actual_duration=record.actual_duration,
            status=record.status,
            progress=record.progress,
            responsible_person=record.responsible_person,
            team_members=record.team_members,
            description=record.description,
            achievements=record.achievements,
            issues=record.issues,
            next_steps=record.next_steps,
            remark=record.remark,
            stages=stage_details,
            quality_records=quality_details,
            updates=update_details,
            created_at=record.created_at,
            updated_at=record.updated_at,
            created_by=record.created_by,
            updated_by=record.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取进度记录详情成功",
            data=record_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度记录详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取进度记录详情服务异常"
        )

@router.post("/", response_model=ResponseModel[ProgressRecordDetail])
async def create_progress_record(
    record_data: ProgressRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建进度记录"""
    try:
        # 检查记录编号是否已存在
        existing_record = db.query(ProgressRecord).filter(ProgressRecord.record_number == record_data.record_number).first()
        if existing_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="记录编号已存在"
            )
        
        # 检查关联计划是否存在
        if record_data.plan_id:
            plan = db.query(ProductionPlan).filter(ProductionPlan.id == record_data.plan_id).first()
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="关联生产计划不存在"
                )
        
        # 检查关联订单是否存在
        if record_data.order_id:
            order = db.query(Order).filter(Order.id == record_data.order_id).first()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="关联订单不存在"
                )
        
        # 创建进度记录
        record = ProgressRecord(
            record_number=record_data.record_number,
            task_name=record_data.task_name,
            plan_id=record_data.plan_id,
            order_id=record_data.order_id,
            start_date=record_data.start_date,
            end_date=record_data.end_date,
            planned_duration=record_data.planned_duration,
            status=record_data.status or ProgressStatus.NOT_STARTED,
            progress=record_data.progress or 0,
            responsible_person=record_data.responsible_person,
            team_members=record_data.team_members,
            description=record_data.description,
            remark=record_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # 创建阶段记录
        if record_data.stages:
            for stage_data in record_data.stages:
                stage = StageRecord(
                    progress_id=record.id,
                    stage_name=stage_data.stage_name,
                    stage_sequence=stage_data.stage_sequence,
                    planned_start_date=stage_data.planned_start_date,
                    planned_end_date=stage_data.planned_end_date,
                    responsible_person=stage_data.responsible_person,
                    remark=stage_data.remark,
                    created_by=current_user.username,
                    updated_by=current_user.username
                )
                db.add(stage)
            
            db.commit()
        
        record_detail = ProgressRecordDetail(
            id=record.id,
            record_number=record.record_number,
            task_name=record.task_name,
            plan_id=record.plan_id,
            order_id=record.order_id,
            start_date=record.start_date,
            end_date=record.end_date,
            planned_duration=record.planned_duration,
            status=record.status,
            progress=record.progress,
            responsible_person=record.responsible_person,
            team_members=record.team_members,
            description=record.description,
            remark=record.remark,
            created_at=record.created_at,
            created_by=record.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建进度记录成功",
            data=record_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建进度记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建进度记录服务异常"
        )

@router.put("/{record_id}", response_model=ResponseModel[ProgressRecordDetail])
async def update_progress_record(
    record_id: int,
    record_data: ProgressRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新进度记录"""
    try:
        record = db.query(ProgressRecord).filter(ProgressRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="进度记录不存在"
            )
        
        # 记录进度变化
        previous_progress = record.progress
        
        # 更新字段
        update_data = record_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        record.updated_by = current_user.username
        record.updated_at = datetime.now()
        
        # 如果进度有变化，创建进度更新记录
        if record_data.progress is not None and record_data.progress != previous_progress:
            progress_update = ProgressUpdate(
                progress_id=record_id,
                update_date=datetime.now().date(),
                previous_progress=previous_progress,
                current_progress=record_data.progress,
                update_content=record_data.achievements or "进度更新",
                achievements=record_data.achievements,
                issues=record_data.issues,
                next_steps=record_data.next_steps,
                updater=current_user.username
            )
            db.add(progress_update)
        
        db.commit()
        db.refresh(record)
        
        record_detail = ProgressRecordDetail(
            id=record.id,
            record_number=record.record_number,
            task_name=record.task_name,
            plan_id=record.plan_id,
            order_id=record.order_id,
            start_date=record.start_date,
            end_date=record.end_date,
            planned_duration=record.planned_duration,
            actual_duration=record.actual_duration,
            status=record.status,
            progress=record.progress,
            responsible_person=record.responsible_person,
            team_members=record.team_members,
            description=record.description,
            achievements=record.achievements,
            issues=record.issues,
            next_steps=record.next_steps,
            remark=record.remark,
            updated_at=record.updated_at,
            updated_by=record.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新进度记录成功",
            data=record_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新进度记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新进度记录服务异常"
        )

@router.delete("/{record_id}", response_model=ResponseModel[dict])
async def delete_progress_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除进度记录"""
    try:
        record = db.query(ProgressRecord).filter(ProgressRecord.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="进度记录不存在"
            )
        
        # 删除关联的阶段记录
        db.query(StageRecord).filter(StageRecord.progress_id == record_id).delete()
        
        # 删除关联的质量记录
        db.query(QualityRecord).filter(QualityRecord.progress_id == record_id).delete()
        
        # 删除关联的进度更新记录
        db.query(ProgressUpdate).filter(ProgressUpdate.progress_id == record_id).delete()
        
        # 删除进度记录
        db.delete(record)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除进度记录成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除进度记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除进度记录服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[ProgressStats])
async def get_progress_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取进度统计信息"""
    try:
        # 总记录数
        total_records = db.query(ProgressRecord).count()
        
        # 各状态记录数
        not_started_records = db.query(ProgressRecord).filter(ProgressRecord.status == ProgressStatus.NOT_STARTED).count()
        in_progress_records = db.query(ProgressRecord).filter(ProgressRecord.status == ProgressStatus.IN_PROGRESS).count()
        completed_records = db.query(ProgressRecord).filter(ProgressRecord.status == ProgressStatus.COMPLETED).count()
        paused_records = db.query(ProgressRecord).filter(ProgressRecord.status == ProgressStatus.PAUSED).count()
        cancelled_records = db.query(ProgressRecord).filter(ProgressRecord.status == ProgressStatus.CANCELLED).count()
        
        # 逾期记录（结束日期已过但未完成）
        today = datetime.now().date()
        overdue_records = db.query(ProgressRecord).filter(
            and_(
                ProgressRecord.end_date < today,
                ProgressRecord.status.in_([ProgressStatus.NOT_STARTED, ProgressStatus.IN_PROGRESS])
            )
        ).count()
        
        # 平均进度
        avg_progress_result = db.query(db.func.avg(ProgressRecord.progress)).filter(
            ProgressRecord.status.in_([ProgressStatus.IN_PROGRESS, ProgressStatus.COMPLETED])
        ).scalar()
        avg_progress = float(avg_progress_result) if avg_progress_result else 0.0
        
        # 本月新增记录
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_new_records = db.query(ProgressRecord).filter(ProgressRecord.created_at >= current_month_start).count()
        
        # 本月完成记录
        monthly_completed_records = db.query(ProgressRecord).filter(
            and_(
                ProgressRecord.status == ProgressStatus.COMPLETED,
                ProgressRecord.updated_at >= current_month_start
            )
        ).count()
        
        # 质量检查统计
        total_quality_checks = db.query(QualityRecord).count()
        passed_quality_checks = db.query(QualityRecord).filter(QualityRecord.check_result == QualityResult.PASS).count()
        failed_quality_checks = db.query(QualityRecord).filter(QualityRecord.check_result == QualityResult.FAIL).count()
        
        progress_stats = ProgressStats(
            total_records=total_records,
            not_started_records=not_started_records,
            in_progress_records=in_progress_records,
            completed_records=completed_records,
            paused_records=paused_records,
            cancelled_records=cancelled_records,
            overdue_records=overdue_records,
            avg_progress=avg_progress,
            monthly_new_records=monthly_new_records,
            monthly_completed_records=monthly_completed_records,
            total_quality_checks=total_quality_checks,
            passed_quality_checks=passed_quality_checks,
            failed_quality_checks=failed_quality_checks
        )
        
        return ResponseModel(
            code=200,
            message="获取进度统计成功",
            data=progress_stats
        )
        
    except Exception as e:
        logger.error(f"获取进度统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取进度统计服务异常"
        )

@router.post("/{record_id}/quality", response_model=ResponseModel[QualityRecordDetail])
async def create_quality_record(
    record_id: int,
    quality_data: QualityRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建质量检查记录"""
    try:
        # 检查进度记录是否存在
        progress_record = db.query(ProgressRecord).filter(ProgressRecord.id == record_id).first()
        if not progress_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="进度记录不存在"
            )
        
        # 创建质量记录
        quality_record = QualityRecord(
            progress_id=record_id,
            checkpoint_name=quality_data.checkpoint_name,
            check_date=quality_data.check_date,
            checker=quality_data.checker,
            check_result=quality_data.check_result,
            check_details=quality_data.check_details,
            defect_quantity=quality_data.defect_quantity,
            rework_quantity=quality_data.rework_quantity,
            scrap_quantity=quality_data.scrap_quantity,
            remark=quality_data.remark,
            created_by=current_user.username
        )
        
        db.add(quality_record)
        db.commit()
        db.refresh(quality_record)
        
        quality_detail = QualityRecordDetail(
            id=quality_record.id,
            progress_id=quality_record.progress_id,
            checkpoint_name=quality_record.checkpoint_name,
            check_date=quality_record.check_date,
            checker=quality_record.checker,
            check_result=quality_record.check_result,
            check_details=quality_record.check_details,
            defect_quantity=quality_record.defect_quantity,
            rework_quantity=quality_record.rework_quantity,
            scrap_quantity=quality_record.scrap_quantity,
            remark=quality_record.remark,
            created_at=quality_record.created_at
        )
        
        return ResponseModel(
            code=200,
            message="创建质量检查记录成功",
            data=quality_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建质量检查记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建质量检查记录服务异常"
        )

@router.post("/{record_id}/update", response_model=ResponseModel[ProgressUpdateDetail])
async def create_progress_update(
    record_id: int,
    update_data: ProgressUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建进度更新记录"""
    try:
        # 检查进度记录是否存在
        progress_record = db.query(ProgressRecord).filter(ProgressRecord.id == record_id).first()
        if not progress_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="进度记录不存在"
            )
        
        # 创建进度更新记录
        progress_update = ProgressUpdate(
            progress_id=record_id,
            update_date=update_data.update_date,
            previous_progress=progress_record.progress,
            current_progress=update_data.current_progress,
            update_content=update_data.update_content,
            achievements=update_data.achievements,
            issues=update_data.issues,
            next_steps=update_data.next_steps,
            attachments=update_data.attachments,
            updater=current_user.username
        )
        
        db.add(progress_update)
        
        # 更新进度记录的进度
        progress_record.progress = update_data.current_progress
        progress_record.updated_by = current_user.username
        progress_record.updated_at = datetime.now()
        
        db.commit()
        db.refresh(progress_update)
        
        update_detail = ProgressUpdateDetail(
            id=progress_update.id,
            progress_id=progress_update.progress_id,
            update_date=progress_update.update_date,
            previous_progress=progress_update.previous_progress,
            current_progress=progress_update.current_progress,
            update_content=progress_update.update_content,
            achievements=progress_update.achievements,
            issues=progress_update.issues,
            next_steps=progress_update.next_steps,
            attachments=progress_update.attachments,
            updater=progress_update.updater,
            created_at=progress_update.created_at
        )
        
        return ResponseModel(
            code=200,
            message="创建进度更新记录成功",
            data=update_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建进度更新记录异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建进度更新记录服务异常"
        )