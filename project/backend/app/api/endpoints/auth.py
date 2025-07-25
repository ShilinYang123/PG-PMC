from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User, UserSession, UserLoginLog, UserStatus
from app.schemas.auth import Token, UserLogin, UserInfo
from app.schemas.common import ResponseModel
import jwt
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token():
    """创建刷新令牌"""
    return secrets.token_urlsafe(32)

def verify_token(token: str):
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已被锁定",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户账户未激活")
    return current_user

def authenticate_user(db: Session, username: str, password: str):
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    
    # 这里应该使用密码哈希验证
    # if not user.check_password(password):
    #     return False
    
    # 临时简单验证（实际应用中应该使用加密密码）
    if user.hashed_password != password:
        return False
    
    return user

def create_user_session(db: Session, user: User, ip_address: str = None, user_agent: str = None):
    """创建用户会话"""
    session_id = secrets.token_urlsafe(32)
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token()
    
    session = UserSession(
        user_id=user.id,
        username=user.username,
        session_id=session_id,
        token=access_token,
        refresh_token=refresh_token,
        login_time=datetime.now(),
        last_activity=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

def log_user_login(db: Session, user: User, result: str, ip_address: str = None, user_agent: str = None, failure_reason: str = None):
    """记录用户登录日志"""
    log = UserLoginLog(
        user_id=user.id if user else None,
        username=user.username if user else "unknown",
        login_time=datetime.now(),
        login_result=result,
        failure_reason=failure_reason,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(log)
    db.commit()

@router.post("/login", response_model=ResponseModel[Token])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 验证用户
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # 记录登录失败
            log_user_login(db, None, "失败", failure_reason="用户名或密码错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if not user.is_active or user.status != UserStatus.ACTIVE:
            log_user_login(db, user, "失败", failure_reason="账户已被禁用")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用"
            )
        
        if user.is_account_locked():
            log_user_login(db, user, "失败", failure_reason="账户已被锁定")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被锁定"
            )
        
        # 创建会话
        session = create_user_session(db, user)
        
        # 更新用户登录信息
        user.last_login_at = datetime.now()
        user.login_count += 1
        user.failed_login_count = 0  # 重置失败次数
        db.commit()
        
        # 记录登录成功
        log_user_login(db, user, "成功")
        
        token_data = Token(
            access_token=session.token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return ResponseModel(
            code=200,
            message="登录成功",
            data=token_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务异常"
        )

@router.post("/logout", response_model=ResponseModel[dict])
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """用户登出"""
    try:
        # 查找并停用用户会话
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).all()
        
        for session in sessions:
            session.is_active = False
            session.logout_time = datetime.now()
            session.logout_reason = "用户主动登出"
        
        db.commit()
        
        return ResponseModel(
            code=200,
            message="登出成功",
            data={}
        )
        
    except Exception as e:
        logger.error(f"登出异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出服务异常"
        )

@router.post("/refresh", response_model=ResponseModel[Token])
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """刷新令牌"""
    try:
        # 查找会话
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        ).first()
        
        if not session or session.is_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期"
            )
        
        # 获取用户
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        new_access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token()
        
        # 更新会话
        session.token = new_access_token
        session.refresh_token = new_refresh_token
        session.last_activity = datetime.now()
        session.expires_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        db.commit()
        
        token_data = Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        return ResponseModel(
            code=200,
            message="令牌刷新成功",
            data=token_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新令牌异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌服务异常"
        )

@router.get("/me", response_model=ResponseModel[UserInfo])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
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
            message="获取用户信息成功",
            data=user_info
        )
        
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息服务异常"
        )