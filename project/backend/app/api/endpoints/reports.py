"""报表生成API接口

提供各类报表生成的REST API接口：
- 生产报表
- 质量报表
- 设备状态报表
- 订单分析报表
- 进度跟踪报表
- 物料库存报表
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
import logging
import os
import tempfile

from ...db.database import get_db
from ...models.user import User
from ...models.production_plan import ProductionPlan, PlanStatus
from ...models.order import Order, OrderStatus
from ...models.quality import QualityCheck, QualityResult
from ...models.equipment import Equipment, MaintenanceRecord, EquipmentStatus
from ...models.material import Material, MaterialStatus
from ...models.progress import ProgressRecord, ProgressStatus
from ...schemas.common import ResponseModel
from ...core.auth import get_current_user
from ...utils.report_export import report_exporter

logger = logging.getLogger(__name__)

router = APIRouter()

# 报表请求模型
class ReportRequest(BaseModel):
    """报表请求基础模型"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    format: str = Field(default="json", description="报表格式: json, excel, pdf")
    
class ProductionReportRequest(ReportRequest):
    """生产报表请求"""
    workshop: Optional[str] = Field(None, description="车间筛选")
    production_line: Optional[str] = Field(None, description="生产线筛选")
    status: Optional[List[PlanStatus]] = Field(None, description="状态筛选")
    
class QualityReportRequest(ReportRequest):
    """质量报表请求"""
    product_name: Optional[str] = Field(None, description="产品名称筛选")
    quality_result: Optional[List[QualityResult]] = Field(None, description="质量结果筛选")
    
class EquipmentReportRequest(ReportRequest):
    """设备报表请求"""
    equipment_type: Optional[str] = Field(None, description="设备类型筛选")
    status: Optional[List[EquipmentStatus]] = Field(None, description="设备状态筛选")
    workshop: Optional[str] = Field(None, description="车间筛选")

# 报表响应模型
class ProductionReportData(BaseModel):
    """生产报表数据"""
    total_plans: int = Field(..., description="总计划数")
    completed_plans: int = Field(..., description="已完成计划数")
    in_progress_plans: int = Field(..., description="进行中计划数")
    overdue_plans: int = Field(..., description="逾期计划数")
    completion_rate: float = Field(..., description="完成率")
    avg_progress: float = Field(..., description="平均进度")
    workshop_stats: List[Dict[str, Any]] = Field(..., description="车间统计")
    daily_production: List[Dict[str, Any]] = Field(..., description="日产量统计")
    efficiency_analysis: Dict[str, Any] = Field(..., description="效率分析")
    
class QualityReportData(BaseModel):
    """质量报表数据"""
    total_checks: int = Field(..., description="总检查次数")
    passed_checks: int = Field(..., description="通过检查次数")
    failed_checks: int = Field(..., description="未通过检查次数")
    pass_rate: float = Field(..., description="合格率")
    defect_rate: float = Field(..., description="缺陷率")
    quality_trends: List[Dict[str, Any]] = Field(..., description="质量趋势")
    defect_analysis: List[Dict[str, Any]] = Field(..., description="缺陷分析")
    product_quality: List[Dict[str, Any]] = Field(..., description="产品质量统计")
    
class EquipmentReportData(BaseModel):
    """设备报表数据"""
    total_equipment: int = Field(..., description="设备总数")
    running_equipment: int = Field(..., description="运行中设备数")
    maintenance_equipment: int = Field(..., description="维护中设备数")
    fault_equipment: int = Field(..., description="故障设备数")
    utilization_rate: float = Field(..., description="设备利用率")
    maintenance_stats: List[Dict[str, Any]] = Field(..., description="维护统计")
    fault_analysis: List[Dict[str, Any]] = Field(..., description="故障分析")
    efficiency_trends: List[Dict[str, Any]] = Field(..., description="效率趋势")

@router.post("/production", response_model=ResponseModel[ProductionReportData])
async def generate_production_report(
    request: ProductionReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成生产报表"""
    try:
        # 构建查询条件
        filters = [
            ProductionPlan.planned_start_date >= request.start_date,
            ProductionPlan.planned_start_date <= request.end_date
        ]
        
        if request.workshop:
            filters.append(ProductionPlan.workshop.contains(request.workshop))
        if request.production_line:
            filters.append(ProductionPlan.production_line.contains(request.production_line))
        if request.status:
            filters.append(ProductionPlan.status.in_(request.status))
            
        # 基础统计
        base_query = db.query(ProductionPlan).filter(and_(*filters))
        total_plans = base_query.count()
        completed_plans = base_query.filter(ProductionPlan.status == PlanStatus.COMPLETED).count()
        in_progress_plans = base_query.filter(ProductionPlan.status == PlanStatus.IN_PROGRESS).count()
        
        # 逾期计划
        today = datetime.now().date()
        overdue_plans = base_query.filter(
            and_(
                ProductionPlan.planned_end_date < today,
                ProductionPlan.status.in_([PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS])
            )
        ).count()
        
        # 完成率和平均进度
        completion_rate = (completed_plans / total_plans * 100) if total_plans > 0 else 0
        avg_progress_result = base_query.with_entities(func.avg(ProductionPlan.progress)).scalar()
        avg_progress = float(avg_progress_result) if avg_progress_result else 0
        
        # 车间统计
        workshop_stats = []
        workshop_query = base_query.with_entities(
            ProductionPlan.workshop,
            func.count(ProductionPlan.id).label('count'),
            func.avg(ProductionPlan.progress).label('avg_progress')
        ).group_by(ProductionPlan.workshop).all()
        
        for workshop, count, progress in workshop_query:
            workshop_stats.append({
                'workshop': workshop,
                'total_plans': count,
                'avg_progress': float(progress) if progress else 0
            })
        
        # 日产量统计
        daily_production = []
        current_date = request.start_date
        while current_date <= request.end_date:
            daily_count = base_query.filter(
                func.date(ProductionPlan.planned_start_date) == current_date
            ).count()
            daily_production.append({
                'date': current_date.isoformat(),
                'count': daily_count
            })
            current_date += timedelta(days=1)
        
        # 效率分析
        efficiency_analysis = {
            'on_time_completion_rate': completion_rate,
            'average_delay_days': 0,  # 需要根据实际完成时间计算
            'resource_utilization': avg_progress
        }
        
        report_data = ProductionReportData(
            total_plans=total_plans,
            completed_plans=completed_plans,
            in_progress_plans=in_progress_plans,
            overdue_plans=overdue_plans,
            completion_rate=completion_rate,
            avg_progress=avg_progress,
            workshop_stats=workshop_stats,
            daily_production=daily_production,
            efficiency_analysis=efficiency_analysis
        )
        
        return ResponseModel(
            code=200,
            message="生产报表生成成功",
            data=report_data
        )
        
    except Exception as e:
        logger.error(f"生成生产报表异常: {e}")
        raise HTTPException(status_code=500, detail="生成生产报表失败")

@router.post("/quality", response_model=ResponseModel[QualityReportData])
async def generate_quality_report(
    request: QualityReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成质量报表"""
    try:
        # 构建查询条件
        filters = [
            QualityCheck.check_date >= request.start_date,
            QualityCheck.check_date <= request.end_date
        ]
        
        if request.product_name:
            filters.append(QualityCheck.product_name.contains(request.product_name))
        if request.quality_result:
            filters.append(QualityCheck.result.in_(request.quality_result))
            
        # 基础统计
        base_query = db.query(QualityCheck).filter(and_(*filters))
        total_checks = base_query.count()
        passed_checks = base_query.filter(QualityCheck.result == QualityResult.PASSED).count()
        failed_checks = base_query.filter(QualityCheck.result == QualityResult.FAILED).count()
        
        # 合格率和缺陷率
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        defect_rate = (failed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # 质量趋势
        quality_trends = []
        current_date = request.start_date
        while current_date <= request.end_date:
            daily_checks = base_query.filter(
                func.date(QualityCheck.check_date) == current_date
            )
            daily_total = daily_checks.count()
            daily_passed = daily_checks.filter(QualityCheck.result == QualityResult.PASSED).count()
            daily_rate = (daily_passed / daily_total * 100) if daily_total > 0 else 0
            
            quality_trends.append({
                'date': current_date.isoformat(),
                'total_checks': daily_total,
                'pass_rate': daily_rate
            })
            current_date += timedelta(days=1)
        
        # 缺陷分析
        defect_analysis = []
        defect_query = base_query.filter(QualityCheck.result == QualityResult.FAILED).with_entities(
            QualityCheck.defect_type,
            func.count(QualityCheck.id).label('count')
        ).group_by(QualityCheck.defect_type).all()
        
        for defect_type, count in defect_query:
            defect_analysis.append({
                'defect_type': defect_type,
                'count': count,
                'percentage': (count / failed_checks * 100) if failed_checks > 0 else 0
            })
        
        # 产品质量统计
        product_quality = []
        product_query = base_query.with_entities(
            QualityCheck.product_name,
            func.count(QualityCheck.id).label('total'),
            func.sum(func.case([(QualityCheck.result == QualityResult.PASSED, 1)], else_=0)).label('passed')
        ).group_by(QualityCheck.product_name).all()
        
        for product_name, total, passed in product_query:
            product_quality.append({
                'product_name': product_name,
                'total_checks': total,
                'passed_checks': passed,
                'pass_rate': (passed / total * 100) if total > 0 else 0
            })
        
        report_data = QualityReportData(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            pass_rate=pass_rate,
            defect_rate=defect_rate,
            quality_trends=quality_trends,
            defect_analysis=defect_analysis,
            product_quality=product_quality
        )
        
        return ResponseModel(
            code=200,
            message="质量报表生成成功",
            data=report_data
        )
        
    except Exception as e:
        logger.error(f"生成质量报表异常: {e}")
        raise HTTPException(status_code=500, detail="生成质量报表失败")

@router.post("/equipment", response_model=ResponseModel[EquipmentReportData])
async def generate_equipment_report(
    request: EquipmentReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成设备状态报表"""
    try:
        # 构建查询条件
        filters = []
        
        if request.equipment_type:
            filters.append(Equipment.equipment_type.contains(request.equipment_type))
        if request.status:
            filters.append(Equipment.status.in_(request.status))
        if request.workshop:
            filters.append(Equipment.workshop.contains(request.workshop))
            
        # 基础统计
        base_query = db.query(Equipment)
        if filters:
            base_query = base_query.filter(and_(*filters))
            
        total_equipment = base_query.count()
        running_equipment = base_query.filter(Equipment.status == EquipmentStatus.RUNNING).count()
        maintenance_equipment = base_query.filter(Equipment.status == EquipmentStatus.MAINTENANCE).count()
        fault_equipment = base_query.filter(Equipment.status == EquipmentStatus.FAULT).count()
        
        # 设备利用率
        utilization_rate = (running_equipment / total_equipment * 100) if total_equipment > 0 else 0
        
        # 维护统计
        maintenance_stats = []
        maintenance_query = db.query(MaintenanceRecord).filter(
            and_(
                MaintenanceRecord.maintenance_date >= request.start_date,
                MaintenanceRecord.maintenance_date <= request.end_date
            )
        ).with_entities(
            MaintenanceRecord.maintenance_type,
            func.count(MaintenanceRecord.id).label('count'),
            func.avg(MaintenanceRecord.cost).label('avg_cost')
        ).group_by(MaintenanceRecord.maintenance_type).all()
        
        for maintenance_type, count, avg_cost in maintenance_query:
            maintenance_stats.append({
                'maintenance_type': maintenance_type,
                'count': count,
                'avg_cost': float(avg_cost) if avg_cost else 0
            })
        
        # 故障分析
        fault_analysis = []
        fault_query = base_query.filter(Equipment.status == EquipmentStatus.FAULT).with_entities(
            Equipment.equipment_type,
            func.count(Equipment.id).label('count')
        ).group_by(Equipment.equipment_type).all()
        
        for equipment_type, count in fault_query:
            fault_analysis.append({
                'equipment_type': equipment_type,
                'fault_count': count,
                'fault_rate': (count / total_equipment * 100) if total_equipment > 0 else 0
            })
        
        # 效率趋势（简化版）
        efficiency_trends = []
        current_date = request.start_date
        while current_date <= request.end_date:
            # 这里可以根据实际需求计算每日设备效率
            efficiency_trends.append({
                'date': current_date.isoformat(),
                'utilization_rate': utilization_rate,  # 简化处理
                'maintenance_count': 0  # 需要根据实际维护记录计算
            })
            current_date += timedelta(days=1)
        
        report_data = EquipmentReportData(
            total_equipment=total_equipment,
            running_equipment=running_equipment,
            maintenance_equipment=maintenance_equipment,
            fault_equipment=fault_equipment,
            utilization_rate=utilization_rate,
            maintenance_stats=maintenance_stats,
            fault_analysis=fault_analysis,
            efficiency_trends=efficiency_trends
        )
        
        return ResponseModel(
            code=200,
            message="设备报表生成成功",
            data=report_data
        )
        
    except Exception as e:
        logger.error(f"生成设备报表异常: {e}")
        raise HTTPException(status_code=500, detail="生成设备报表失败")

@router.get("/dashboard", response_model=ResponseModel[Dict[str, Any]])
async def get_reports_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取报表仪表板数据"""
    try:
        # 获取最近30天的数据
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # 生产概览
        production_overview = {
            'total_plans': db.query(ProductionPlan).count(),
            'completed_plans': db.query(ProductionPlan).filter(
                ProductionPlan.status == PlanStatus.COMPLETED
            ).count(),
            'in_progress_plans': db.query(ProductionPlan).filter(
                ProductionPlan.status == PlanStatus.IN_PROGRESS
            ).count()
        }
        
        # 质量概览
        quality_overview = {
            'total_checks': db.query(QualityCheck).count(),
            'passed_checks': db.query(QualityCheck).filter(
                QualityCheck.result == QualityResult.PASSED
            ).count(),
            'failed_checks': db.query(QualityCheck).filter(
                QualityCheck.result == QualityResult.FAILED
            ).count()
        }
        
        # 设备概览
        equipment_overview = {
            'total_equipment': db.query(Equipment).count(),
            'running_equipment': db.query(Equipment).filter(
                Equipment.status == EquipmentStatus.RUNNING
            ).count(),
            'fault_equipment': db.query(Equipment).filter(
                Equipment.status == EquipmentStatus.FAULT
            ).count()
        }
        
        # 订单概览
        order_overview = {
            'total_orders': db.query(Order).count(),
            'pending_orders': db.query(Order).filter(
                Order.status == OrderStatus.PENDING
            ).count(),
            'completed_orders': db.query(Order).filter(
                Order.status == OrderStatus.COMPLETED
            ).count()
        }
        
        dashboard_data = {
            'production_overview': production_overview,
            'quality_overview': quality_overview,
            'equipment_overview': equipment_overview,
            'order_overview': order_overview,
            'last_updated': datetime.now().isoformat()
        }
        
        return ResponseModel(
            code=200,
            message="获取报表仪表板数据成功",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"获取报表仪表板数据异常: {e}")
        raise HTTPException(status_code=500, detail="获取报表仪表板数据失败")

@router.get("/export/{report_type}")
async def export_report(
    report_type: str,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    format: str = Query(default="excel", description="导出格式: excel, pdf, csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出报表"""
    try:
        if report_type not in ["production", "quality", "equipment"]:
            raise HTTPException(status_code=400, detail="不支持的报表类型")
        
        # 获取报表数据
        if report_type == "production":
            # 构建查询条件
            filters = [
                ProductionPlan.planned_start_date >= start_date,
                ProductionPlan.planned_start_date <= end_date
            ]
            
            base_query = db.query(ProductionPlan).filter(and_(*filters))
            plans = base_query.all()
            
            # 构建报表数据
            report_data = {
                "total_plans": len(plans),
                "completed_plans": len([p for p in plans if p.status == PlanStatus.COMPLETED]),
                "in_progress_plans": len([p for p in plans if p.status == PlanStatus.IN_PROGRESS]),
                "overdue_plans": 0,  # 需要根据实际逻辑计算
                "completion_rate": len([p for p in plans if p.status == PlanStatus.COMPLETED]) / len(plans) * 100 if plans else 0,
                "avg_progress": sum([p.progress for p in plans]) / len(plans) if plans else 0,
                "workshop_stats": [],
                "daily_production": []
            }
            
        elif report_type == "quality":
            # 获取质量报表数据
            filters = [
                QualityCheck.check_date >= start_date,
                QualityCheck.check_date <= end_date
            ]
            
            base_query = db.query(QualityCheck).filter(and_(*filters))
            checks = base_query.all()
            
            report_data = {
                "total_checks": len(checks),
                "passed_checks": len([c for c in checks if c.result == QualityResult.PASSED]),
                "failed_checks": len([c for c in checks if c.result == QualityResult.FAILED]),
                "pass_rate": len([c for c in checks if c.result == QualityResult.PASSED]) / len(checks) * 100 if checks else 0,
                "defect_rate": len([c for c in checks if c.result == QualityResult.FAILED]) / len(checks) * 100 if checks else 0,
                "defect_analysis": [],
                "product_quality": []
            }
            
        elif report_type == "equipment":
            # 获取设备报表数据
            equipment = db.query(Equipment).all()
            
            report_data = {
                "total_equipment": len(equipment),
                "running_equipment": len([e for e in equipment if e.status == EquipmentStatus.RUNNING]),
                "maintenance_equipment": len([e for e in equipment if e.status == EquipmentStatus.MAINTENANCE]),
                "fault_equipment": len([e for e in equipment if e.status == EquipmentStatus.FAULT]),
                "utilization_rate": len([e for e in equipment if e.status == EquipmentStatus.RUNNING]) / len(equipment) * 100 if equipment else 0,
                "maintenance_stats": [],
                "fault_analysis": []
            }
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "excel":
            filename = f"{report_type}_report_{timestamp}.xlsx"
            if report_type == "production":
                filepath = report_exporter.export_production_report_excel(report_data, filename)
            elif report_type == "quality":
                filepath = report_exporter.export_quality_report_excel(report_data, filename)
            elif report_type == "equipment":
                filepath = report_exporter.export_equipment_report_excel(report_data, filename)
                
        elif format == "pdf":
            filename = f"{report_type}_report_{timestamp}.pdf"
            filepath = report_exporter.export_to_pdf(report_data, report_type, filename)
            
        elif format == "csv":
            filename = f"{report_type}_report_{timestamp}.csv"
            filepath = report_exporter.export_to_csv(report_data, report_type, filename)
        
        # 返回文件
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"导出报表异常: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")