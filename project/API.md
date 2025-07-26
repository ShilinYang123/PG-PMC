# PMC全流程管理系统 - API文档

## 📋 目录

- [API概述](#api概述)
- [认证授权](#认证授权)
- [通用响应格式](#通用响应格式)
- [错误处理](#错误处理)
- [用户管理API](#用户管理api)
- [订单管理API](#订单管理api)
- [物料管理API](#物料管理api)
- [生产管理API](#生产管理api)
- [通知管理API](#通知管理api)
- [文件管理API](#文件管理api)
- [系统管理API](#系统管理api)

## 🌐 API概述

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8
- **API版本**: v1

### 访问地址

| 环境 | 地址 | 说明 |
|------|------|------|
| 开发环境 | http://localhost:8001/api/v1 | 开发测试 |
| 生产环境 | http://localhost:8000/api/v1 | 生产部署 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | ReDoc文档 |

## 🔐 认证授权

### JWT Token认证

系统使用JWT (JSON Web Token) 进行用户认证。

#### 获取Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "username": "admin",
      "role": "admin",
      "email": "admin@example.com"
    }
  }
}
```

#### 使用Token

在请求头中添加Authorization字段：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### 刷新Token

```http
POST /auth/refresh
Authorization: Bearer <current_token>
```

### 权限控制

| 角色 | 权限 |
|------|------|
| admin | 系统管理员，拥有所有权限 |
| manager | 管理员，可管理订单、物料、生产 |
| operator | 操作员，可查看和操作生产流程 |
| viewer | 查看者，只能查看数据 |

## 📄 通用响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体数据
  }
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      // 数据列表
    ],
    "total": 100,
    "page": 1,
    "size": 20,
    "pages": 5
  }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": null,
  "errors": [
    {
      "field": "username",
      "message": "用户名不能为空"
    }
  ]
}
```

## ❌ 错误处理

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 错误代码

| 错误代码 | 说明 |
|----------|------|
| 1001 | 用户名或密码错误 |
| 1002 | Token已过期 |
| 1003 | Token无效 |
| 2001 | 订单不存在 |
| 2002 | 订单状态不允许此操作 |
| 3001 | 物料库存不足 |
| 3002 | 物料已被使用，无法删除 |

## 👤 用户管理API

### 用户登录

```http
POST /auth/login
```

**请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```

### 用户注册

```http
POST /auth/register
```

**请求参数**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "viewer"
}
```

### 获取当前用户信息

```http
GET /auth/me
Authorization: Bearer <token>
```

### 修改密码

```http
PUT /auth/password
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

### 用户列表

```http
GET /users?page=1&size=20&role=admin
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `size`: 每页数量 (默认: 20)
- `role`: 角色筛选
- `search`: 搜索关键词

### 创建用户

```http
POST /users
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "viewer",
  "is_active": true
}
```

### 更新用户

```http
PUT /users/{user_id}
Authorization: Bearer <token>
```

### 删除用户

```http
DELETE /users/{user_id}
Authorization: Bearer <token>
```

## 📦 订单管理API

### 订单列表

```http
GET /orders?page=1&size=20&status=pending
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `status`: 订单状态 (pending, confirmed, in_production, completed, cancelled)
- `customer_name`: 客户名称
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "order_number": "ORD-20240101-001",
        "customer_name": "客户A",
        "product_name": "产品A",
        "quantity": 100,
        "status": "pending",
        "delivery_date": "2024-01-15",
        "notes": "备注信息",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      }
    ],
    "total": 50,
    "page": 1,
    "size": 20,
    "pages": 3
  }
}
```

### 创建订单

```http
POST /orders
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "customer_name": "客户A",
  "product_name": "产品A",
  "quantity": 100,
  "delivery_date": "2024-01-15",
  "notes": "备注信息",
  "materials": [
    {
      "material_id": "uuid",
      "quantity": 50
    }
  ]
}
```

### 获取订单详情

```http
GET /orders/{order_id}
Authorization: Bearer <token>
```

### 更新订单

```http
PUT /orders/{order_id}
Authorization: Bearer <token>
```

### 删除订单

```http
DELETE /orders/{order_id}
Authorization: Bearer <token>
```

### 更新订单状态

```http
PATCH /orders/{order_id}/status
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "status": "confirmed",
  "notes": "状态变更备注"
}
```

### 订单统计

```http
GET /orders/statistics
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_orders": 150,
    "pending_orders": 20,
    "in_production_orders": 30,
    "completed_orders": 90,
    "cancelled_orders": 10,
    "monthly_trend": [
      {
        "month": "2024-01",
        "count": 25
      }
    ]
  }
}
```

## 🧱 物料管理API

### 物料列表

```http
GET /materials?page=1&size=20&category=raw
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `category`: 物料类别 (raw, semi_finished, finished)
- `status`: 物料状态 (active, inactive)
- `search`: 搜索关键词

### 创建物料

```http
POST /materials
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "name": "原料A",
  "code": "RAW-001",
  "category": "raw",
  "unit": "kg",
  "unit_price": 10.50,
  "stock_quantity": 1000,
  "min_stock": 100,
  "max_stock": 5000,
  "supplier": "供应商A",
  "description": "物料描述"
}
```

### 获取物料详情

```http
GET /materials/{material_id}
Authorization: Bearer <token>
```

### 更新物料

```http
PUT /materials/{material_id}
Authorization: Bearer <token>
```

### 删除物料

```http
DELETE /materials/{material_id}
Authorization: Bearer <token>
```

### 物料入库

```http
POST /materials/{material_id}/stock-in
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "quantity": 500,
  "unit_price": 10.50,
  "supplier": "供应商A",
  "batch_number": "BATCH-001",
  "notes": "入库备注"
}
```

### 物料出库

```http
POST /materials/{material_id}/stock-out
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "quantity": 100,
  "purpose": "生产使用",
  "order_id": "uuid",
  "notes": "出库备注"
}
```

### 库存统计

```http
GET /materials/inventory
Authorization: Bearer <token>
```

### 库存预警

```http
GET /materials/alerts
Authorization: Bearer <token>
```

## 🏭 生产管理API

### 生产计划列表

```http
GET /production/plans?page=1&size=20&status=active
Authorization: Bearer <token>
```

### 创建生产计划

```http
POST /production/plans
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "order_id": "uuid",
  "product_name": "产品A",
  "quantity": 100,
  "start_date": "2024-01-10",
  "end_date": "2024-01-20",
  "priority": "high",
  "materials": [
    {
      "material_id": "uuid",
      "quantity": 50
    }
  ],
  "notes": "生产备注"
}
```

### 生产进度更新

```http
PATCH /production/plans/{plan_id}/progress
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "completed_quantity": 30,
  "status": "in_progress",
  "notes": "进度更新备注"
}
```

### 生产完成

```http
POST /production/plans/{plan_id}/complete
Authorization: Bearer <token>
```

**请求参数**:
```json
{
  "actual_quantity": 98,
  "quality_check": true,
  "notes": "生产完成备注"
}
```

### 生产统计

```http
GET /production/statistics
Authorization: Bearer <token>
```

## 🔔 通知管理API

### 通知列表

```http
GET /notifications?page=1&size=20&is_read=false
Authorization: Bearer <token>
```

### 标记已读

```http
PATCH /notifications/{notification_id}/read
Authorization: Bearer <token>
```

### 批量标记已读

```http
PATCH /notifications/mark-all-read
Authorization: Bearer <token>
```

### 删除通知

```http
DELETE /notifications/{notification_id}
Authorization: Bearer <token>
```

## 📁 文件管理API

### 文件上传

```http
POST /files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
category: documents
description: 文件描述
```

**响应示例**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": "uuid",
    "filename": "document.pdf",
    "original_name": "原始文件名.pdf",
    "size": 1024000,
    "mime_type": "application/pdf",
    "url": "/files/download/uuid",
    "category": "documents",
    "uploaded_at": "2024-01-01T10:00:00Z"
  }
}
```

### 文件下载

```http
GET /files/download/{file_id}
Authorization: Bearer <token>
```

### 文件列表

```http
GET /files?page=1&size=20&category=documents
Authorization: Bearer <token>
```

### 删除文件

```http
DELETE /files/{file_id}
Authorization: Bearer <token>
```

## ⚙️ 系统管理API

### 系统健康检查

```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  }
}
```

### 系统信息

```http
GET /system/info
Authorization: Bearer <token>
```

### 系统配置

```http
GET /system/config
Authorization: Bearer <token>
```

### 更新系统配置

```http
PUT /system/config
Authorization: Bearer <token>
```

### 系统日志

```http
GET /system/logs?level=error&start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

### 数据备份

```http
POST /system/backup
Authorization: Bearer <token>
```

### 数据导出

```http
GET /system/export?type=orders&format=excel&start_date=2024-01-01
Authorization: Bearer <token>
```

## 📊 WebSocket API

### 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// 认证
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));

// 订阅通知
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'notifications'
}));
```

### 消息格式

```json
{
  "type": "notification",
  "channel": "notifications",
  "data": {
    "id": "uuid",
    "title": "库存预警",
    "message": "原料A库存不足",
    "type": "warning",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

## 🧪 API测试

### 使用curl测试

```bash
# 登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 使用token访问API
curl -X GET http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer <your-token>"
```

### 使用Postman

1. 导入API集合
2. 设置环境变量
3. 配置认证
4. 执行测试

### 自动化测试

```python
# tests/test_api.py
import pytest
import requests

class TestOrderAPI:
    def test_create_order(self, auth_headers):
        data = {
            "customer_name": "测试客户",
            "product_name": "测试产品",
            "quantity": 100
        }
        response = requests.post(
            "http://localhost:8000/api/v1/orders",
            json=data,
            headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["code"] == 200
```

## 📝 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 用户认证和授权
- 订单管理功能
- 物料管理功能
- 生产管理功能
- 通知系统
- 文件管理

---

**注意**: 
1. 所有API都需要有效的JWT Token（除了登录和健康检查）
2. 请求和响应数据都使用JSON格式
3. 日期时间格式使用ISO 8601标准
4. 分页从1开始计数
5. 所有删除操作都是软删除