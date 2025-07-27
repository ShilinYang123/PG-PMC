from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.common import ResponseModel, PagedResponseModel, QueryParams, PageInfo
from app.schemas.auth import UserInfo, UserProfile
from app.api.endpoints.auth import get_current_user, get_current_active_user
from app.schemas.user import UserCreate, UserUpdate, UserQuery, UserDetail
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def check_admin_permission(current_user: User = Depends(get_current_user)):
    """检查管理员权限"""
    if not current_user.is_superuser and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

@router.get("/", response_model=PagedResponseModel[UserDetail])
async def get_users(
    query: UserQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """获取用户列表"""
    try:
        # 构建查询条件
        filters = []
        
        if query.keyword:
            filters.append(
                or_(
                    User.username.contains(query.keyword),
                    User.full_name.contains(query.keyword),
                    User.email.contains(query.keyword),
                    User.employee_id.contains(query.keyword)
                )
            )
        
        if query.role:
            filters.append(User.role == query.role)
        
        if query.status:
            filters.append(User.status == query.status)
        
        if query.department:
            filters.append(User.department == query.department)
        
        if query.workshop:
            filters.append(User.workshop == query.workshop)
        
        if query.is_active is not None:
            filters.append(User.is_active == query.is_active)
        
        # 构建基础查询
        base_query = db.query(User)
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # 获取总数
        total = base_query.count()
        
        # 排序
        if query.sort_field:
            sort_column = getattr(User, query.sort_field, None)
            if sort_column:
                if query.sort_order == "desc":
                    base_query = base_query.order_by(sort_column.desc())
                else:
                    base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(User.created_at.desc())
        
        # 分页
        offset = (query.page - 1) * query.page_size
        users = base_query.offset(offset).limit(query.page_size).all()
        
        # 转换为响应模型
        user_details = []
        for user in users:
            user_detail = UserDetail(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                full_name=user.full_name,
                employee_id=user.employee_id,
                department=user.department,
                position=user.position,
                role=user.role,
                status=user.status,
                is_active=user.is_active,
                workshop=user.workshop,
                team=user.team,
                last_login_at=user.last_login_at,
                login_count=user.login_count,
                created_at=user.created_at,
                updated_at=user.updated_at,
                created_by=user.created_by
            )
            user_details.append(user_detail)
        
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
            message="获取用户列表成功",
            data=user_details,
            page_info=page_info
        )
        
    except Exception as e:
        logger.error(f"获取用户列表异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表服务异常"
        )

@router.get("/{user_id}", response_model=ResponseModel[UserDetail])
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户详情"""
    try:
        # 检查权限：只能查看自己的信息或管理员可以查看所有用户
        if user_id != current_user.id and not current_user.is_superuser and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_detail = UserDetail(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            employee_id=user.employee_id,
            department=user.department,
            position=user.position,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            workshop=user.workshop,
            team=user.team,
            supervisor_id=user.supervisor_id,
            address=user.address,
            emergency_contact=user.emergency_contact,
            emergency_phone=user.emergency_phone,
            avatar=user.avatar,
            timezone=user.timezone,
            language=user.language,
            theme=user.theme,
            permissions=user.get_permissions(),
            last_login_at=user.last_login_at,
            login_count=user.login_count,
            failed_login_count=user.failed_login_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
            created_by=user.created_by,
            updated_by=user.updated_by,
            remark=user.remark
        )
        
        return ResponseModel(
            code=200,
            message="获取用户详情成功",
            data=user_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情服务异常"
        )

@router.post("/", response_model=ResponseModel[UserDetail])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """创建用户"""
    try:
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )
        
        # 检查工号是否已存在
        if user_data.employee_id:
            existing_employee = db.query(User).filter(User.employee_id == user_data.employee_id).first()
            if existing_employee:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="工号已存在"
                )
        
        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,
            employee_id=user_data.employee_id,
            department=user_data.department,
            position=user_data.position,
            role=user_data.role,
            status=user_data.status or UserStatus.ACTIVE,
            is_active=user_data.is_active if user_data.is_active is not None else True,
            workshop=user_data.workshop,
            team=user_data.team,
            supervisor_id=user_data.supervisor_id,
            address=user_data.address,
            emergency_contact=user_data.emergency_contact,
            emergency_phone=user_data.emergency_phone,
            timezone=user_data.timezone or "Asia/Shanghai",
            language=user_data.language or "zh-CN",
            theme=user_data.theme or "light",
            remark=user_data.remark,
            created_by=current_user.username,
            updated_by=current_user.username
        )
        
        # 设置密码（实际应用中应该使用加密）
        user.hashed_password = user_data.password
        user.password_changed_at = datetime.now()
        
        # 设置权限
        if user_data.permissions:
            user.set_permissions(user_data.permissions)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        user_detail = UserDetail(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            employee_id=user.employee_id,
            department=user.department,
            position=user.position,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            workshop=user.workshop,
            team=user.team,
            created_at=user.created_at,
            created_by=user.created_by
        )
        
        return ResponseModel(
            code=200,
            message="创建用户成功",
            data=user_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户服务异常"
        )

@router.put("/{user_id}", response_model=ResponseModel[UserDetail])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户"""
    try:
        # 检查权限：只能更新自己的信息或管理员可以更新所有用户
        if user_id != current_user.id and not current_user.is_superuser and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "permissions":
                user.set_permissions(value)
            else:
                setattr(user, field, value)
        
        user.updated_by = current_user.username
        user.updated_at = datetime.now()
        
        db.commit()
        db.refresh(user)
        
        user_detail = UserDetail(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            employee_id=user.employee_id,
            department=user.department,
            position=user.position,
            role=user.role,
            status=user.status,
            is_active=user.is_active,
            workshop=user.workshop,
            team=user.team,
            updated_at=user.updated_at,
            updated_by=user.updated_by
        )
        
        return ResponseModel(
            code=200,
            message="更新用户成功",
            data=user_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户服务异常"
        )

@router.delete("/{user_id}", response_model=ResponseModel[dict])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """删除用户"""
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        db.delete(user)
        db.commit()
        
        return ResponseModel(
            code=200,
            message="删除用户成功",
            data={}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户服务异常"
        )

@router.put("/profile", response_model=ResponseModel[UserInfo])
async def update_profile(
    profile_data: UserProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新个人资料"""
    try:
        # 更新字段
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.now()
        
        db.commit()
        db.refresh(current_user)
        
        user_info = UserInfo(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            employee_id=current_user.employee_id,
            department=current_user.department,
            position=current_user.position,
            role=current_user.role,
            workshop=current_user.workshop,
            avatar=current_user.avatar,
            permissions=current_user.get_permissions(),
            last_login_at=current_user.last_login_at
        )
        
        return ResponseModel(
            code=200,
            message="更新个人资料成功",
            data=user_info
        )
        
    except Exception as e:
        logger.error(f"更新个人资料异常: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新个人资料服务异常"
        )