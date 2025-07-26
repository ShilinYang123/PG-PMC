# PMC全流程管理系统 - 开发指南

## 📋 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [测试指南](#测试指南)
- [API开发](#api开发)
- [前端开发](#前端开发)
- [数据库开发](#数据库开发)
- [调试技巧](#调试技巧)
- [性能优化](#性能优化)

## 🛠️ 开发环境搭建

### 前置要求

- **Git**: 版本控制
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+ (可选，用于本地前端开发)
- **Python**: 3.11+ (可选，用于本地后端开发)
- **IDE**: VS Code / PyCharm / WebStorm

### 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd PG-PMC/project

# 2. 启动开发环境
# Windows
start-dev.bat

# Linux/macOS
make dev-quick-start
```

### 开发环境访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:3001 | React开发服务器 |
| 后端API | http://localhost:8001 | FastAPI应用 |
| API文档 | http://localhost:8001/docs | Swagger UI |
| 数据库管理 | http://localhost:5050 | pgAdmin |
| Redis管理 | http://localhost:8081 | Redis Commander |

### IDE配置

#### VS Code 推荐插件

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers"
  ]
}
```

#### 工作区设置

```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 📁 项目结构

```
PG-PMC/project/
├── backend/                 # 后端应用
│   ├── app/                # 应用代码
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── crud/          # 数据库操作
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # Pydantic模式
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── tests/             # 测试代码
│   ├── requirements.txt   # Python依赖
│   ├── Dockerfile         # 生产环境镜像
│   └── Dockerfile.dev     # 开发环境镜像
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── hooks/         # 自定义Hook
│   │   ├── services/      # API服务
│   │   ├── store/         # 状态管理
│   │   ├── utils/         # 工具函数
│   │   └── types/         # TypeScript类型
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   ├── Dockerfile         # 生产环境镜像
│   └── Dockerfile.dev     # 开发环境镜像
├── nginx/                  # Nginx配置
├── docs/                   # 文档
├── scripts/                # 脚本文件
└── docker-compose*.yml     # Docker编排文件
```

## 🔄 开发流程

### Git工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和提交
git add .
git commit -m "feat: add new feature"

# 3. 推送分支
git push origin feature/new-feature

# 4. 创建Pull Request
# 5. 代码审查
# 6. 合并到主分支
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
type(scope): description

[optional body]

[optional footer]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(orders): add order status tracking
fix(auth): resolve token expiration issue
docs(api): update authentication documentation
```

## 📝 代码规范

### Python代码规范

#### 格式化工具

```bash
# 代码格式化
make format

# 或者手动执行
docker exec pmc_backend_dev black app/
docker exec pmc_backend_dev isort app/
```

#### 代码检查

```bash
# 代码检查
make lint

# 或者手动执行
docker exec pmc_backend_dev flake8 app/
docker exec pmc_backend_dev mypy app/
```

#### 编码规范

```python
# 导入顺序
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse

# 函数定义
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
) -> OrderResponse:
    """创建新订单.
    
    Args:
        order_data: 订单创建数据
        db: 数据库会话
        
    Returns:
        创建的订单信息
        
    Raises:
        HTTPException: 当创建失败时
    """
    # 实现逻辑
    pass
```

### TypeScript代码规范

#### 格式化配置

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

#### 编码规范

```typescript
// 接口定义
interface OrderData {
  id: string;
  customerName: string;
  status: OrderStatus;
  createdAt: Date;
}

// 组件定义
interface OrderListProps {
  orders: OrderData[];
  onOrderSelect: (order: OrderData) => void;
}

export const OrderList: React.FC<OrderListProps> = ({
  orders,
  onOrderSelect,
}) => {
  return (
    <div className="order-list">
      {orders.map((order) => (
        <OrderItem
          key={order.id}
          order={order}
          onClick={() => onOrderSelect(order)}
        />
      ))}
    </div>
  );
};
```

## 🧪 测试指南

### 后端测试

#### 测试结构

```
tests/
├── conftest.py           # 测试配置
├── test_api/            # API测试
│   ├── test_auth.py
│   ├── test_orders.py
│   └── test_materials.py
├── test_crud/           # CRUD测试
├── test_services/       # 服务测试
└── test_utils/          # 工具测试
```

#### 测试示例

```python
# tests/test_api/test_orders.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.order import Order

client = TestClient(app)

def test_create_order(db: Session):
    """测试创建订单."""
    order_data = {
        "customer_name": "测试客户",
        "product_name": "测试产品",
        "quantity": 100
    }
    
    response = client.post("/api/v1/orders/", json=order_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == order_data["customer_name"]
    assert "id" in data

def test_get_orders(db: Session):
    """测试获取订单列表."""
    response = client.get("/api/v1/orders/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

#### 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
docker exec pmc_backend_dev pytest tests/test_api/test_orders.py -v

# 运行测试并生成覆盖率报告
docker exec pmc_backend_dev pytest --cov=app --cov-report=html
```

### 前端测试

#### 测试工具

- **Jest**: 测试框架
- **React Testing Library**: React组件测试
- **MSW**: API模拟

#### 测试示例

```typescript
// src/components/__tests__/OrderList.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { OrderList } from '../OrderList';

const mockOrders = [
  {
    id: '1',
    customerName: '测试客户',
    status: 'pending',
    createdAt: new Date(),
  },
];

test('renders order list', () => {
  const onOrderSelect = jest.fn();
  
  render(
    <OrderList orders={mockOrders} onOrderSelect={onOrderSelect} />
  );
  
  expect(screen.getByText('测试客户')).toBeInTheDocument();
});

test('calls onOrderSelect when order is clicked', () => {
  const onOrderSelect = jest.fn();
  
  render(
    <OrderList orders={mockOrders} onOrderSelect={onOrderSelect} />
  );
  
  fireEvent.click(screen.getByText('测试客户'));
  expect(onOrderSelect).toHaveBeenCalledWith(mockOrders[0]);
});
```

## 🔌 API开发

### API设计原则

1. **RESTful设计**: 使用标准HTTP方法
2. **一致性**: 统一的响应格式
3. **版本控制**: API版本管理
4. **错误处理**: 标准化错误响应
5. **文档化**: 完整的API文档

### 路由结构

```python
# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth, orders, materials, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(materials.router, prefix="/materials", tags=["物料"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
```

### 响应格式

```python
# app/schemas/response.py
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

DataT = TypeVar("DataT")

class Response(BaseModel, Generic[DataT]):
    """标准响应格式."""
    code: int = 200
    message: str = "success"
    data: Optional[DataT] = None

class PaginatedResponse(BaseModel, Generic[DataT]):
    """分页响应格式."""
    items: list[DataT]
    total: int
    page: int
    size: int
    pages: int
```

### 错误处理

```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class BusinessException(HTTPException):
    """业务异常."""
    def __init__(self, message: str, code: int = 400):
        super().__init__(status_code=code, detail=message)

class NotFoundError(BusinessException):
    """资源不存在异常."""
    def __init__(self, resource: str):
        super().__init__(f"{resource}不存在", 404)

class ValidationError(BusinessException):
    """验证异常."""
    def __init__(self, message: str):
        super().__init__(message, 422)
```

## 🎨 前端开发

### 技术栈

- **React 18**: UI框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **React Query**: 数据获取
- **React Router**: 路由管理
- **Zustand**: 状态管理

### 组件开发

#### 组件结构

```typescript
// src/components/OrderCard/index.tsx
import React from 'react';
import { OrderData } from '../../types/order';
import './OrderCard.css';

interface OrderCardProps {
  order: OrderData;
  onEdit?: (order: OrderData) => void;
  onDelete?: (orderId: string) => void;
}

export const OrderCard: React.FC<OrderCardProps> = ({
  order,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="order-card">
      <div className="order-card__header">
        <h3>{order.customerName}</h3>
        <span className={`status status--${order.status}`}>
          {order.status}
        </span>
      </div>
      <div className="order-card__content">
        <p>产品: {order.productName}</p>
        <p>数量: {order.quantity}</p>
      </div>
      <div className="order-card__actions">
        {onEdit && (
          <button onClick={() => onEdit(order)}>编辑</button>
        )}
        {onDelete && (
          <button onClick={() => onDelete(order.id)}>删除</button>
        )}
      </div>
    </div>
  );
};
```

#### 自定义Hook

```typescript
// src/hooks/useOrders.ts
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { orderService } from '../services/orderService';
import { OrderData, OrderCreateData } from '../types/order';

export const useOrders = () => {
  return useQuery('orders', orderService.getOrders);
};

export const useCreateOrder = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (data: OrderCreateData) => orderService.createOrder(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('orders');
      },
    }
  );
};
```

### 状态管理

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(n  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

## 🗄️ 数据库开发

### 模型定义

```python
# app/models/order.py
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base
from app.core.enums import OrderStatus

class Order(Base):
    """订单模型."""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Order {self.order_number}>"
```

### 数据库迁移

```python
# 创建迁移文件
alembic revision --autogenerate -m "add order table"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### CRUD操作

```python
# app/crud/order.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate
from app.core.enums import OrderStatus

class OrderCRUD:
    """订单CRUD操作."""
    
    def create(self, db: Session, obj_in: OrderCreate) -> Order:
        """创建订单."""
        db_obj = Order(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: str) -> Optional[Order]:
        """根据ID获取订单."""
        return db.query(Order).filter(Order.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """获取订单列表."""
        query = db.query(Order)
        if status:
            query = query.filter(Order.status == status)
        return query.offset(skip).limit(limit).all()
    
    def update(self, db: Session, db_obj: Order, obj_in: OrderUpdate) -> Order:
        """更新订单."""
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: str) -> Order:
        """删除订单."""
        obj = db.query(Order).get(id)
        db.delete(obj)
        db.commit()
        return obj

order_crud = OrderCRUD()
```

## 🐛 调试技巧

### 后端调试

#### 日志调试

```python
# app/core/logging.py
import logging
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 使用示例
logger.info(f"Creating order: {order_data}")
logger.error(f"Failed to create order: {error}")
```

#### 断点调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用ipdb（更友好的界面）
import ipdb; ipdb.set_trace()
```

#### 性能分析

```python
# 使用cProfile
import cProfile
import pstats

def profile_function():
    pr = cProfile.Profile()
    pr.enable()
    
    # 执行代码
    result = some_function()
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

### 前端调试

#### React DevTools

```typescript
// 组件调试
const OrderList = ({ orders }) => {
  console.log('OrderList rendered with:', orders);
  
  useEffect(() => {
    console.log('Orders updated:', orders);
  }, [orders]);
  
  return (
    // JSX
  );
};
```

#### 网络调试

```typescript
// 拦截器调试
axios.interceptors.request.use(
  (config) => {
    console.log('Request:', config);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => {
    console.log('Response:', response);
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    return Promise.reject(error);
  }
);
```

## ⚡ 性能优化

### 后端优化

#### 数据库查询优化

```python
# 使用索引
from sqlalchemy import Index

Index('idx_order_status_created', Order.status, Order.created_at)

# 预加载关联数据
from sqlalchemy.orm import joinedload

orders = db.query(Order).options(
    joinedload(Order.customer),
    joinedload(Order.items)
).all()

# 分页查询
def get_orders_paginated(db: Session, page: int, size: int):
    offset = (page - 1) * size
    return db.query(Order).offset(offset).limit(size).all()
```

#### 缓存优化

```python
# Redis缓存
from app.core.cache import cache

@cache.cached(timeout=300, key_prefix='order_list')
def get_orders_cached(status: str = None):
    # 查询逻辑
    return orders

# 缓存失效
cache.delete('order_list')
```

### 前端优化

#### 组件优化

```typescript
// 使用React.memo
const OrderCard = React.memo<OrderCardProps>(({ order, onEdit }) => {
  return (
    // JSX
  );
});

// 使用useMemo
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// 使用useCallback
const handleClick = useCallback((id: string) => {
  onOrderSelect(id);
}, [onOrderSelect]);
```

#### 代码分割

```typescript
// 路由级别的代码分割
const OrderPage = lazy(() => import('../pages/OrderPage'));
const MaterialPage = lazy(() => import('../pages/MaterialPage'));

// 组件级别的代码分割
const HeavyComponent = lazy(() => import('../components/HeavyComponent'));
```

## 📚 学习资源

### 官方文档

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)

### 推荐阅读

- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Effective Python](https://effectivepython.com/)
- [You Don't Know JS](https://github.com/getify/You-Dont-Know-JS)

---

**注意**: 本文档会随着项目发展持续更新，建议定期查看最新版本。