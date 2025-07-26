from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from app.db.database import get_db
from app.models.quality import QualityCheck, QualityStandard, QualityIssue, QualityCheckStatus, QualityResult, IssueStatus, IssueSeverity
from app.models.user import User
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.quality import (
    QualityCheckCreate, QualityCheckUpdate, QualityCheckQuery, QualityCheckDetail,
    QualityStandardCreate, QualityStandardUpdate, QualityStandardDetail,
    QualityIssueCreate, QualityIssueUpdate, QualityIssueDetail,
    QualityStats, QualityCheckSummary, QualityCheckStatusUpdate
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/checks", response_model=PagedResponseModel[QualityCheckDetail])
async def get_quality_checks(
    query: QualityCheckQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取质量检查列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    QualityCheck.check_number.contains(query.keyword),
                    QualityCheck.product_name.contains(query.keyword),
                    QualityCheck.batch_number.contains(query.keyword),
                    QualityCheck.inspector.contains(query.keyword)
                )
            )
        
        if query.status:
            filters.append(QualityCheck.status == query.status)
        
        if query.result:
            filters.append(QualityCheck.result == query.result)
        
        if query.product_name:
            filters.append(QualityCheck.product_name.contains(query.product_name))
        
        if query.batch_number:
            filters.append(QualityCheck.batch_number.contains(query.batch_number))
        
        if query.inspector:
            filters.append(QualityCheck.inspector.contains(query.inspector))
        
        if query.order_id:
            filters.append(QualityCheck.order_id == query.order_id)
        
        if query.production_plan_id:
            filters.append(QualityCheck.production_plan_id == query.production_plan_id)
        
        if query.check_date_start:
            filters.append(QualityCheck.check_date >= query.check_date_start)
        
        if query.check_date_end:
            filters.append(QualityCheck.check_date <= query.check_date_end)
        
        if query.has_issues is not None:
            if query.has_issues:
                filters.append(QualityCheck.issues_found > 0)
            else:
                filters.append(QualityCheck.issues_found == 0)
        
        # 构建基础查询
        base_query = db.query(QualityCheck)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(QualityCheck, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(QualityCheck.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        checks = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        check_details = []
        for check in checks:
            # 获取关联的质量问题
            issues = db.query(QualityIssue).filter(QualityIssue.quality_check_id == check.id).all()
            
            # 计算检查状态指标
            pass_rate = (check.pass_quantity / check.check_quantity * 100) if check.check_quantity > 0 else 0
            
            check_detail = QualityCheckDetail(
                id=check.id,
                check_number=check.check_number,
                product_name=check.product_name,
                batch_number=check.batch_number,
                order_id=check.order_id,
                production_plan_id=check.production_plan_id,
                check_date=check.check_date,
                inspector=check.inspector,
                check_quantity=check.check_quantity,
                pass_quantity=check.pass_quantity,
                fail_quantity=check.fail_quantity,
                defect_quantity=check.defect_quantity,
                pass_rate=round(pass_rate, 2),
                status=check.status,
                result=check.result,
                check_items=check.check_items,
                check_standards=check.check_standards,
                issues_found=check.issues_found,
                corrective_actions=check.corrective_actions,
                remark=check.remark,
                issues=[QualityIssueDetail(
                    id=issue.id,
                    issue_number=issue.issue_number,
                    issue_type=issue.issue_type,
                    severity=issue.severity,
                    description=issue.description,
                    status=issue.status,
                    created_at=issue.created_at
                ) for issue in issues],
                created_at=check.created_at,
                updated_at=check.updated_at,
                created_by=check.created_by,
                updated_by=check.updated_by
            )
            check_details.append(check_detail)
        
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
            message="获取质量检查列表成功",
            data=check_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取质量检查列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取质量检查列表服务异常"
        )

@router.get("/checks/{check_id}", response_model=ResponseModel[QualityCheckDetail])
async def get_quality_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取质量检查详情"""
    try:
        check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()
        if not check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="质量检查记录不存在"
            )
        
        # 获取关联的质量问题
        issues = db.query(QualityIssue).filter(QualityIssue.quality_check_id == check_id).all()
        
        issue_details = []
        for issue in issues:
            issue_detail = QualityIssueDetail(
                id=issue.id,
                quality_check_id=issue.quality_check_id,
                issue_number=issue.issue_number,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                root_cause=issue.root_cause,
                corrective_action=issue.corrective_action,
                preventive_action=issue.preventive_action,
                responsible_person=issue.responsible_person,
                due_date=issue.due_date,
                completion_date=issue.completion_date,
                status=issue.status,
                verification_result=issue.verification_result,
                remark=issue.remark,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                created_by=issue.created_by,
                updated_by=issue.updated_by
            )
            issue_details.append(issue_detail)
        
        # 计算检查状态指标
        pass_rate = (check.pass_quantity / check.check_quantity * 100) if check.check_quantity > 0 else 0
        
        check_detail = QualityCheckDetail(
            id=check.id,
            check_number=check.check_number,
            product_name=check.product_name,
            batch_number=check.batch_number,
            order_id=check.order_id,
            production_plan_id=check.production_plan_id,
            check_date=check.check_date,
            inspector=check.inspector,
            check_quantity=check.check_quantity,
            pass_quantity=check.pass_quantity,
            fail_quantity=check.fail_quantity,
            defect_quantity=check.defect_quantity,
            pass_rate=round(pass_rate, 2),
            status=check.status,
            result=check.result,
            check_items=check.check_items,
            check_standards=check.check_standards,
            issues_found=check.issues_found,
            corrective_actions=check.corrective_actions,
            remark=check.remark,
            issues=issue_details,
            created_at=check.created_at,
            updated_at=check.updated_at,
            created_by=check.created_by,
            updated_by=check.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="获取质量检查详情成功",
            data=check_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取质量检查详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取质量检查详情服务异常"
        )

@router.post("/checks", response_model=ResponseModel[QualityCheckDetail])
async def create_quality_check(
    check_data: QualityCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager", "quality"]))
):
    """创建质量检查"""
    try:
        # 检查检查编号是否已存在
        existing_check = db.query(QualityCheck).filter(QualityCheck.check_number == check_data.check_number).first()
        if existing_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="检查编号已存在"
            )
        
        # 创建质量检查
        quality_check = QualityCheck(
            check_number=check_data.check_number,
            product_name=check_data.product_name,
            batch_number=check_data.batch_number,
            order_id=check_data.order_id,
            production_plan_id=check_data.production_plan_id,
            check_date=check_data.check_date,
            inspector=check_data.inspector,
            check_quantity=check_data.check_quantity,
            pass_quantity=check_data.pass_quantity or 0,
            fail_quantity=check_data.fail_quantity or 0,
            defect_quantity=check_data.defect_quantity or 0,
            status=check_data.status or QualityCheckStatus.PENDING,
            result=check_data.result,
            check_items=check_data.check_items,
            check_standards=check_data.check_standards,
            issues_found=check_data.issues_found or 0,
            corrective_actions=check_data.corrective_actions,
            remark=check_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(quality_check)
        db.commit()
        db.refresh(quality_check)
        
        # 创建关联的质量问题
        if check_data.issues:
            for issue_data in check_data.issues:
                quality_issue = QualityIssue(
                    quality_check_id=quality_check.id,
                    issue_number=issue_data.issue_number,
                    issue_type=issue_data.issue_type,
                    severity=issue_data.severity,
                    description=issue_data.description,
                    root_cause=issue_data.root_cause,
                    corrective_action=issue_data.corrective_action,
                    preventive_action=issue_data.preventive_action,
                    responsible_person=issue_data.responsible_person,
                    due_date=issue_data.due_date,
                    status=issue_data.status or IssueStatus.OPEN,
                    remark=issue_data.remark,
                    created_by=current_user.username,
                    updated_by=current_user.username
                )
                db.add(quality_issue)
            
            # 更新问题数量
            quality_check.issues_found = len(check_data.issues)
            db.commit()
        
        # 计算通过率
        pass_rate = (quality_check.pass_quantity / quality_check.check_quantity * 100) if quality_check.check_quantity > 0 else 0
        
        check_detail = QualityCheckDetail(
            id=quality_check.id,
            check_number=quality_check.check_number,
            product_name=quality_check.product_name,
            batch_number=quality_check.batch_number,
            order_id=quality_check.order_id,
            production_plan_id=quality_check.production_plan_id,
            check_date=quality_check.check_date,
            inspector=quality_check.inspector,
            check_quantity=quality_check.check_quantity,
            pass_quantity=quality_check.pass_quantity,
            fail_quantity=quality_check.fail_quantity,
            defect_quantity=quality_check.defect_quantity,
            pass_rate=round(pass_rate, 2),
            status=quality_check.status,
            result=quality_check.result,
            check_items=quality_check.check_items,
            check_standards=quality_check.check_standards,
            issues_found=quality_check.issues_found,
            corrective_actions=quality_check.corrective_actions,
            remark=quality_check.remark,
            created_at=quality_check.created_at,
            created_by=quality_check.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建质量检查成功",
            data=check_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建质量检查异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建质量检查服务异常"
        )

@router.put("/checks/{check_id}", response_model=ResponseModel[QualityCheckDetail])
async def update_quality_check(
    check_id: int,
    check_data: QualityCheckUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager", "quality"]))
):
    """更新质量检查"""
    try:
        quality_check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()
        if not quality_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="质量检查记录不存在"
            )
        
        # 检查检查编号是否已被其他记录使用
        if check_data.check_number and check_data.check_number != quality_check.check_number:
            existing_check = db.query(QualityCheck).filter(
                and_(
                    QualityCheck.check_number == check_data.check_number,
                    QualityCheck.id != check_id
                )
            ).first()
            if existing_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="检查编号已存在"
                )
        
        # 更新字段
        update_data = check_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quality_check, field, value)
        
        quality_check.updated_by = current_user.username
        quality_check.updated_at = datetime.now()
        
        db.commit()
        db.refresh(quality_check)
        
        # 计算通过率
        pass_rate = (quality_check.pass_quantity / quality_check.check_quantity * 100) if quality_check.check_quantity > 0 else 0
        
        check_detail = QualityCheckDetail(
            id=quality_check.id,
            check_number=quality_check.check_number,
            product_name=quality_check.product_name,
            batch_number=quality_check.batch_number,
            order_id=quality_check.order_id,
            production_plan_id=quality_check.production_plan_id,
            check_date=quality_check.check_date,
            inspector=quality_check.inspector,
            check_quantity=quality_check.check_quantity,
            pass_quantity=quality_check.pass_quantity,
            fail_quantity=quality_check.fail_quantity,
            defect_quantity=quality_check.defect_quantity,
            pass_rate=round(pass_rate, 2),
            status=quality_check.status,
            result=quality_check.result,
            check_items=quality_check.check_items,
            check_standards=quality_check.check_standards,
            issues_found=quality_check.issues_found,
            corrective_actions=quality_check.corrective_actions,
            remark=quality_check.remark,
            updated_at=quality_check.updated_at,
            updated_by=quality_check.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新质量检查成功",
            data=check_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新质量检查异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新质量检查服务异常"
        )

@router.delete("/checks/{check_id}", response_model=ResponseModel[dict])
async def delete_quality_check(
    check_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin"]))
):
    """删除质量检查"""
    try:
        quality_check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()
        if not quality_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="质量检查记录不存在"
            )
        
        # 删除关联的质量问题
        db.query(QualityIssue).filter(QualityIssue.quality_check_id == check_id).delete()
        
        # 删除质量检查
        db.delete(quality_check)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除质量检查成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除质量检查异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除质量检查服务异常"
        )

@router.get("/stats/overview", response_model=ResponseModel[QualityStats])
async def get_quality_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取质量统计信息"""
    try:
        # 总检查数
        total_checks = db.query(QualityCheck).count()
        
        # 各状态检查数
        pending_checks = db.query(QualityCheck).filter(QualityCheck.status == QualityCheckStatus.PENDING).count()
        in_progress_checks = db.query(QualityCheck).filter(QualityCheck.status == QualityCheckStatus.IN_PROGRESS).count()
        completed_checks = db.query(QualityCheck).filter(QualityCheck.status == QualityCheckStatus.COMPLETED).count()
        
        # 各结果检查数
        pass_checks = db.query(QualityCheck).filter(QualityCheck.result == QualityResult.PASS).count()
        fail_checks = db.query(QualityCheck).filter(QualityCheck.result == QualityResult.FAIL).count()
        rework_checks = db.query(QualityCheck).filter(QualityCheck.result == QualityResult.REWORK).count()
        
        # 总问题数
        total_issues = db.query(QualityIssue).count()
        
        # 各状态问题数
        open_issues = db.query(QualityIssue).filter(QualityIssue.status == IssueStatus.OPEN).count()
        in_progress_issues = db.query(QualityIssue).filter(QualityIssue.status == IssueStatus.IN_PROGRESS).count()
        resolved_issues = db.query(QualityIssue).filter(QualityIssue.status == IssueStatus.RESOLVED).count()
        closed_issues = db.query(QualityIssue).filter(QualityIssue.status == IssueStatus.CLOSED).count()
        
        # 各严重程度问题数
        critical_issues = db.query(QualityIssue).filter(QualityIssue.severity == IssueSeverity.CRITICAL).count()
        high_issues = db.query(QualityIssue).filter(QualityIssue.severity == IssueSeverity.HIGH).count()
        medium_issues = db.query(QualityIssue).filter(QualityIssue.severity == IssueSeverity.MEDIUM).count()
        low_issues = db.query(QualityIssue).filter(QualityIssue.severity == IssueSeverity.LOW).count()
        
        # 总检查数量和通过数量
        total_check_quantity = db.query(db.func.sum(QualityCheck.check_quantity)).scalar() or 0
        total_pass_quantity = db.query(db.func.sum(QualityCheck.pass_quantity)).scalar() or 0
        
        # 整体通过率
        overall_pass_rate = (total_pass_quantity / total_check_quantity * 100) if total_check_quantity > 0 else 0
        
        # 本月数据
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_checks = db.query(QualityCheck).filter(QualityCheck.created_at >= current_month_start).count()
        monthly_issues = db.query(QualityIssue).filter(QualityIssue.created_at >= current_month_start).count()
        
        # 本月检查数量和通过数量
        monthly_check_quantity = db.query(db.func.sum(QualityCheck.check_quantity)).filter(
            QualityCheck.created_at >= current_month_start
        ).scalar() or 0
        monthly_pass_quantity = db.query(db.func.sum(QualityCheck.pass_quantity)).filter(
            QualityCheck.created_at >= current_month_start
        ).scalar() or 0
        
        # 本月通过率
        monthly_pass_rate = (monthly_pass_quantity / monthly_check_quantity * 100) if monthly_check_quantity > 0 else 0
        
        # 逾期问题数（超过截止日期且未关闭）
        overdue_issues = db.query(QualityIssue).filter(
            and_(
                QualityIssue.due_date < datetime.now().date(),
                QualityIssue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        ).count()
        
        quality_stats = QualityStats(
            total_checks=total_checks,
            pending_checks=pending_checks,
            in_progress_checks=in_progress_checks,
            completed_checks=completed_checks,
            pass_checks=pass_checks,
            fail_checks=fail_checks,
            rework_checks=rework_checks,
            total_issues=total_issues,
            open_issues=open_issues,
            in_progress_issues=in_progress_issues,
            resolved_issues=resolved_issues,
            closed_issues=closed_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            overall_pass_rate=round(overall_pass_rate, 2),
            monthly_checks=monthly_checks,
            monthly_issues=monthly_issues,
            monthly_pass_rate=round(monthly_pass_rate, 2),
            overdue_issues=overdue_issues
        )
        
        return ResponseModel(
            code=200,
            message="获取质量统计成功",
            data=quality_stats
        )
        
    except Exception as e:
        logger.error(f"获取质量统计异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取质量统计服务异常"
        )

@router.post("/checks/{check_id}/issues", response_model=ResponseModel[QualityIssueDetail])
async def create_quality_issue(
    check_id: int,
    issue_data: QualityIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager", "quality"]))
):
    """创建质量问题"""
    try:
        # 检查质量检查是否存在
        quality_check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()
        if not quality_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="质量检查记录不存在"
            )
        
        # 检查问题编号是否已存在
        existing_issue = db.query(QualityIssue).filter(QualityIssue.issue_number == issue_data.issue_number).first()
        if existing_issue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="问题编号已存在"
            )
        
        # 创建质量问题
        quality_issue = QualityIssue(
            quality_check_id=check_id,
            issue_number=issue_data.issue_number,
            issue_type=issue_data.issue_type,
            severity=issue_data.severity,
            description=issue_data.description,
            root_cause=issue_data.root_cause,
            corrective_action=issue_data.corrective_action,
            preventive_action=issue_data.preventive_action,
            responsible_person=issue_data.responsible_person,
            due_date=issue_data.due_date,
            status=issue_data.status or IssueStatus.OPEN,
            remark=issue_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(quality_issue)
        
        # 更新质量检查的问题数量
        quality_check.issues_found = db.query(QualityIssue).filter(QualityIssue.quality_check_id == check_id).count() + 1
        quality_check.updated_by = current_user.username
        quality_check.updated_at = datetime.now()
        
        db.commit()
        db.refresh(quality_issue)
        
        issue_detail = QualityIssueDetail(
            id=quality_issue.id,
            quality_check_id=quality_issue.quality_check_id,
            issue_number=quality_issue.issue_number,
            issue_type=quality_issue.issue_type,
            severity=quality_issue.severity,
            description=quality_issue.description,
            root_cause=quality_issue.root_cause,
            corrective_action=quality_issue.corrective_action,
            preventive_action=quality_issue.preventive_action,
            responsible_person=quality_issue.responsible_person,
            due_date=quality_issue.due_date,
            status=quality_issue.status,
            remark=quality_issue.remark,
            created_at=quality_issue.created_at,
            created_by=quality_issue.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建质量问题成功",
            data=issue_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建质量问题异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建质量问题服务异常"
        )

@router.put("/checks/{check_id}/status", response_model=ResponseModel[QualityCheckDetail])
async def update_quality_check_status(
    check_id: int,
    status_data: QualityCheckStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["admin", "manager", "quality"]))
):
    """更新质量检查状态"""
    try:
        quality_check = db.query(QualityCheck).filter(QualityCheck.id == check_id).first()
        if not quality_check:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="质量检查记录不存在"
            )
        
        # 更新状态
        quality_check.status = status_data.status
        if status_data.result:
            quality_check.result = status_data.result
        if status_data.remark:
            quality_check.remark = status_data.remark
        
        quality_check.updated_by = current_user.username
        quality_check.updated_at = datetime.now()
        
        db.commit()
        db.refresh(quality_check)
        
        # 计算通过率
        pass_rate = (quality_check.pass_quantity / quality_check.check_quantity * 100) if quality_check.check_quantity > 0 else 0
        
        check_detail = QualityCheckDetail(
            id=quality_check.id,
            check_number=quality_check.check_number,
            product_name=quality_check.product_name,
            status=quality_check.status,
            result=quality_check.result,
            pass_rate=round(pass_rate, 2),
            remark=quality_check.remark,
            updated_at=quality_check.updated_at,
            updated_by=quality_check.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新质量检查状态成功",
            data=check_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新质量检查状态异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新质量检查状态服务异常"
        )

@router.get("/issues/overdue", response_model=ResponseModel[List[QualityIssueDetail]])
async def get_overdue_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取逾期质量问题"""
    try:
        overdue_issues = db.query(QualityIssue).filter(
            and_(
                QualityIssue.due_date < datetime.now().date(),
                QualityIssue.status.in_([IssueStatus.OPEN, IssueStatus.IN_PROGRESS])
            )
        ).order_by(QualityIssue.due_date.asc()).all()
        
        issue_details = []
        for issue in overdue_issues:
            issue_detail = QualityIssueDetail(
                id=issue.id,
                quality_check_id=issue.quality_check_id,
                issue_number=issue.issue_number,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                responsible_person=issue.responsible_person,
                due_date=issue.due_date,
                status=issue.status,
                created_at=issue.created_at
            )
            issue_details.append(issue_detail)
        
        return ResponseModel(
            code=200,
            message="获取逾期质量问题成功",
            data=issue_details
        )
        
    except Exception as e:
        logger.error(f"获取逾期质量问题异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取逾期质量问题服务异常"
        )