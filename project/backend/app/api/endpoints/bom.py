"""BOM管理API端点

提供BOM(物料清单)管理的REST API接口：
- BOM创建、查询、更新、删除
- BOM明细管理
- BOM版本控制
- BOM成本计算
- BOM导入导出
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from loguru import logger

from ...database import get_db
from ...models.material import BOM, BOMItem, Material
from ...schemas.base import BaseResponse, PaginatedResponse
from ...core.auth import get_current_user
from ...models.user import User
from pydantic import BaseModel, Field
from typing import Union

router = APIRouter(prefix="/bom", tags=["BOM管理"])


# BOM相关的Pydantic模型
class BOMItemCreate(BaseModel):
    """BOM明细创建模型"""
    material_id: int = Field(..., description="物料ID")
    quantity: float = Field(..., gt=0, description="用量")
    unit: str = Field(..., max_length=20, description="单位")
    loss_rate: float = Field(0, ge=0, le=100, description="损耗率(%)")
    level: int = Field(1, ge=1, description="层级")
    parent_item_id: Optional[int] = Field(None, description="父级明细ID")
    is_substitute: bool = Field(False, description="是否替代料")
    substitute_group: Optional[str] = Field(None, max_length=50, description="替代组")
    remark: Optional[str] = Field(None, description="备注")


class BOMCreate(BaseModel):
    """BOM创建模型"""
    bom_code: str = Field(..., max_length=50, description="BOM编码")
    product_name: str = Field(..., max_length=100, description="产品名称")
    product_model: Optional[str] = Field(None, max_length=50, description="产品型号")
    version: str = Field(..., max_length=20, description="版本号")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    expiry_date: Optional[datetime] = Field(None, description="失效日期")
    description: Optional[str] = Field(None, description="描述")
    remark: Optional[str] = Field(None, description="备注")
    items: List[BOMItemCreate] = Field([], description="BOM明细列表")


class BOMUpdate(BaseModel):
    """BOM更新模型"""
    product_name: Optional[str] = Field(None, max_length=100, description="产品名称")
    product_model: Optional[str] = Field(None, max_length=50, description="产品型号")
    version: Optional[str] = Field(None, max_length=20, description="版本号")
    is_active: Optional[bool] = Field(None, description="是否启用")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    expiry_date: Optional[datetime] = Field(None, description="失效日期")
    description: Optional[str] = Field(None, description="描述")
    remark: Optional[str] = Field(None, description="备注")


class BOMItemUpdate(BaseModel):
    """BOM明细更新模型"""
    quantity: Optional[float] = Field(None, gt=0, description="用量")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    loss_rate: Optional[float] = Field(None, ge=0, le=100, description="损耗率(%)")
    level: Optional[int] = Field(None, ge=1, description="层级")
    parent_item_id: Optional[int] = Field(None, description="父级明细ID")
    is_substitute: Optional[bool] = Field(None, description="是否替代料")
    substitute_group: Optional[str] = Field(None, max_length=50, description="替代组")
    remark: Optional[str] = Field(None, description="备注")


class BOMResponse(BaseModel):
    """BOM响应模型"""
    id: int
    bom_code: str
    product_name: str
    product_model: Optional[str]
    version: str
    is_active: bool
    effective_date: Optional[datetime]
    expiry_date: Optional[datetime]
    description: Optional[str]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    items_count: int = 0
    total_cost: float = 0.0

    class Config:
        from_attributes = True


class BOMItemResponse(BaseModel):
    """BOM明细响应模型"""
    id: int
    bom_id: int
    material_id: int
    material_code: str
    material_name: str
    quantity: float
    unit: str
    loss_rate: float
    level: int
    parent_item_id: Optional[int]
    is_substitute: bool
    substitute_group: Optional[str]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime
    unit_cost: float = 0.0
    total_cost: float = 0.0

    class Config:
        from_attributes = True


@router.get("/", response_model=PaginatedResponse[BOMResponse])
async def get_bom_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索(BOM编码、产品名称)"),
    product_name: Optional[str] = Query(None, description="产品名称"),
    version: Optional[str] = Query(None, description="版本号"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方式"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取BOM列表"""
    try:
        # 构建查询
        query = db.query(BOM)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    BOM.bom_code.ilike(f"%{keyword}%"),
                    BOM.product_name.ilike(f"%{keyword}%")
                )
            )
        
        # 产品名称过滤
        if product_name:
            query = query.filter(BOM.product_name.ilike(f"%{product_name}%"))
        
        # 版本过滤
        if version:
            query = query.filter(BOM.version == version)
        
        # 状态过滤
        if is_active is not None:
            query = query.filter(BOM.is_active == is_active)
        
        # 排序
        if hasattr(BOM, sort_by):
            if sort_order == "desc":
                query = query.order_by(getattr(BOM, sort_by).desc())
            else:
                query = query.order_by(getattr(BOM, sort_by))
        
        # 分页
        total = query.count()
        offset = (page - 1) * size
        boms = query.offset(offset).limit(size).all()
        
        # 计算每个BOM的明细数量和总成本
        bom_list = []
        for bom in boms:
            # 计算明细数量
            items_count = db.query(BOMItem).filter(BOMItem.bom_id == bom.id).count()
            
            # 计算总成本
            total_cost = db.query(
                func.sum(BOMItem.quantity * Material.unit_price)
            ).join(
                Material, BOMItem.material_id == Material.id
            ).filter(
                BOMItem.bom_id == bom.id
            ).scalar() or 0.0
            
            bom_data = BOMResponse.from_orm(bom)
            bom_data.items_count = items_count
            bom_data.total_cost = total_cost
            bom_list.append(bom_data)
        
        return PaginatedResponse(
            code=200,
            message="获取BOM列表成功",
            data={
                "items": bom_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        )
        
    except Exception as e:
        logger.error(f"获取BOM列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BOM列表失败")


@router.get("/{bom_id}", response_model=BaseResponse[BOMResponse])
async def get_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取BOM详情"""
    try:
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 计算明细数量和总成本
        items_count = db.query(BOMItem).filter(BOMItem.bom_id == bom.id).count()
        total_cost = db.query(
            func.sum(BOMItem.quantity * Material.unit_price)
        ).join(
            Material, BOMItem.material_id == Material.id
        ).filter(
            BOMItem.bom_id == bom.id
        ).scalar() or 0.0
        
        bom_data = BOMResponse.from_orm(bom)
        bom_data.items_count = items_count
        bom_data.total_cost = total_cost
        
        return BaseResponse(
            code=200,
            message="获取BOM详情成功",
            data=bom_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取BOM详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BOM详情失败")


@router.post("/", response_model=BaseResponse[BOMResponse])
async def create_bom(
    bom_data: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建BOM"""
    try:
        # 检查BOM编码是否重复
        existing_bom = db.query(BOM).filter(BOM.bom_code == bom_data.bom_code).first()
        if existing_bom:
            raise HTTPException(status_code=400, detail="BOM编码已存在")
        
        # 创建BOM
        bom = BOM(
            bom_code=bom_data.bom_code,
            product_name=bom_data.product_name,
            product_model=bom_data.product_model,
            version=bom_data.version,
            effective_date=bom_data.effective_date,
            expiry_date=bom_data.expiry_date,
            description=bom_data.description,
            remark=bom_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        db.add(bom)
        db.flush()  # 获取BOM ID
        
        # 创建BOM明细
        for item_data in bom_data.items:
            # 检查物料是否存在
            material = db.query(Material).filter(Material.id == item_data.material_id).first()
            if not material:
                raise HTTPException(status_code=400, detail=f"物料ID {item_data.material_id} 不存在")
            
            bom_item = BOMItem(
                bom_id=bom.id,
                material_id=item_data.material_id,
                material_code=material.material_code,
                material_name=material.material_name,
                quantity=item_data.quantity,
                unit=item_data.unit,
                loss_rate=item_data.loss_rate,
                level=item_data.level,
                parent_item_id=item_data.parent_item_id,
                is_substitute=item_data.is_substitute,
                substitute_group=item_data.substitute_group,
                remark=item_data.remark
            )
            db.add(bom_item)
        
        db.commit()
        db.refresh(bom)
        
        # 计算明细数量和总成本
        items_count = len(bom_data.items)
        total_cost = sum(
            item.quantity * db.query(Material).filter(Material.id == item.material_id).first().unit_price
            for item in bom_data.items
        )
        
        bom_response = BOMResponse.from_orm(bom)
        bom_response.items_count = items_count
        bom_response.total_cost = total_cost
        
        return BaseResponse(
            code=201,
            message="创建BOM成功",
            data=bom_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建BOM失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建BOM失败")


@router.put("/{bom_id}", response_model=BaseResponse[BOMResponse])
async def update_bom(
    bom_id: int,
    bom_data: BOMUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新BOM"""
    try:
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 更新字段
        update_data = bom_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bom, field, value)
        
        bom.updated_by = current_user.username
        
        db.commit()
        db.refresh(bom)
        
        # 计算明细数量和总成本
        items_count = db.query(BOMItem).filter(BOMItem.bom_id == bom.id).count()
        total_cost = db.query(
            func.sum(BOMItem.quantity * Material.unit_price)
        ).join(
            Material, BOMItem.material_id == Material.id
        ).filter(
            BOMItem.bom_id == bom.id
        ).scalar() or 0.0
        
        bom_response = BOMResponse.from_orm(bom)
        bom_response.items_count = items_count
        bom_response.total_cost = total_cost
        
        return BaseResponse(
            code=200,
            message="更新BOM成功",
            data=bom_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新BOM失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新BOM失败")


@router.delete("/{bom_id}", response_model=BaseResponse[Dict[str, Any]])
async def delete_bom(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除BOM"""
    try:
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 删除BOM明细
        db.query(BOMItem).filter(BOMItem.bom_id == bom_id).delete()
        
        # 删除BOM
        db.delete(bom)
        db.commit()
        
        return BaseResponse(
            code=200,
            message="删除BOM成功",
            data={"deleted_id": bom_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除BOM失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除BOM失败")


@router.get("/{bom_id}/items", response_model=PaginatedResponse[BOMItemResponse])
async def get_bom_items(
    bom_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页数量"),
    level: Optional[int] = Query(None, description="层级过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取BOM明细列表"""
    try:
        # 检查BOM是否存在
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 构建查询
        query = db.query(BOMItem).filter(BOMItem.bom_id == bom_id)
        
        # 层级过滤
        if level is not None:
            query = query.filter(BOMItem.level == level)
        
        # 排序
        query = query.order_by(BOMItem.level, BOMItem.id)
        
        # 分页
        total = query.count()
        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()
        
        # 计算每个明细的成本
        item_list = []
        for item in items:
            material = db.query(Material).filter(Material.id == item.material_id).first()
            unit_cost = material.unit_price if material else 0.0
            total_cost = item.quantity * unit_cost
            
            item_data = BOMItemResponse.from_orm(item)
            item_data.unit_cost = unit_cost
            item_data.total_cost = total_cost
            item_list.append(item_data)
        
        return PaginatedResponse(
            code=200,
            message="获取BOM明细列表成功",
            data={
                "items": item_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取BOM明细列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BOM明细列表失败")


@router.post("/{bom_id}/items", response_model=BaseResponse[BOMItemResponse])
async def add_bom_item(
    bom_id: int,
    item_data: BOMItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加BOM明细"""
    try:
        # 检查BOM是否存在
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 检查物料是否存在
        material = db.query(Material).filter(Material.id == item_data.material_id).first()
        if not material:
            raise HTTPException(status_code=400, detail="物料不存在")
        
        # 检查是否已存在相同物料
        existing_item = db.query(BOMItem).filter(
            and_(
                BOMItem.bom_id == bom_id,
                BOMItem.material_id == item_data.material_id,
                BOMItem.level == item_data.level
            )
        ).first()
        if existing_item:
            raise HTTPException(status_code=400, detail="该层级已存在相同物料")
        
        # 创建BOM明细
        bom_item = BOMItem(
            bom_id=bom_id,
            material_id=item_data.material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            quantity=item_data.quantity,
            unit=item_data.unit,
            loss_rate=item_data.loss_rate,
            level=item_data.level,
            parent_item_id=item_data.parent_item_id,
            is_substitute=item_data.is_substitute,
            substitute_group=item_data.substitute_group,
            remark=item_data.remark
        )
        
        db.add(bom_item)
        db.commit()
        db.refresh(bom_item)
        
        # 计算成本
        unit_cost = material.unit_price
        total_cost = bom_item.quantity * unit_cost
        
        item_response = BOMItemResponse.from_orm(bom_item)
        item_response.unit_cost = unit_cost
        item_response.total_cost = total_cost
        
        return BaseResponse(
            code=201,
            message="添加BOM明细成功",
            data=item_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"添加BOM明细失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加BOM明细失败")


@router.put("/items/{item_id}", response_model=BaseResponse[BOMItemResponse])
async def update_bom_item(
    item_id: int,
    item_data: BOMItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新BOM明细"""
    try:
        bom_item = db.query(BOMItem).filter(BOMItem.id == item_id).first()
        if not bom_item:
            raise HTTPException(status_code=404, detail="BOM明细不存在")
        
        # 更新字段
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bom_item, field, value)
        
        db.commit()
        db.refresh(bom_item)
        
        # 计算成本
        material = db.query(Material).filter(Material.id == bom_item.material_id).first()
        unit_cost = material.unit_price if material else 0.0
        total_cost = bom_item.quantity * unit_cost
        
        item_response = BOMItemResponse.from_orm(bom_item)
        item_response.unit_cost = unit_cost
        item_response.total_cost = total_cost
        
        return BaseResponse(
            code=200,
            message="更新BOM明细成功",
            data=item_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新BOM明细失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新BOM明细失败")


@router.delete("/items/{item_id}", response_model=BaseResponse[Dict[str, Any]])
async def delete_bom_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除BOM明细"""
    try:
        bom_item = db.query(BOMItem).filter(BOMItem.id == item_id).first()
        if not bom_item:
            raise HTTPException(status_code=404, detail="BOM明细不存在")
        
        db.delete(bom_item)
        db.commit()
        
        return BaseResponse(
            code=200,
            message="删除BOM明细成功",
            data={"deleted_id": item_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除BOM明细失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除BOM明细失败")


@router.get("/{bom_id}/cost-analysis", response_model=BaseResponse[Dict[str, Any]])
async def get_bom_cost_analysis(
    bom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取BOM成本分析"""
    try:
        # 检查BOM是否存在
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM不存在")
        
        # 获取BOM明细和物料信息
        items = db.query(BOMItem, Material).join(
            Material, BOMItem.material_id == Material.id
        ).filter(BOMItem.bom_id == bom_id).all()
        
        total_cost = 0.0
        cost_by_category = {}
        cost_by_level = {}
        item_details = []
        
        for bom_item, material in items:
            item_cost = bom_item.quantity * material.unit_price
            total_cost += item_cost
            
            # 按类别统计
            category = material.category.value if material.category else "未分类"
            if category not in cost_by_category:
                cost_by_category[category] = 0.0
            cost_by_category[category] += item_cost
            
            # 按层级统计
            level = bom_item.level
            if level not in cost_by_level:
                cost_by_level[level] = 0.0
            cost_by_level[level] += item_cost
            
            # 明细信息
            item_details.append({
                "material_code": material.material_code,
                "material_name": material.material_name,
                "quantity": bom_item.quantity,
                "unit": bom_item.unit,
                "unit_price": material.unit_price,
                "total_cost": item_cost,
                "level": bom_item.level,
                "category": category
            })
        
        return BaseResponse(
            code=200,
            message="获取BOM成本分析成功",
            data={
                "bom_info": {
                    "bom_code": bom.bom_code,
                    "product_name": bom.product_name,
                    "version": bom.version
                },
                "total_cost": total_cost,
                "cost_by_category": cost_by_category,
                "cost_by_level": cost_by_level,
                "item_count": len(items),
                "item_details": item_details
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取BOM成本分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BOM成本分析失败")


@router.get("/stats", response_model=BaseResponse[Dict[str, Any]])
async def get_bom_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取BOM统计信息"""
    try:
        # 总BOM数量
        total_boms = db.query(BOM).count()
        
        # 启用的BOM数量
        active_boms = db.query(BOM).filter(BOM.is_active == True).count()
        
        # 本月新增BOM数量
        from datetime import datetime, timedelta
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_boms_this_month = db.query(BOM).filter(BOM.created_at >= month_start).count()
        
        # 按产品名称分组统计
        product_stats = db.query(
            BOM.product_name,
            func.count(BOM.id).label('count')
        ).group_by(BOM.product_name).all()
        
        # 版本统计
        version_stats = db.query(
            BOM.version,
            func.count(BOM.id).label('count')
        ).group_by(BOM.version).all()
        
        return BaseResponse(
            code=200,
            message="获取BOM统计信息成功",
            data={
                "total_boms": total_boms,
                "active_boms": active_boms,
                "inactive_boms": total_boms - active_boms,
                "new_boms_this_month": new_boms_this_month,
                "product_stats": [{
                    "product_name": stat.product_name,
                    "count": stat.count
                } for stat in product_stats],
                "version_stats": [{
                    "version": stat.version,
                    "count": stat.count
                } for stat in version_stats]
            }
        )
        
    except Exception as e:
        logger.error(f"获取BOM统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BOM统计信息失败")