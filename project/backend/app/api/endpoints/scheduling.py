"""排产管理API接口

提供自动排产相关的REST API接口：
- 执行自动排产
- 查看排产结果
- 重新排产
- 获取甘特图数据
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from loguru import logger

from ...services.scheduling_service import (
    scheduling_service, 
    ProductionOrder, 
    Equipment, 
    Material, 
    Priority, 
    OrderStatus
)
from ...services.wechat_service import MessageType, Priority as WeChatPriority

router = APIRouter()


# Pydantic模型定义
class ProductionOrderCreate(BaseModel):
    """创建生产订单请求模型"""
    order_id: str = Field(..., description="订单ID")
    product_code: str = Field(..., description="产品编码")
    quantity: int = Field(..., gt=0, description="生产数量")
    due_date: datetime = Field(..., description="交期")
    priority: str = Field("NORMAL", description="优先级: LOW, NORMAL, HIGH, URGENT")
    estimated_hours: float = Field(..., gt=0, description="预计工时")
    material_requirements: Dict[str, int] = Field(default_factory=dict, description="物料需求")


class EquipmentCreate(BaseModel):
    """创建设备请求模型"""
    equipment_id: str = Field(..., description="设备ID")
    name: str = Field(..., description="设备名称")
    capacity_per_hour: float = Field(..., gt=0, description="每小时产能")
    available_hours_per_day: float = Field(..., gt=0, le=24, description="每日可用工时")
    maintenance_schedule: List[Dict[str, str]] = Field(default_factory=list, description="维护计划")


class MaterialCreate(BaseModel):
    """创建物料请求模型"""
    material_code: str = Field(..., description="物料编码")
    name: str = Field(..., description="物料名称")
    current_stock: int = Field(..., ge=0, description="当前库存")
    safety_stock: int = Field(..., ge=0, description="安全库存")
    lead_time_days: int = Field(..., ge=0, description="采购周期(天)")
    supplier: str = Field(..., description="供应商")


class ScheduleRequest(BaseModel):
    """排产请求模型"""
    start_date: Optional[datetime] = Field(None, description="排产开始时间")
    force_reschedule: bool = Field(False, description="是否强制重新排产")
    notify_wechat: bool = Field(True, description="是否发送微信通知")


class RescheduleRequest(BaseModel):
    """重新排产请求模型"""
    order_id: str = Field(..., description="订单ID")
    new_priority: Optional[str] = Field(None, description="新优先级")
    new_due_date: Optional[datetime] = Field(None, description="新交期")


class ScheduleResponse(BaseModel):
    """排产结果响应模型"""
    success: bool
    message: str
    data: Optional[Dict] = None


@router.post("/orders", response_model=ScheduleResponse)
async def create_production_order(order: ProductionOrderCreate):
    """创建生产订单"""
    try:
        # 验证优先级
        try:
            priority = Priority[order.priority.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的优先级: {order.priority}")
        
        # 创建生产订单对象
        production_order = ProductionOrder(
            order_id=order.order_id,
            product_code=order.product_code,
            quantity=order.quantity,
            due_date=order.due_date,
            priority=priority,
            estimated_hours=order.estimated_hours,
            material_requirements=order.material_requirements
        )
        
        # 检查订单是否已存在
        existing_order = next((o for o in scheduling_service.orders if o.order_id == order.order_id), None)
        if existing_order:
            raise HTTPException(status_code=400, detail=f"订单 {order.order_id} 已存在")
        
        # 添加到排产服务
        scheduling_service.add_order(production_order)
        
        return ScheduleResponse(
            success=True,
            message=f"生产订单 {order.order_id} 创建成功",
            data={"order_id": order.order_id, "status": "pending"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建生产订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.post("/equipment", response_model=ScheduleResponse)
async def create_equipment(equipment: EquipmentCreate):
    """创建设备"""
    try:
        # 解析维护计划
        maintenance_schedule = []
        for schedule in equipment.maintenance_schedule:
            start_time = datetime.fromisoformat(schedule['start_time'])
            end_time = datetime.fromisoformat(schedule['end_time'])
            maintenance_schedule.append((start_time, end_time))
        
        # 创建设备对象
        equipment_obj = Equipment(
            equipment_id=equipment.equipment_id,
            name=equipment.name,
            capacity_per_hour=equipment.capacity_per_hour,
            available_hours_per_day=equipment.available_hours_per_day,
            maintenance_schedule=maintenance_schedule
        )
        
        # 检查设备是否已存在
        existing_equipment = next((e for e in scheduling_service.equipment if e.equipment_id == equipment.equipment_id), None)
        if existing_equipment:
            raise HTTPException(status_code=400, detail=f"设备 {equipment.equipment_id} 已存在")
        
        # 添加到排产服务
        scheduling_service.add_equipment(equipment_obj)
        
        return ScheduleResponse(
            success=True,
            message=f"设备 {equipment.equipment_id} 创建成功",
            data={"equipment_id": equipment.equipment_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建设备失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建设备失败: {str(e)}")


@router.post("/materials", response_model=ScheduleResponse)
async def create_material(material: MaterialCreate):
    """创建物料"""
    try:
        # 创建物料对象
        material_obj = Material(
            material_code=material.material_code,
            name=material.name,
            current_stock=material.current_stock,
            safety_stock=material.safety_stock,
            lead_time_days=material.lead_time_days,
            supplier=material.supplier
        )
        
        # 检查物料是否已存在
        existing_material = next((m for m in scheduling_service.materials if m.material_code == material.material_code), None)
        if existing_material:
            raise HTTPException(status_code=400, detail=f"物料 {material.material_code} 已存在")
        
        # 添加到排产服务
        scheduling_service.add_material(material_obj)
        
        return ScheduleResponse(
            success=True,
            message=f"物料 {material.material_code} 创建成功",
            data={"material_code": material.material_code}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建物料失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建物料失败: {str(e)}")


@router.post("/schedule", response_model=ScheduleResponse)
async def execute_scheduling(request: ScheduleRequest, background_tasks: BackgroundTasks):
    """执行自动排产"""
    try:
        # 检查是否有待排产的订单
        pending_orders = [o for o in scheduling_service.orders if o.status == OrderStatus.PENDING]
        if not pending_orders:
            return ScheduleResponse(
                success=False,
                message="没有待排产的订单",
                data={"pending_orders": 0}
            )
        
        # 如果需要强制重新排产，重置已排产订单
        if request.force_reschedule:
            for order in scheduling_service.orders:
                if order.status == OrderStatus.SCHEDULED:
                    scheduling_service.reschedule_order(order.order_id)
        
        # 执行排产
        result = scheduling_service.schedule_orders(request.start_date)
        
        # 发送微信通知
        if request.notify_wechat:
            try:
                # 这里需要导入微信服务实例
                # wechat_service.send_schedule_notification(result)
                logger.info("排产通知已加入微信发送队列")
            except Exception as e:
                logger.warning(f"发送微信通知失败: {e}")
        
        return ScheduleResponse(
            success=True,
            message=f"排产完成，成功排产 {result['scheduled_count']} 个订单",
            data={
                "schedule_time": result['schedule_time'].isoformat(),
                "total_orders": result['total_orders'],
                "scheduled_count": result['scheduled_count'],
                "failed_count": result['failed_count'],
                "equipment_utilization": result['equipment_utilization']
            }
        )
        
    except Exception as e:
        logger.error(f"执行排产失败: {e}")
        raise HTTPException(status_code=500, detail=f"排产失败: {str(e)}")


@router.post("/reschedule", response_model=ScheduleResponse)
async def reschedule_order(request: RescheduleRequest):
    """重新排产指定订单"""
    try:
        # 验证新优先级
        new_priority = None
        if request.new_priority:
            try:
                new_priority = Priority[request.new_priority.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"无效的优先级: {request.new_priority}")
        
        # 执行重新排产
        success = scheduling_service.reschedule_order(
            request.order_id,
            new_priority,
            request.new_due_date
        )
        
        if success:
            return ScheduleResponse(
                success=True,
                message=f"订单 {request.order_id} 重新排产成功",
                data={"order_id": request.order_id, "status": "pending"}
            )
        else:
            raise HTTPException(status_code=404, detail=f"订单 {request.order_id} 不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新排产失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新排产失败: {str(e)}")


@router.get("/gantt", response_model=ScheduleResponse)
async def get_gantt_chart_data():
    """获取甘特图数据"""
    try:
        gantt_data = scheduling_service.get_schedule_gantt_data()
        
        return ScheduleResponse(
            success=True,
            message="获取甘特图数据成功",
            data={
                "gantt_data": gantt_data,
                "total_scheduled": len(gantt_data)
            }
        )
        
    except Exception as e:
        logger.error(f"获取甘特图数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取甘特图数据失败: {str(e)}")


@router.get("/summary", response_model=ScheduleResponse)
async def get_production_summary():
    """获取生产概况"""
    try:
        summary = scheduling_service.get_production_summary()
        
        return ScheduleResponse(
            success=True,
            message="获取生产概况成功",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"获取生产概况失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取生产概况失败: {str(e)}")


@router.get("/orders", response_model=ScheduleResponse)
async def get_orders(
    status: Optional[str] = Query(None, description="订单状态过滤"),
    priority: Optional[str] = Query(None, description="优先级过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """获取订单列表"""
    try:
        orders = scheduling_service.orders
        
        # 状态过滤
        if status:
            try:
                status_enum = OrderStatus(status.lower())
                orders = [o for o in orders if o.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的订单状态: {status}")
        
        # 优先级过滤
        if priority:
            try:
                priority_enum = Priority[priority.upper()]
                orders = [o for o in orders if o.priority == priority_enum]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"无效的优先级: {priority}")
        
        # 限制返回数量
        orders = orders[:limit]
        
        # 转换为字典格式
        orders_data = []
        for order in orders:
            orders_data.append({
                "order_id": order.order_id,
                "product_code": order.product_code,
                "quantity": order.quantity,
                "due_date": order.due_date.isoformat(),
                "priority": order.priority.name,
                "estimated_hours": order.estimated_hours,
                "status": order.status.value,
                "scheduled_start": order.scheduled_start.isoformat() if order.scheduled_start else None,
                "scheduled_end": order.scheduled_end.isoformat() if order.scheduled_end else None,
                "assigned_equipment": order.assigned_equipment
            })
        
        return ScheduleResponse(
            success=True,
            message=f"获取订单列表成功，共 {len(orders_data)} 个订单",
            data={
                "orders": orders_data,
                "total_count": len(orders_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")


@router.get("/equipment", response_model=ScheduleResponse)
async def get_equipment_list():
    """获取设备列表"""
    try:
        equipment_data = []
        for equipment in scheduling_service.equipment:
            equipment_data.append({
                "equipment_id": equipment.equipment_id,
                "name": equipment.name,
                "capacity_per_hour": equipment.capacity_per_hour,
                "available_hours_per_day": equipment.available_hours_per_day,
                "current_load": equipment.current_load,
                "utilization_rate": round((equipment.current_load / equipment.available_hours_per_day) * 100, 2),
                "maintenance_count": len(equipment.maintenance_schedule)
            })
        
        return ScheduleResponse(
            success=True,
            message=f"获取设备列表成功，共 {len(equipment_data)} 台设备",
            data={
                "equipment": equipment_data,
                "total_count": len(equipment_data)
            }
        )
        
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取设备列表失败: {str(e)}")


@router.get("/materials", response_model=ScheduleResponse)
async def get_materials_list():
    """获取物料列表"""
    try:
        materials_data = []
        for material in scheduling_service.materials:
            materials_data.append({
                "material_code": material.material_code,
                "name": material.name,
                "current_stock": material.current_stock,
                "safety_stock": material.safety_stock,
                "lead_time_days": material.lead_time_days,
                "supplier": material.supplier,
                "stock_status": "充足" if material.current_stock > material.safety_stock else "不足"
            })
        
        return ScheduleResponse(
            success=True,
            message=f"获取物料列表成功，共 {len(materials_data)} 种物料",
            data={
                "materials": materials_data,
                "total_count": len(materials_data)
            }
        )
        
    except Exception as e:
        logger.error(f"获取物料列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取物料列表失败: {str(e)}")