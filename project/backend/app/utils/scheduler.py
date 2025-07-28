from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import heapq
from sqlalchemy.orm import Session
from app.models.production_plan import ProductionPlan, ProductionStage, PlanStatus, PlanPriority
from app.models.order import Order
import logging

logger = logging.getLogger(__name__)

class ScheduleStrategy(str, Enum):
    """排程策略枚举"""
    PRIORITY_FIRST = "priority_first"  # 优先级优先
    DEADLINE_FIRST = "deadline_first"  # 交期优先
    SHORTEST_FIRST = "shortest_first"  # 最短作业优先
    BALANCED = "balanced"  # 平衡策略

@dataclass
class ResourceConstraint:
    """资源约束"""
    workshop: str
    production_line: str
    capacity: int  # 产能（件/天）
    available_hours: int  # 可用工时/天
    skill_requirements: List[str]  # 技能要求
    
@dataclass
class ScheduleTask:
    """排程任务"""
    plan_id: int
    plan_no: str
    product_name: str
    quantity: int
    priority: PlanPriority
    deadline: datetime
    estimated_duration: int  # 预计工期（天）
    workshop: str
    production_line: str
    dependencies: List[int]  # 依赖的任务ID
    earliest_start: datetime  # 最早开始时间
    latest_finish: datetime  # 最晚完成时间
    
@dataclass
class ScheduleResult:
    """排程结果"""
    plan_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    assigned_workshop: str
    assigned_line: str
    resource_utilization: float  # 资源利用率
    
class ProductionScheduler:
    """生产排程器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.priority_weights = {
            PlanPriority.URGENT: 4,
            PlanPriority.HIGH: 3,
            PlanPriority.MEDIUM: 2,
            PlanPriority.LOW: 1
        }
        
    def schedule_production_plans(
        self,
        plan_ids: List[int],
        strategy: ScheduleStrategy = ScheduleStrategy.BALANCED,
        start_date: Optional[datetime] = None
    ) -> List[ScheduleResult]:
        """对生产计划进行排程"""
        try:
            # 获取生产计划数据
            tasks = self._prepare_tasks(plan_ids)
            if not tasks:
                return []
            
            # 获取资源约束
            resources = self._get_resource_constraints()
            
            # 根据策略进行排程
            if strategy == ScheduleStrategy.PRIORITY_FIRST:
                results = self._schedule_by_priority(tasks, resources, start_date)
            elif strategy == ScheduleStrategy.DEADLINE_FIRST:
                results = self._schedule_by_deadline(tasks, resources, start_date)
            elif strategy == ScheduleStrategy.SHORTEST_FIRST:
                results = self._schedule_by_duration(tasks, resources, start_date)
            else:  # BALANCED
                results = self._schedule_balanced(tasks, resources, start_date)
            
            # 优化排程结果
            optimized_results = self._optimize_schedule(results, tasks, resources)
            
            logger.info(f"Successfully scheduled {len(optimized_results)} production plans")
            return optimized_results
            
        except Exception as e:
            logger.error(f"Error in production scheduling: {str(e)}")
            raise
    
    def _prepare_tasks(self, plan_ids: List[int]) -> List[ScheduleTask]:
        """准备排程任务数据"""
        tasks = []
        
        plans = self.db.query(ProductionPlan).filter(
            ProductionPlan.id.in_(plan_ids),
            ProductionPlan.status.in_([PlanStatus.DRAFT, PlanStatus.CONFIRMED])
        ).all()
        
        for plan in plans:
            # 计算预计工期
            estimated_duration = self._calculate_duration(plan)
            
            # 获取依赖关系
            dependencies = self._get_dependencies(plan)
            
            # 计算最早开始时间和最晚完成时间
            earliest_start = plan.plan_start_date or datetime.now()
            latest_finish = plan.plan_end_date or (earliest_start + timedelta(days=estimated_duration * 2))
            
            task = ScheduleTask(
                plan_id=plan.id,
                plan_no=plan.plan_no,
                product_name=plan.product_name,
                quantity=plan.quantity,
                priority=plan.priority,
                deadline=plan.plan_end_date or latest_finish,
                estimated_duration=estimated_duration,
                workshop=plan.workshop or "默认车间",
                production_line=plan.production_line or "默认生产线",
                dependencies=dependencies,
                earliest_start=earliest_start,
                latest_finish=latest_finish
            )
            tasks.append(task)
        
        return tasks
    
    def _calculate_duration(self, plan: ProductionPlan) -> int:
        """计算生产计划的预计工期"""
        # 基础工期计算（可根据实际情况调整）
        base_duration = max(1, plan.quantity // 100)  # 每100件需要1天
        
        # 根据产品复杂度调整
        complexity_factor = 1.0
        if plan.technical_requirements:
            complexity_factor = 1.5
        
        # 根据优先级调整
        priority_factor = {
            PlanPriority.URGENT: 0.8,  # 紧急任务加快进度
            PlanPriority.HIGH: 0.9,
            PlanPriority.MEDIUM: 1.0,
            PlanPriority.LOW: 1.2
        }.get(plan.priority, 1.0)
        
        return max(1, int(base_duration * complexity_factor * priority_factor))
    
    def _get_dependencies(self, plan: ProductionPlan) -> List[int]:
        """获取生产计划的依赖关系"""
        dependencies = []
        
        # 如果有关联订单，检查是否有前置订单
        if plan.order_id:
            # 查找同一客户的前置订单
            related_plans = self.db.query(ProductionPlan).join(Order).filter(
                Order.customer_name == plan.order.customer_name,
                ProductionPlan.id != plan.id,
                ProductionPlan.status.in_([PlanStatus.DRAFT, PlanStatus.CONFIRMED, PlanStatus.IN_PROGRESS])
            ).all()
            
            for related_plan in related_plans:
                if related_plan.priority.value >= plan.priority.value:
                    dependencies.append(related_plan.id)
        
        return dependencies
    
    def _get_resource_constraints(self) -> Dict[str, ResourceConstraint]:
        """获取资源约束信息"""
        # 这里可以从数据库或配置文件中获取资源信息
        # 暂时使用硬编码的资源配置
        return {
            "车间A": ResourceConstraint(
                workshop="车间A",
                production_line="生产线1",
                capacity=500,
                available_hours=8,
                skill_requirements=["机械加工", "质量检验"]
            ),
            "车间B": ResourceConstraint(
                workshop="车间B",
                production_line="生产线2",
                capacity=300,
                available_hours=8,
                skill_requirements=["装配", "调试"]
            ),
            "车间C": ResourceConstraint(
                workshop="车间C",
                production_line="生产线3",
                capacity=200,
                available_hours=8,
                skill_requirements=["精密加工", "表面处理"]
            )
        }
    
    def _schedule_by_priority(self, tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint], start_date: Optional[datetime]) -> List[ScheduleResult]:
        """按优先级排程"""
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: (-self.priority_weights[t.priority], t.deadline))
        return self._assign_resources(sorted_tasks, resources, start_date)
    
    def _schedule_by_deadline(self, tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint], start_date: Optional[datetime]) -> List[ScheduleResult]:
        """按交期排程"""
        # 按交期排序
        sorted_tasks = sorted(tasks, key=lambda t: t.deadline)
        return self._assign_resources(sorted_tasks, resources, start_date)
    
    def _schedule_by_duration(self, tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint], start_date: Optional[datetime]) -> List[ScheduleResult]:
        """按工期长短排程"""
        # 按工期排序（最短作业优先）
        sorted_tasks = sorted(tasks, key=lambda t: t.estimated_duration)
        return self._assign_resources(sorted_tasks, resources, start_date)
    
    def _schedule_balanced(self, tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint], start_date: Optional[datetime]) -> List[ScheduleResult]:
        """平衡策略排程"""
        # 综合考虑优先级、交期、工期的平衡排程
        def score_function(task: ScheduleTask) -> float:
            priority_score = self.priority_weights[task.priority] * 0.4
            
            # 交期紧迫度评分
            days_to_deadline = (task.deadline - datetime.now()).days
            deadline_score = max(0, 10 - days_to_deadline) * 0.4
            
            # 工期评分（工期越短评分越高）
            duration_score = max(0, 10 - task.estimated_duration) * 0.2
            
            return priority_score + deadline_score + duration_score
        
        sorted_tasks = sorted(tasks, key=score_function, reverse=True)
        return self._assign_resources(sorted_tasks, resources, start_date)
    
    def _assign_resources(self, sorted_tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint], start_date: Optional[datetime]) -> List[ScheduleResult]:
        """分配资源并生成排程结果"""
        results = []
        resource_schedule = {name: [] for name in resources.keys()}  # 记录每个资源的占用情况
        current_date = start_date or datetime.now()
        
        for task in sorted_tasks:
            # 找到最适合的资源
            best_resource = self._find_best_resource(task, resources, resource_schedule)
            
            if best_resource:
                # 计算开始时间（考虑依赖关系）
                earliest_start = max(task.earliest_start, current_date)
                if task.dependencies:
                    # 找到依赖任务的最晚完成时间
                    dep_finish_times = []
                    for dep_id in task.dependencies:
                        for result in results:
                            if result.plan_id == dep_id:
                                dep_finish_times.append(result.scheduled_end)
                    if dep_finish_times:
                        earliest_start = max(earliest_start, max(dep_finish_times))
                
                # 找到资源的下一个可用时间
                available_start = self._find_next_available_time(best_resource, resource_schedule, earliest_start)
                scheduled_end = available_start + timedelta(days=task.estimated_duration)
                
                # 记录资源占用
                resource_schedule[best_resource].append((available_start, scheduled_end))
                
                # 计算资源利用率
                resource_constraint = resources[best_resource]
                utilization = min(1.0, task.quantity / (resource_constraint.capacity * task.estimated_duration))
                
                result = ScheduleResult(
                    plan_id=task.plan_id,
                    scheduled_start=available_start,
                    scheduled_end=scheduled_end,
                    assigned_workshop=best_resource,
                    assigned_line=resource_constraint.production_line,
                    resource_utilization=utilization
                )
                results.append(result)
        
        return results
    
    def _find_best_resource(self, task: ScheduleTask, resources: Dict[str, ResourceConstraint], resource_schedule: Dict[str, List[Tuple[datetime, datetime]]]) -> Optional[str]:
        """为任务找到最佳资源"""
        best_resource = None
        best_score = -1
        
        for resource_name, constraint in resources.items():
            # 检查资源是否满足任务要求
            if task.workshop and task.workshop != resource_name:
                continue
            
            # 计算资源评分
            score = self._calculate_resource_score(task, constraint, resource_schedule[resource_name])
            
            if score > best_score:
                best_score = score
                best_resource = resource_name
        
        return best_resource
    
    def _calculate_resource_score(self, task: ScheduleTask, constraint: ResourceConstraint, schedule: List[Tuple[datetime, datetime]]) -> float:
        """计算资源评分"""
        # 基础评分：产能匹配度
        capacity_score = min(1.0, constraint.capacity / max(1, task.quantity)) * 0.4
        
        # 空闲度评分
        current_load = len(schedule)
        idle_score = max(0, 1 - current_load / 10) * 0.3
        
        # 技能匹配度评分（简化处理）
        skill_score = 0.3  # 假设所有资源都能满足基本技能要求
        
        return capacity_score + idle_score + skill_score
    
    def _find_next_available_time(self, resource: str, resource_schedule: Dict[str, List[Tuple[datetime, datetime]]], earliest_start: datetime) -> datetime:
        """找到资源的下一个可用时间"""
        schedule = resource_schedule[resource]
        
        if not schedule:
            return earliest_start
        
        # 按时间排序
        sorted_schedule = sorted(schedule, key=lambda x: x[0])
        
        # 检查是否可以在现有任务之间插入
        for i, (start, end) in enumerate(sorted_schedule):
            if earliest_start < start:
                return earliest_start
            if i < len(sorted_schedule) - 1:
                next_start = sorted_schedule[i + 1][0]
                if end <= earliest_start < next_start:
                    return earliest_start
        
        # 在最后一个任务之后安排
        last_end = sorted_schedule[-1][1]
        return max(earliest_start, last_end)
    
    def _optimize_schedule(self, results: List[ScheduleResult], tasks: List[ScheduleTask], resources: Dict[str, ResourceConstraint]) -> List[ScheduleResult]:
        """优化排程结果"""
        # 简单的优化：检查是否有任务可以提前
        optimized_results = results.copy()
        
        # 按开始时间排序
        optimized_results.sort(key=lambda r: r.scheduled_start)
        
        # 尝试压缩时间间隔
        for i in range(1, len(optimized_results)):
            current = optimized_results[i]
            previous = optimized_results[i-1]
            
            # 如果同一资源且有时间间隔，尝试提前
            if (current.assigned_workshop == previous.assigned_workshop and 
                current.scheduled_start > previous.scheduled_end):
                
                # 检查是否有依赖关系阻止提前
                task = next(t for t in tasks if t.plan_id == current.plan_id)
                can_advance = True
                
                for dep_id in task.dependencies:
                    dep_result = next((r for r in optimized_results if r.plan_id == dep_id), None)
                    if dep_result and dep_result.scheduled_end > previous.scheduled_end:
                        can_advance = False
                        break
                
                if can_advance:
                    duration = current.scheduled_end - current.scheduled_start
                    current.scheduled_start = previous.scheduled_end
                    current.scheduled_end = current.scheduled_start + duration
        
        return optimized_results
    
    def get_gantt_data(self, results: List[ScheduleResult]) -> Dict:
        """生成甘特图数据"""
        gantt_data = {
            "tasks": [],
            "resources": [],
            "timeline": {
                "start": None,
                "end": None
            }
        }
        
        if not results:
            return gantt_data
        
        # 获取时间范围
        start_times = [r.scheduled_start for r in results]
        end_times = [r.scheduled_end for r in results]
        gantt_data["timeline"]["start"] = min(start_times)
        gantt_data["timeline"]["end"] = max(end_times)
        
        # 获取任务详情
        plan_ids = [r.plan_id for r in results]
        plans = self.db.query(ProductionPlan).filter(ProductionPlan.id.in_(plan_ids)).all()
        plan_dict = {p.id: p for p in plans}
        
        # 构建任务数据
        for result in results:
            plan = plan_dict.get(result.plan_id)
            if plan:
                task_data = {
                    "id": result.plan_id,
                    "name": f"{plan.plan_no} - {plan.product_name}",
                    "start": result.scheduled_start.isoformat(),
                    "end": result.scheduled_end.isoformat(),
                    "resource": result.assigned_workshop,
                    "progress": plan.progress,
                    "priority": plan.priority.value,
                    "status": plan.status.value,
                    "utilization": result.resource_utilization
                }
                gantt_data["tasks"].append(task_data)
        
        # 构建资源数据
        resources_used = set(r.assigned_workshop for r in results)
        for resource in resources_used:
            gantt_data["resources"].append({
                "id": resource,
                "name": resource
            })
        
        return gantt_data