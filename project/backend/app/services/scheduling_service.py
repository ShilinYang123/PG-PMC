"""自动排产算法服务

实现基于约束条件的智能排产算法，支持：
- 产能约束排产
- 交期优先级排产
- 物料可用性检查
- 设备负荷均衡
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from loguru import logger


class Priority(Enum):
    """优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"  # 待排产
    SCHEDULED = "scheduled"  # 已排产
    IN_PROGRESS = "in_progress"  # 生产中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


@dataclass
class ProductionOrder:
    """生产订单数据类"""
    order_id: str
    product_code: str
    quantity: int
    due_date: datetime
    priority: Priority
    estimated_hours: float
    material_requirements: Dict[str, int]
    status: OrderStatus = OrderStatus.PENDING
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    assigned_equipment: Optional[str] = None


@dataclass
class Equipment:
    """设备信息数据类"""
    equipment_id: str
    name: str
    capacity_per_hour: float
    available_hours_per_day: float
    maintenance_schedule: List[Tuple[datetime, datetime]]
    current_load: float = 0.0


@dataclass
class Material:
    """物料信息数据类"""
    material_code: str
    name: str
    current_stock: int
    safety_stock: int
    lead_time_days: int
    supplier: str


class SchedulingService:
    """自动排产服务"""
    
    def __init__(self):
        self.orders: List[ProductionOrder] = []
        self.equipment: List[Equipment] = []
        self.materials: List[Material] = []
        self.schedule_results: List[Dict] = []
        
    def add_order(self, order: ProductionOrder) -> None:
        """添加生产订单"""
        self.orders.append(order)
        logger.info(f"添加生产订单: {order.order_id}, 产品: {order.product_code}, 数量: {order.quantity}")
    
    def add_equipment(self, equipment: Equipment) -> None:
        """添加设备信息"""
        self.equipment.append(equipment)
        logger.info(f"添加设备: {equipment.equipment_id}, 名称: {equipment.name}")
    
    def add_material(self, material: Material) -> None:
        """添加物料信息"""
        self.materials.append(material)
        logger.info(f"添加物料: {material.material_code}, 库存: {material.current_stock}")
    
    def check_material_availability(self, order: ProductionOrder) -> Tuple[bool, List[str]]:
        """检查物料可用性"""
        missing_materials = []
        
        for material_code, required_qty in order.material_requirements.items():
            material = next((m for m in self.materials if m.material_code == material_code), None)
            if not material:
                missing_materials.append(f"{material_code}: 物料不存在")
                continue
                
            if material.current_stock < required_qty:
                shortage = required_qty - material.current_stock
                missing_materials.append(f"{material_code}: 缺料{shortage}件")
        
        is_available = len(missing_materials) == 0
        return is_available, missing_materials
    
    def find_available_equipment(self, order: ProductionOrder, start_time: datetime) -> Optional[Equipment]:
        """查找可用设备"""
        end_time = start_time + timedelta(hours=order.estimated_hours)
        
        for equipment in self.equipment:
            # 检查设备是否在维护期间
            in_maintenance = any(
                start_time < maint_end and end_time > maint_start
                for maint_start, maint_end in equipment.maintenance_schedule
            )
            
            if in_maintenance:
                continue
                
            # 检查设备负荷
            daily_hours = equipment.available_hours_per_day
            if equipment.current_load + order.estimated_hours <= daily_hours:
                return equipment
        
        return None
    
    def calculate_priority_score(self, order: ProductionOrder) -> float:
        """计算订单优先级分数"""
        # 基础优先级分数
        priority_scores = {
            Priority.LOW: 1.0,
            Priority.NORMAL: 2.0,
            Priority.HIGH: 3.0,
            Priority.URGENT: 4.0
        }
        
        base_score = priority_scores[order.priority]
        
        # 交期紧急度调整
        days_to_due = (order.due_date - datetime.now()).days
        if days_to_due <= 1:
            urgency_multiplier = 3.0
        elif days_to_due <= 3:
            urgency_multiplier = 2.0
        elif days_to_due <= 7:
            urgency_multiplier = 1.5
        else:
            urgency_multiplier = 1.0
        
        return base_score * urgency_multiplier
    
    def schedule_orders(self, start_date: datetime = None) -> Dict:
        """执行自动排产"""
        if start_date is None:
            start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        logger.info(f"开始自动排产，起始时间: {start_date}")
        
        # 按优先级排序订单
        pending_orders = [o for o in self.orders if o.status == OrderStatus.PENDING]
        sorted_orders = sorted(pending_orders, key=self.calculate_priority_score, reverse=True)
        
        scheduled_orders = []
        failed_orders = []
        current_time = start_date
        
        for order in sorted_orders:
            # 检查物料可用性
            material_available, missing_materials = self.check_material_availability(order)
            if not material_available:
                failed_orders.append({
                    'order': order,
                    'reason': f"物料不足: {', '.join(missing_materials)}"
                })
                continue
            
            # 查找可用设备
            equipment = self.find_available_equipment(order, current_time)
            if not equipment:
                failed_orders.append({
                    'order': order,
                    'reason': "无可用设备"
                })
                continue
            
            # 排产成功
            order.status = OrderStatus.SCHEDULED
            order.scheduled_start = current_time
            order.scheduled_end = current_time + timedelta(hours=order.estimated_hours)
            order.assigned_equipment = equipment.equipment_id
            
            # 更新设备负荷
            equipment.current_load += order.estimated_hours
            
            # 扣减物料库存
            for material_code, required_qty in order.material_requirements.items():
                material = next(m for m in self.materials if m.material_code == material_code)
                material.current_stock -= required_qty
            
            scheduled_orders.append(order)
            current_time = order.scheduled_end
            
            logger.info(f"订单 {order.order_id} 排产成功: {order.scheduled_start} - {order.scheduled_end}")
        
        # 生成排产结果
        result = {
            'schedule_time': datetime.now(),
            'total_orders': len(pending_orders),
            'scheduled_count': len(scheduled_orders),
            'failed_count': len(failed_orders),
            'scheduled_orders': scheduled_orders,
            'failed_orders': failed_orders,
            'equipment_utilization': self._calculate_equipment_utilization()
        }
        
        self.schedule_results.append(result)
        logger.info(f"排产完成: 成功{len(scheduled_orders)}个，失败{len(failed_orders)}个")
        
        return result
    
    def _calculate_equipment_utilization(self) -> Dict[str, float]:
        """计算设备利用率"""
        utilization = {}
        for equipment in self.equipment:
            utilization_rate = (equipment.current_load / equipment.available_hours_per_day) * 100
            utilization[equipment.equipment_id] = round(utilization_rate, 2)
        return utilization
    
    def get_schedule_gantt_data(self) -> List[Dict]:
        """获取甘特图数据"""
        gantt_data = []
        
        for order in self.orders:
            if order.status == OrderStatus.SCHEDULED and order.scheduled_start and order.scheduled_end:
                gantt_data.append({
                    'order_id': order.order_id,
                    'product_code': order.product_code,
                    'start_time': order.scheduled_start.isoformat(),
                    'end_time': order.scheduled_end.isoformat(),
                    'equipment': order.assigned_equipment,
                    'priority': order.priority.name,
                    'status': order.status.value
                })
        
        return gantt_data
    
    def reschedule_order(self, order_id: str, new_priority: Priority = None, new_due_date: datetime = None) -> bool:
        """重新排产指定订单"""
        order = next((o for o in self.orders if o.order_id == order_id), None)
        if not order:
            logger.error(f"订单 {order_id} 不存在")
            return False
        
        # 更新订单信息
        if new_priority:
            order.priority = new_priority
        if new_due_date:
            order.due_date = new_due_date
        
        # 重置订单状态
        if order.status == OrderStatus.SCHEDULED:
            # 释放设备资源
            if order.assigned_equipment:
                equipment = next(e for e in self.equipment if e.equipment_id == order.assigned_equipment)
                equipment.current_load -= order.estimated_hours
            
            # 恢复物料库存
            for material_code, required_qty in order.material_requirements.items():
                material = next(m for m in self.materials if m.material_code == material_code)
                material.current_stock += required_qty
        
        order.status = OrderStatus.PENDING
        order.scheduled_start = None
        order.scheduled_end = None
        order.assigned_equipment = None
        
        logger.info(f"订单 {order_id} 已重置为待排产状态")
        return True
    
    def get_production_summary(self) -> Dict:
        """获取生产概况"""
        total_orders = len(self.orders)
        scheduled_orders = len([o for o in self.orders if o.status == OrderStatus.SCHEDULED])
        in_progress_orders = len([o for o in self.orders if o.status == OrderStatus.IN_PROGRESS])
        completed_orders = len([o for o in self.orders if o.status == OrderStatus.COMPLETED])
        
        return {
            'total_orders': total_orders,
            'scheduled_orders': scheduled_orders,
            'in_progress_orders': in_progress_orders,
            'completed_orders': completed_orders,
            'completion_rate': round((completed_orders / total_orders * 100) if total_orders > 0 else 0, 2),
            'equipment_count': len(self.equipment),
            'material_count': len(self.materials)
        }


# 创建全局排产服务实例
scheduling_service = SchedulingService()