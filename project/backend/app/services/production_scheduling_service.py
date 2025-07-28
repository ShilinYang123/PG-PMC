from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority, StageStatus
from app.models.order import Order
from app.models.equipment import Equipment
from app.models.material import Material
from decimal import Decimal
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SchedulingStrategy(Enum):
    """排程策略"""
    EARLIEST_DUE_DATE = "earliest_due_date"  # 最早交期优先
    SHORTEST_PROCESSING_TIME = "shortest_processing_time"  # 最短加工时间优先
    CRITICAL_RATIO = "critical_ratio"  # 紧急比率
    PRIORITY_FIRST = "priority_first"  # 优先级优先
    BALANCED = "balanced"  # 平衡策略

class ResourceType(Enum):
    """资源类型"""
    EQUIPMENT = "equipment"
    WORKSHOP = "workshop"
    PRODUCTION_LINE = "production_line"
    PERSONNEL = "personnel"

@dataclass
class SchedulingConstraint:
    """排程约束"""
    resource_type: ResourceType
    resource_id: str
    capacity: Decimal
    available_time_slots: List[Tuple[datetime, datetime]]
    maintenance_windows: List[Tuple[datetime, datetime]]

@dataclass
class SchedulingResult:
    """排程结果"""
    plan_id: int
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    assigned_resources: Dict[str, str]
    estimated_duration: timedelta
    conflicts: List[str]
    feasibility_score: float

class ProductionSchedulingService:
    """生产计划排程服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_strategy = SchedulingStrategy.BALANCED
        
    def auto_schedule_plans(
        self,
        plan_ids: Optional[List[int]] = None,
        strategy: SchedulingStrategy = None,
        start_date: Optional[datetime] = None,
        constraints: Optional[List[SchedulingConstraint]] = None
    ) -> List[SchedulingResult]:
        """自动排程生产计划
        
        Args:
            plan_ids: 指定计划ID列表，为空则排程所有待排程计划
            strategy: 排程策略
            start_date: 排程开始时间
            constraints: 资源约束
            
        Returns:
            排程结果列表
        """
        try:
            strategy = strategy or self.default_strategy
            start_date = start_date or datetime.now()
            
            # 获取待排程的计划
            plans = self._get_plans_to_schedule(plan_ids)
            if not plans:
                logger.info("没有找到待排程的计划")
                return []
            
            # 获取资源约束
            if constraints is None:
                constraints = self._get_default_constraints()
            
            # 根据策略排序计划
            sorted_plans = self._sort_plans_by_strategy(plans, strategy)
            
            # 执行排程
            results = []
            current_time = start_date
            
            for plan in sorted_plans:
                result = self._schedule_single_plan(
                    plan, current_time, constraints
                )
                results.append(result)
                
                # 更新当前时间为下一个可用时间
                if result.scheduled_end_date:
                    current_time = max(current_time, result.scheduled_end_date)
            
            # 保存排程结果
            self._save_scheduling_results(results)
            
            logger.info(f"完成 {len(results)} 个计划的自动排程")
            return results
            
        except Exception as e:
            logger.error(f"自动排程失败: {str(e)}")
            raise
    
    def manual_schedule_plan(
        self,
        plan_id: int,
        start_date: datetime,
        end_date: datetime,
        resources: Dict[str, str]
    ) -> SchedulingResult:
        """手动排程单个计划
        
        Args:
            plan_id: 计划ID
            start_date: 指定开始时间
            end_date: 指定结束时间
            resources: 指定资源分配
            
        Returns:
            排程结果
        """
        try:
            plan = self.db.query(ProductionPlan).filter(
                ProductionPlan.id == plan_id
            ).first()
            
            if not plan:
                raise ValueError(f"计划 {plan_id} 不存在")
            
            # 验证时间合理性
            if start_date >= end_date:
                raise ValueError("开始时间必须早于结束时间")
            
            # 检查资源冲突
            conflicts = self._check_resource_conflicts(
                start_date, end_date, resources, exclude_plan_id=plan_id
            )
            
            # 创建排程结果
            result = SchedulingResult(
                plan_id=plan_id,
                scheduled_start_date=start_date,
                scheduled_end_date=end_date,
                assigned_resources=resources,
                estimated_duration=end_date - start_date,
                conflicts=conflicts,
                feasibility_score=1.0 if not conflicts else 0.5
            )
            
            # 保存结果
            self._save_scheduling_results([result])
            
            logger.info(f"完成计划 {plan_id} 的手动排程")
            return result
            
        except Exception as e:
            logger.error(f"手动排程失败: {str(e)}")
            raise
    
    def reschedule_plan(
        self,
        plan_id: int,
        new_priority: Optional[PlanPriority] = None,
        new_due_date: Optional[date] = None,
        strategy: Optional[SchedulingStrategy] = None
    ) -> SchedulingResult:
        """重新排程计划
        
        Args:
            plan_id: 计划ID
            new_priority: 新优先级
            new_due_date: 新交期
            strategy: 排程策略
            
        Returns:
            排程结果
        """
        try:
            plan = self.db.query(ProductionPlan).filter(
                ProductionPlan.id == plan_id
            ).first()
            
            if not plan:
                raise ValueError(f"计划 {plan_id} 不存在")
            
            # 更新计划信息
            if new_priority:
                plan.priority = new_priority
            if new_due_date:
                plan.planned_end_date = new_due_date
            
            # 重新排程
            results = self.auto_schedule_plans(
                plan_ids=[plan_id],
                strategy=strategy or self.default_strategy
            )
            
            if results:
                self.db.commit()
                logger.info(f"完成计划 {plan_id} 的重新排程")
                return results[0]
            else:
                raise ValueError("重新排程失败")
                
        except Exception as e:
            logger.error(f"重新排程失败: {str(e)}")
            self.db.rollback()
            raise
    
    def get_gantt_chart_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        workshop: Optional[str] = None,
        production_line: Optional[str] = None
    ) -> Dict:
        """获取甘特图数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            workshop: 车间筛选
            production_line: 生产线筛选
            
        Returns:
            甘特图数据
        """
        try:
            # 构建查询条件
            filters = [ProductionPlan.status.in_([
                PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS, PlanStatus.COMPLETED
            ])]
            
            if start_date:
                filters.append(ProductionPlan.planned_start_date >= start_date)
            if end_date:
                filters.append(ProductionPlan.planned_end_date <= end_date)
            if workshop:
                filters.append(ProductionPlan.workshop == workshop)
            if production_line:
                filters.append(ProductionPlan.production_line == production_line)
            
            # 查询计划
            plans = self.db.query(ProductionPlan).filter(
                and_(*filters)
            ).order_by(ProductionPlan.planned_start_date).all()
            
            # 构建甘特图数据
            gantt_data = {
                "tasks": [],
                "resources": [],
                "timeline": {
                    "start": start_date or min([p.planned_start_date for p in plans]) if plans else date.today(),
                    "end": end_date or max([p.planned_end_date for p in plans]) if plans else date.today()
                }
            }
            
            # 添加任务数据
            for plan in plans:
                task = {
                    "id": plan.id,
                    "name": plan.plan_name,
                    "start": plan.planned_start_date.isoformat(),
                    "end": plan.planned_end_date.isoformat(),
                    "progress": float(plan.progress),
                    "status": plan.status.value,
                    "priority": plan.priority.value,
                    "workshop": plan.workshop,
                    "production_line": plan.production_line,
                    "responsible_person": plan.responsible_person,
                    "product_name": plan.product_name,
                    "planned_quantity": float(plan.planned_quantity),
                    "unit": plan.unit
                }
                
                # 添加实际时间（如果有）
                if plan.actual_start_date:
                    task["actual_start"] = plan.actual_start_date.isoformat()
                if plan.actual_end_date:
                    task["actual_end"] = plan.actual_end_date.isoformat()
                
                gantt_data["tasks"].append(task)
            
            # 添加资源数据
            workshops = list(set([p.workshop for p in plans if p.workshop]))
            production_lines = list(set([p.production_line for p in plans if p.production_line]))
            
            gantt_data["resources"] = {
                "workshops": workshops,
                "production_lines": production_lines
            }
            
            return gantt_data
            
        except Exception as e:
            logger.error(f"获取甘特图数据失败: {str(e)}")
            raise
    
    def analyze_scheduling_conflicts(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """分析排程冲突
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            
        Returns:
            冲突分析结果
        """
        try:
            # 获取指定时间范围内的计划
            filters = [ProductionPlan.status.in_([
                PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS
            ])]
            
            if start_date:
                filters.append(ProductionPlan.planned_start_date >= start_date)
            if end_date:
                filters.append(ProductionPlan.planned_end_date <= end_date)
            
            plans = self.db.query(ProductionPlan).filter(
                and_(*filters)
            ).all()
            
            conflicts = {
                "resource_conflicts": [],
                "time_conflicts": [],
                "capacity_overloads": [],
                "summary": {
                    "total_conflicts": 0,
                    "affected_plans": 0,
                    "critical_conflicts": 0
                }
            }
            
            # 检查资源冲突
            resource_usage = {}
            for plan in plans:
                key = f"{plan.workshop}_{plan.production_line}"
                if key not in resource_usage:
                    resource_usage[key] = []
                resource_usage[key].append(plan)
            
            # 分析每个资源的使用情况
            for resource_key, resource_plans in resource_usage.items():
                if len(resource_plans) > 1:
                    # 检查时间重叠
                    for i, plan1 in enumerate(resource_plans):
                        for plan2 in resource_plans[i+1:]:
                            if self._check_time_overlap(plan1, plan2):
                                conflict = {
                                    "type": "resource_conflict",
                                    "resource": resource_key,
                                    "plan1": {
                                        "id": plan1.id,
                                        "name": plan1.plan_name,
                                        "start": plan1.planned_start_date.isoformat(),
                                        "end": plan1.planned_end_date.isoformat()
                                    },
                                    "plan2": {
                                        "id": plan2.id,
                                        "name": plan2.plan_name,
                                        "start": plan2.planned_start_date.isoformat(),
                                        "end": plan2.planned_end_date.isoformat()
                                    },
                                    "severity": "high" if plan1.priority == PlanPriority.HIGH or plan2.priority == PlanPriority.HIGH else "medium"
                                }
                                conflicts["resource_conflicts"].append(conflict)
            
            # 统计冲突信息
            conflicts["summary"]["total_conflicts"] = len(conflicts["resource_conflicts"])
            conflicts["summary"]["affected_plans"] = len(set([
                c["plan1"]["id"] for c in conflicts["resource_conflicts"]
            ] + [
                c["plan2"]["id"] for c in conflicts["resource_conflicts"]
            ]))
            conflicts["summary"]["critical_conflicts"] = len([
                c for c in conflicts["resource_conflicts"] if c["severity"] == "high"
            ])
            
            return conflicts
            
        except Exception as e:
            logger.error(f"分析排程冲突失败: {str(e)}")
            raise
    
    def _get_plans_to_schedule(self, plan_ids: Optional[List[int]]) -> List[ProductionPlan]:
        """获取待排程的计划"""
        query = self.db.query(ProductionPlan)
        
        if plan_ids:
            query = query.filter(ProductionPlan.id.in_(plan_ids))
        else:
            query = query.filter(ProductionPlan.status.in_([
                PlanStatus.DRAFT, PlanStatus.CONFIRMED
            ]))
        
        return query.all()
    
    def _get_default_constraints(self) -> List[SchedulingConstraint]:
        """获取默认资源约束"""
        # 这里可以从数据库或配置文件中获取资源约束
        # 暂时返回空列表，实际应用中需要根据具体情况实现
        return []
    
    def _sort_plans_by_strategy(
        self, 
        plans: List[ProductionPlan], 
        strategy: SchedulingStrategy
    ) -> List[ProductionPlan]:
        """根据策略排序计划"""
        if strategy == SchedulingStrategy.EARLIEST_DUE_DATE:
            return sorted(plans, key=lambda p: p.planned_end_date)
        elif strategy == SchedulingStrategy.PRIORITY_FIRST:
            priority_order = {PlanPriority.URGENT: 0, PlanPriority.HIGH: 1, PlanPriority.MEDIUM: 2, PlanPriority.LOW: 3}
            return sorted(plans, key=lambda p: (priority_order.get(p.priority, 4), p.planned_end_date))
        elif strategy == SchedulingStrategy.SHORTEST_PROCESSING_TIME:
            return sorted(plans, key=lambda p: (p.planned_end_date - p.planned_start_date).days)
        else:  # BALANCED or others
            # 平衡策略：优先级 + 交期 + 处理时间
            priority_order = {PlanPriority.URGENT: 0, PlanPriority.HIGH: 1, PlanPriority.MEDIUM: 2, PlanPriority.LOW: 3}
            return sorted(plans, key=lambda p: (
                priority_order.get(p.priority, 4),
                p.planned_end_date,
                (p.planned_end_date - p.planned_start_date).days
            ))
    
    def _schedule_single_plan(
        self,
        plan: ProductionPlan,
        current_time: datetime,
        constraints: List[SchedulingConstraint]
    ) -> SchedulingResult:
        """排程单个计划"""
        try:
            # 计算预估工期
            estimated_duration = timedelta(days=(plan.planned_end_date - plan.planned_start_date).days)
            
            # 确定开始时间（不早于当前时间和计划开始时间）
            start_time = max(current_time, datetime.combine(plan.planned_start_date, datetime.min.time()))
            end_time = start_time + estimated_duration
            
            # 分配资源
            assigned_resources = {
                "workshop": plan.workshop or "默认车间",
                "production_line": plan.production_line or "默认生产线",
                "responsible_person": plan.responsible_person or "待分配"
            }
            
            # 检查冲突
            conflicts = self._check_resource_conflicts(
                start_time, end_time, assigned_resources, exclude_plan_id=plan.id
            )
            
            # 计算可行性评分
            feasibility_score = self._calculate_feasibility_score(
                plan, start_time, end_time, conflicts
            )
            
            return SchedulingResult(
                plan_id=plan.id,
                scheduled_start_date=start_time,
                scheduled_end_date=end_time,
                assigned_resources=assigned_resources,
                estimated_duration=estimated_duration,
                conflicts=conflicts,
                feasibility_score=feasibility_score
            )
            
        except Exception as e:
            logger.error(f"排程计划 {plan.id} 失败: {str(e)}")
            return SchedulingResult(
                plan_id=plan.id,
                scheduled_start_date=current_time,
                scheduled_end_date=current_time,
                assigned_resources={},
                estimated_duration=timedelta(),
                conflicts=[f"排程失败: {str(e)}"],
                feasibility_score=0.0
            )
    
    def _check_resource_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        resources: Dict[str, str],
        exclude_plan_id: Optional[int] = None
    ) -> List[str]:
        """检查资源冲突"""
        conflicts = []
        
        try:
            # 查询同时间段使用相同资源的计划
            query = self.db.query(ProductionPlan).filter(
                and_(
                    ProductionPlan.status.in_([PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS]),
                    or_(
                        and_(
                            ProductionPlan.planned_start_date <= start_time.date(),
                            ProductionPlan.planned_end_date >= start_time.date()
                        ),
                        and_(
                            ProductionPlan.planned_start_date <= end_time.date(),
                            ProductionPlan.planned_end_date >= end_time.date()
                        ),
                        and_(
                            ProductionPlan.planned_start_date >= start_time.date(),
                            ProductionPlan.planned_end_date <= end_time.date()
                        )
                    )
                )
            )
            
            if exclude_plan_id:
                query = query.filter(ProductionPlan.id != exclude_plan_id)
            
            conflicting_plans = query.all()
            
            for plan in conflicting_plans:
                if (plan.workshop == resources.get("workshop") and 
                    plan.production_line == resources.get("production_line")):
                    conflicts.append(f"与计划 {plan.plan_number} 存在资源冲突")
            
        except Exception as e:
            logger.error(f"检查资源冲突失败: {str(e)}")
            conflicts.append(f"冲突检查失败: {str(e)}")
        
        return conflicts
    
    def _calculate_feasibility_score(
        self,
        plan: ProductionPlan,
        start_time: datetime,
        end_time: datetime,
        conflicts: List[str]
    ) -> float:
        """计算可行性评分"""
        score = 1.0
        
        # 冲突扣分
        if conflicts:
            score -= 0.3 * len(conflicts)
        
        # 延期扣分
        if end_time.date() > plan.planned_end_date:
            delay_days = (end_time.date() - plan.planned_end_date).days
            score -= 0.1 * delay_days
        
        # 提前加分
        if end_time.date() < plan.planned_end_date:
            advance_days = (plan.planned_end_date - end_time.date()).days
            score += 0.05 * advance_days
        
        return max(0.0, min(1.0, score))
    
    def _save_scheduling_results(self, results: List[SchedulingResult]):
        """保存排程结果"""
        try:
            for result in results:
                plan = self.db.query(ProductionPlan).filter(
                    ProductionPlan.id == result.plan_id
                ).first()
                
                if plan:
                    # 更新计划的排程信息
                    plan.planned_start_date = result.scheduled_start_date.date()
                    plan.planned_end_date = result.scheduled_end_date.date()
                    
                    # 更新资源分配
                    if "workshop" in result.assigned_resources:
                        plan.workshop = result.assigned_resources["workshop"]
                    if "production_line" in result.assigned_resources:
                        plan.production_line = result.assigned_resources["production_line"]
                    if "responsible_person" in result.assigned_resources:
                        plan.responsible_person = result.assigned_resources["responsible_person"]
                    
                    # 如果没有冲突且可行性评分高，则确认计划
                    if not result.conflicts and result.feasibility_score > 0.8:
                        plan.status = PlanStatus.CONFIRMED
                    
                    plan.updated_at = datetime.now()
            
            self.db.commit()
            logger.info(f"保存 {len(results)} 个排程结果")
            
        except Exception as e:
            logger.error(f"保存排程结果失败: {str(e)}")
            self.db.rollback()
            raise
    
    def _check_time_overlap(self, plan1: ProductionPlan, plan2: ProductionPlan) -> bool:
        """检查两个计划的时间是否重叠"""
        return not (
            plan1.planned_end_date < plan2.planned_start_date or
            plan2.planned_end_date < plan1.planned_start_date
        )

# 创建全局服务实例
production_scheduling_service = None

def get_production_scheduling_service(db: Session) -> ProductionSchedulingService:
    """获取生产排程服务实例"""
    return ProductionSchedulingService(db)