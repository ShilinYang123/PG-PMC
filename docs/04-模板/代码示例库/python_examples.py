#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python代码示例库 - 3AI工作室
提供常用的Python代码模板，包括数据处理、Web开发、异步编程等
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import wraps, lru_cache, partial
from pathlib import Path
from typing import (
    Any, Dict, List, Optional, Union, Callable,
    TypeVar, Generic, Protocol, Literal
)
from urllib.parse import urljoin, urlparse

import requests
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ================================
# 配置和常量
# ================================


class Config:
    """应用配置类"""
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class StatusCode(Enum):
    """状态码枚举"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# ================================
# 数据类和类型定义
# ================================


@dataclass
class User:
    """用户数据类"""
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """数据验证"""
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")
        if not self.name.strip():
            raise ValueError("Name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """从字典创建用户"""
        return cls(
            id=data['id'],
            name=data['name'],
            email=data['email'],
            created_at=datetime.fromisoformat(
                data.get(
                    'created_at',
                    datetime.now().isoformat())),
            is_active=data.get(
                'is_active',
                True),
            metadata=data.get(
                'metadata',
                {}))


Response = namedtuple('Response', ['status_code', 'data', 'message'])

# 泛型类型
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class Repository(Protocol[T]):
    """仓储模式协议"""

    def get(self, id: int) -> Optional[T]: ...
    def create(self, entity: T) -> T: ...
    def update(self, entity: T) -> T: ...
    def delete(self, id: int) -> bool: ...
    def list(self, limit: int = 10, offset: int = 0) -> List[T]: ...

# ================================
# 装饰器
# ================================


def timer(func: Callable) -> Callable:
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.4f}秒")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise e

                    print(f"第{attempts}次尝试失败: {e}, {current_delay}秒后重试")
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None
        return wrapper
    return decorator


def validate_types(**type_hints):
    """类型验证装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 验证参数类型
            for param_name, expected_type in type_hints.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"参数 {param_name} 期望类型 {expected_type.__name__}, "
                            f"实际类型 {type(value).__name__}"
                        )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """结果缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)

            return result

        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    return decorator


def singleton(cls):
    """单例装饰器"""
    instances = {}
    lock = threading.Lock()

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper

# ================================
# 异常处理
# ================================


class BaseError(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: str = None, details: Dict = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(BaseError):
    """验证错误"""
    pass


class NotFoundError(BaseError):
    """资源未找到错误"""
    pass


class DatabaseError(BaseError):
    """数据库错误"""
    pass


def handle_exceptions(func: Callable) -> Callable:
    """异常处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logging.error(f"验证错误: {e}")
            return Response(StatusCode.BAD_REQUEST.value, None, str(e))
        except NotFoundError as e:
            logging.error(f"资源未找到: {e}")
            return Response(StatusCode.NOT_FOUND.value, None, str(e))
        except Exception as e:
            logging.error(f"未知错误: {e}")
            return Response(StatusCode.INTERNAL_ERROR.value, None, "内部服务器错误")

    return wrapper

# ================================
# 数据库操作
# ================================


Base = declarative_base()


class UserModel(Base):
    """用户数据库模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """执行查询"""
        with self.get_session() as session:
            result = session.execute(query, params or {})
            return [dict(row) for row in result]

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception:
            return False


class UserRepository:
    """用户仓储"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get(self, user_id: int) -> Optional[User]:
        """获取用户"""
        with self.db_manager.get_session() as session:
            user_model = session.query(UserModel).filter(
                UserModel.id == user_id).first()
            if user_model:
                return User(
                    id=user_model.id,
                    name=user_model.name,
                    email=user_model.email,
                    created_at=user_model.created_at
                )
            return None

    def create(self, user: User) -> User:
        """创建用户"""
        with self.db_manager.get_session() as session:
            user_model = UserModel(
                name=user.name,
                email=user.email
            )
            session.add(user_model)
            session.flush()
            user.id = user_model.id
            return user

    def update(self, user: User) -> User:
        """更新用户"""
        with self.db_manager.get_session() as session:
            user_model = session.query(UserModel).filter(
                UserModel.id == user.id).first()
            if not user_model:
                raise NotFoundError(f"用户 {user.id} 不存在")

            user_model.name = user.name
            user_model.email = user.email
            return user

    def delete(self, user_id: int) -> bool:
        """删除用户"""
        with self.db_manager.get_session() as session:
            user_model = session.query(UserModel).filter(
                UserModel.id == user_id).first()
            if user_model:
                session.delete(user_model)
                return True
            return False

    def list(self, limit: int = 10, offset: int = 0) -> List[User]:
        """获取用户列表"""
        with self.db_manager.get_session() as session:
            user_models = session.query(UserModel).offset(
                offset).limit(limit).all()
            return [
                User(
                    id=model.id,
                    name=model.name,
                    email=model.email,
                    created_at=model.created_at
                )
                for model in user_models
            ]

# ================================
# HTTP客户端
# ================================


class HTTPClient:
    """HTTP客户端"""

    def __init__(self, base_url: str = '', timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Python-HTTPClient/1.0',
            'Content-Type': 'application/json'
        })

    def _make_url(self, endpoint: str) -> str:
        """构建完整URL"""
        return urljoin(self.base_url, endpoint)

    @retry(max_attempts=3)
    def get(
            self,
            endpoint: str,
            params: Dict = None,
            headers: Dict = None) -> Dict:
        """GET请求"""
        url = self._make_url(endpoint)
        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    @retry(max_attempts=3)
    def post(
            self,
            endpoint: str,
            data: Dict = None,
            headers: Dict = None) -> Dict:
        """POST请求"""
        url = self._make_url(endpoint)
        response = self.session.post(
            url,
            json=data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    @retry(max_attempts=3)
    def put(
            self,
            endpoint: str,
            data: Dict = None,
            headers: Dict = None) -> Dict:
        """PUT请求"""
        url = self._make_url(endpoint)
        response = self.session.put(
            url,
            json=data,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    @retry(max_attempts=3)
    def delete(self, endpoint: str, headers: Dict = None) -> bool:
        """DELETE请求"""
        url = self._make_url(endpoint)
        response = self.session.delete(
            url,
            headers=headers,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.status_code == 204

    def close(self):
        """关闭会话"""
        self.session.close()

# ================================
# 异步编程
# ================================


class AsyncHTTPClient:
    """异步HTTP客户端"""

    def __init__(self, base_url: str = '', timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        """异步GET请求"""
        import aiohttp

        url = urljoin(self.base_url, endpoint)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def post(self, endpoint: str, data: Dict = None) -> Dict:
        """异步POST请求"""
        import aiohttp

        url = urljoin(self.base_url, endpoint)
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(url, json=data) as response:
                response.raise_for_status()
                return await response.json()


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run_task(self, coro):
        """运行单个任务"""
        async with self.semaphore:
            return await coro

    async def run_tasks(self, tasks: List[Callable]) -> List[Any]:
        """并发运行多个任务"""
        coroutines = [self.run_task(task()) for task in tasks]
        return await asyncio.gather(*coroutines, return_exceptions=True)

    async def run_with_timeout(self, coro, timeout: float):
        """带超时的任务执行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"任务执行超时 ({timeout}秒)")

# ================================
# 工具函数
# ================================


class FileUtils:
    """文件工具类"""

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Dict:
        """读取JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def write_json(file_path: Union[str, Path], data: Dict, indent: int = 2):
        """写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    @staticmethod
    def ensure_dir(dir_path: Union[str, Path]):
        """确保目录存在"""
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """获取文件大小"""
        return Path(file_path).stat().st_size

    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]):
        """复制文件"""
        import shutil
        shutil.copy2(src, dst)


class StringUtils:
    """字符串工具类"""

    @staticmethod
    def snake_to_camel(snake_str: str) -> str:
        """蛇形命名转驼峰命名"""
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize()
                                       for word in components[1:])

    @staticmethod
    def camel_to_snake(camel_str: str) -> str:
        """驼峰命名转蛇形命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def truncate(text: str, length: int, suffix: str = '...') -> str:
        """截断字符串"""
        if len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix

    @staticmethod
    def is_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def generate_slug(text: str) -> str:
        """生成URL友好的slug"""
        # 转小写，替换空格和特殊字符
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')


class DateUtils:
    """日期工具类"""

    @staticmethod
    def format_datetime(
            dt: datetime,
            format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化日期时间"""
        return dt.strftime(format_str)

    @staticmethod
    def parse_datetime(
            date_str: str,
            format_str: str = '%Y-%m-%d %H:%M:%S') -> datetime:
        """解析日期时间字符串"""
        return datetime.strptime(date_str, format_str)

    @staticmethod
    def get_relative_time(dt: datetime) -> str:
        """获取相对时间"""
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"

    @staticmethod
    def is_weekend(dt: datetime) -> bool:
        """判断是否为周末"""
        return dt.weekday() >= 5

    @staticmethod
    def get_month_range(year: int, month: int) -> tuple[datetime, datetime]:
        """获取月份的开始和结束日期"""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        return start, end

# ================================
# 缓存系统
# ================================


class MemoryCache:
    """内存缓存"""

    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = threading.RLock()

    def get(self, key: str) -> Any:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl

        with self.lock:
            self.cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        with self.lock:
            expired_keys = [
                key for key, (_, expiry) in self.cache.items()
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self.cache[key]

# ================================
# 日志配置
# ================================


class Logger:
    """日志管理器"""

    def __init__(self, name: str = __name__, level: str = 'INFO'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # 文件处理器
            file_handler = logging.FileHandler('app.log', encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=kwargs)

# ================================
# Web应用示例
# ================================


class UserService:
    """用户服务"""

    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.logger = Logger('UserService')

    @handle_exceptions
    def create_user(self, name: str, email: str) -> Response:
        """创建用户"""
        # 验证输入
        if not name or not email:
            raise ValidationError("姓名和邮箱不能为空")

        if not StringUtils.is_email(email):
            raise ValidationError("邮箱格式不正确")

        # 创建用户
        user = User(id=0, name=name, email=email)
        created_user = self.repository.create(user)

        self.logger.info(f"用户创建成功: {created_user.id}")
        return Response(
            StatusCode.CREATED.value,
            created_user.to_dict(),
            "用户创建成功")

    @handle_exceptions
    def get_user(self, user_id: int) -> Response:
        """获取用户"""
        user = self.repository.get(user_id)
        if not user:
            raise NotFoundError(f"用户 {user_id} 不存在")

        return Response(StatusCode.SUCCESS.value, user.to_dict(), "获取成功")

    @handle_exceptions
    def list_users(self, page: int = 1, page_size: int = 10) -> Response:
        """获取用户列表"""
        offset = (page - 1) * page_size
        users = self.repository.list(limit=page_size, offset=offset)

        return Response(
            StatusCode.SUCCESS.value,
            {
                'users': [user.to_dict() for user in users],
                'page': page,
                'page_size': page_size
            },
            "获取成功"
        )


def create_app() -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化依赖
    db_manager = DatabaseManager(Config.DATABASE_URL)
    user_repository = UserRepository(db_manager)
    user_service = UserService(user_repository)

    @app.route('/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_manager.health_check()
        })

    @app.route('/users', methods=['POST'])
    def create_user():
        """创建用户"""
        data = request.get_json()
        response = user_service.create_user(
            name=data.get('name'),
            email=data.get('email')
        )
        return jsonify({
            'status_code': response.status_code,
            'data': response.data,
            'message': response.message
        }), response.status_code

    @app.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id: int):
        """获取用户"""
        response = user_service.get_user(user_id)
        return jsonify({
            'status_code': response.status_code,
            'data': response.data,
            'message': response.message
        }), response.status_code

    @app.route('/users', methods=['GET'])
    def list_users():
        """获取用户列表"""
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        response = user_service.list_users(page, page_size)
        return jsonify({
            'status_code': response.status_code,
            'data': response.data,
            'message': response.message
        }), response.status_code

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status_code': 404,
            'message': '资源未找到'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status_code': 500,
            'message': '内部服务器错误'
        }), 500

    return app

# ================================
# 数据处理
# ================================


class DataProcessor:
    """数据处理器"""

    @staticmethod
    def clean_data(data: List[Dict]) -> List[Dict]:
        """清理数据"""
        cleaned_data = []
        for item in data:
            cleaned_item = {}
            for key, value in item.items():
                # 清理字符串
                if isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ['null', 'none', 'n/a', '']:
                        value = None

                # 转换数字
                elif isinstance(value, str) and value.isdigit():
                    value = int(value)

                cleaned_item[key] = value

            cleaned_data.append(cleaned_item)

        return cleaned_data

    @staticmethod
    def group_by(data: List[Dict], key: str) -> Dict[Any, List[Dict]]:
        """按键分组"""
        groups = defaultdict(list)
        for item in data:
            groups[item.get(key)].append(item)
        return dict(groups)

    @staticmethod
    def aggregate(
            data: List[Dict],
            group_key: str,
            agg_key: str,
            agg_func: str = 'sum') -> Dict:
        """聚合数据"""
        groups = DataProcessor.group_by(data, group_key)
        result = {}

        for group_value, items in groups.items():
            values = [item.get(agg_key, 0)
                      for item in items if item.get(agg_key) is not None]

            if agg_func == 'sum':
                result[group_value] = sum(values)
            elif agg_func == 'avg':
                result[group_value] = sum(
                    values) / len(values) if values else 0
            elif agg_func == 'count':
                result[group_value] = len(values)
            elif agg_func == 'max':
                result[group_value] = max(values) if values else 0
            elif agg_func == 'min':
                result[group_value] = min(values) if values else 0

        return result

    @staticmethod
    def filter_data(data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """过滤数据"""
        filtered_data = []
        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_data.append(item)
        return filtered_data

# ================================
# 使用示例
# ================================


def main():
    """主函数示例"""
    # 初始化日志
    logger = Logger('Main')
    logger.info("应用启动")

    # 数据库操作示例
    db_manager = DatabaseManager('sqlite:///example.db')
    user_repo = UserRepository(db_manager)

    # 创建用户
    user = User(id=0, name="张三", email="zhangsan@example.com")
    created_user = user_repo.create(user)
    logger.info(f"创建用户: {created_user.to_dict()}")

    # HTTP客户端示例
    client = HTTPClient('https://jsonplaceholder.typicode.com')
    try:
        posts = client.get('/posts')
        logger.info(f"获取到 {len(posts)} 篇文章")
    except Exception as e:
        logger.error(f"HTTP请求失败: {e}")
    finally:
        client.close()

    # 缓存示例
    cache = MemoryCache()
    cache.set('user:1', created_user.to_dict())
    cached_user = cache.get('user:1')
    logger.info(f"缓存用户: {cached_user}")

    # 数据处理示例
    sample_data = [
        {'name': 'Alice', 'age': 25, 'city': 'Beijing'},
        {'name': 'Bob', 'age': 30, 'city': 'Shanghai'},
        {'name': 'Charlie', 'age': 35, 'city': 'Beijing'}
    ]

    grouped = DataProcessor.group_by(sample_data, 'city')
    logger.info(f"按城市分组: {grouped}")

    avg_age = DataProcessor.aggregate(sample_data, 'city', 'age', 'avg')
    logger.info(f"各城市平均年龄: {avg_age}")


async def async_main():
    """异步主函数示例"""
    logger = Logger('AsyncMain')

    # 异步HTTP客户端示例
    async_client = AsyncHTTPClient('https://jsonplaceholder.typicode.com')

    try:
        # 并发请求示例
        tasks = [
            lambda: async_client.get('/posts/1'),
            lambda: async_client.get('/posts/2'),
            lambda: async_client.get('/posts/3')
        ]

        task_manager = AsyncTaskManager(max_concurrent=3)
        results = await task_manager.run_tasks(tasks)

        logger.info(f"并发请求完成，获取到 {len(results)} 个结果")

    except Exception as e:
        logger.error(f"异步请求失败: {e}")

if __name__ == '__main__':
    # 同步示例
    main()

    # 异步示例
    # asyncio.run(async_main())

    # Web应用示例
    # app = create_app()
    # app.run(debug=True, host='0.0.0.0', port=5000)

# ================================
# 使用说明
# ================================

"""
1. 代码组织原则：
   - 模块化设计：将功能拆分为独立的类和函数
   - 单一职责：每个类和函数只负责一个功能
   - 依赖注入：通过构造函数注入依赖
   - 接口分离：使用Protocol定义接口

2. 错误处理：
   - 自定义异常类型
   - 统一的错误处理装饰器
   - 详细的错误信息和日志

3. 数据库操作：
   - 使用SQLAlchemy ORM
   - 连接池管理
   - 事务处理
   - 仓储模式

4. HTTP客户端：
   - 同步和异步版本
   - 重试机制
   - 超时控制
   - 会话管理

5. 异步编程：
   - asyncio协程
   - 并发控制
   - 超时处理
   - 异常处理

6. 缓存系统：
   - 内存缓存
   - TTL支持
   - 线程安全
   - 自动清理

7. 工具函数：
   - 文件操作
   - 字符串处理
   - 日期处理
   - 数据处理

8. 装饰器：
   - 计时器
   - 重试机制
   - 类型验证
   - 结果缓存
   - 单例模式

9. 日志系统：
   - 多级别日志
   - 多处理器
   - 格式化输出
   - 文件轮转

10. Web框架：
    - Flask应用
    - RESTful API
    - 错误处理
    - 健康检查

11. 最佳实践：
    - 类型注解
    - 文档字符串
    - 单元测试
    - 代码格式化
    - 静态分析

12. 性能优化：
    - 连接池
    - 缓存机制
    - 异步处理
    - 批量操作
    - 索引优化
"""
