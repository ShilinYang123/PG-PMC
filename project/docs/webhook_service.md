# PMC微信Webhook服务文档

## 概述

PMC微信Webhook服务是一个专门处理微信API回调的服务，支持微信企业号API和群机器人的消息接收、状态回调和用户交互处理。

## 功能特性

### 核心功能
- **微信API集成**: 支持微信企业号API和群机器人
- **Webhook处理**: 处理微信平台的各种回调事件
- **消息状态跟踪**: 实时跟踪消息发送状态和用户交互
- **异步处理**: 高性能异步事件处理
- **安全验证**: 支持签名验证和加密解密

### 支持的事件类型
- 消息发送状态 (已发送、已送达、已读、失败)
- 用户交互事件 (点击、回复、转发等)
- 系统事件 (用户加入、离开等)

## 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   微信平台      │───▶│  Webhook服务    │───▶│   业务系统      │
│                 │    │                 │    │                 │
│ • 企业号API     │    │ • 事件接收      │    │ • 消息处理      │
│ • 群机器人      │    │ • 状态跟踪      │    │ • 状态更新      │
│ • 状态回调      │    │ • 签名验证      │    │ • 用户交互      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose
- Redis (缓存)
- MySQL (数据存储)
- MongoDB (日志存储)

### 配置环境变量

在项目根目录的 `.env` 文件中配置以下变量：

```bash
# 微信企业号配置
WECHAT_CORP_ID=your_corp_id
WECHAT_CORP_SECRET=your_corp_secret
WECHAT_AGENT_ID=your_agent_id
WECHAT_BASE_URL=https://qyapi.weixin.qq.com

# 微信群机器人配置
WECHAT_BOT_WEBHOOK_URL=your_bot_webhook_url
WECHAT_BOT_SECRET=your_bot_secret

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=pmc_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=pmc_webhook

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=pmc_logs

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

### 部署方式

#### 方式1: 使用部署脚本 (推荐)

```bash
# 生产环境部署
./scripts/deploy_webhook.sh

# 开发环境部署
./scripts/deploy_webhook.sh -e development

# 启用Nginx反向代理
./scripts/deploy_webhook.sh -n

# 强制重新构建
./scripts/deploy_webhook.sh -f
```

#### 方式2: 手动Docker部署

```bash
# 进入Docker目录
cd docker/webhook

# 启动服务
docker-compose up -d

# 启用Nginx (可选)
docker-compose --profile with-nginx up -d
```

#### 方式3: 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python src/notification/webhooks/run_webhook_server.py
```

## API接口

### Webhook回调接口

#### 微信企业号回调
```
POST /api/v1/webhooks/wechat/api
GET  /api/v1/webhooks/wechat/api/verify
```

#### 微信群机器人回调
```
POST /api/v1/webhooks/wechat/bot
```

### 管理接口

#### 健康检查
```
GET /health
```

#### 服务状态
```
GET /api/v1/status
```

#### 消息状态查询
```
GET /api/v1/messages/{message_id}/status
GET /api/v1/messages/{message_id}/history
```

#### 处理器管理
```
GET /api/v1/webhooks/handlers
```

## 配置说明

### 通知配置文件

配置文件位置: `config/notification.yaml`

```yaml
service:
  name: "PMC通知服务"
  version: "1.0.0"
  
webhook:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  
channels:
  wechat_api:
    enabled: true
    corp_id: "${WECHAT_CORP_ID}"
    secret: "${WECHAT_CORP_SECRET}"
    agent_id: "${WECHAT_AGENT_ID}"
    
  wechat_bot:
    enabled: true
    webhook_url: "${WECHAT_BOT_WEBHOOK_URL}"
    secret: "${WECHAT_BOT_SECRET}"
```

### 安全配置

- **签名验证**: 所有webhook请求都会进行签名验证
- **加密解密**: 支持微信消息加密解密
- **访问控制**: 可配置IP白名单和访问限制
- **SSL/TLS**: 支持HTTPS和证书配置

## 开发指南

### 项目结构

```
src/notification/webhooks/
├── __init__.py              # 模块初始化
├── base.py                  # 基础webhook处理器
├── wechat_webhook.py        # 微信webhook处理器
├── status_handler.py        # 状态回调处理器
├── routes.py                # FastAPI路由
├── app.py                   # FastAPI应用
└── run_webhook_server.py    # 服务启动脚本
```

### 添加新的事件处理器

```python
from src.notification.webhooks import get_message_tracker, MessageStatusType

# 获取消息跟踪器
tracker = get_message_tracker()

# 添加状态回调
async def on_message_sent(status_update):
    print(f"消息 {status_update.message_id} 发送成功")

tracker.add_status_callback(MessageStatusType.SENT, on_message_sent)

# 添加用户交互回调
async def on_user_interaction(interaction):
    print(f"用户 {interaction.user_id} 进行了 {interaction.interaction_type} 操作")

tracker.add_interaction_callback(on_user_interaction)
```

### 自定义Webhook处理器

```python
from src.notification.webhooks.base import BaseWebhookHandler, WebhookEvent

class CustomWebhookHandler(BaseWebhookHandler):
    async def handle_request(self, request_data: dict, headers: dict) -> WebhookEvent:
        # 实现自定义处理逻辑
        pass
    
    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        # 实现签名验证
        pass
```

## 监控和日志

### 日志配置

日志文件位置:
- 应用日志: `/app/logs/webhook_service.log`
- 访问日志: `/var/log/nginx/access.log` (使用Nginx时)
- 错误日志: `/var/log/nginx/error.log` (使用Nginx时)

### 监控指标

- **请求量**: webhook请求数量和频率
- **响应时间**: 请求处理时间
- **错误率**: 失败请求比例
- **消息状态**: 各种消息状态的统计

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查API状态
curl http://localhost:8080/api/v1/status
```

## 故障排除

### 常见问题

#### 1. 服务启动失败

**问题**: 服务无法启动

**解决方案**:
- 检查环境变量配置
- 确认端口未被占用
- 查看错误日志

```bash
# 查看服务日志
docker-compose logs wechat-webhook

# 检查端口占用
netstat -tlnp | grep 8080
```

#### 2. Webhook验证失败

**问题**: 微信平台验证失败

**解决方案**:
- 确认URL配置正确
- 检查Token和EncodingAESKey
- 验证网络连通性

```bash
# 测试webhook端点
curl "http://localhost:8080/api/v1/webhooks/wechat/api/verify?msg_signature=xxx&timestamp=xxx&nonce=xxx&echostr=xxx"
```

#### 3. 消息接收异常

**问题**: 无法接收微信消息

**解决方案**:
- 检查签名验证逻辑
- 确认消息格式解析
- 查看详细错误日志

### 调试模式

```bash
# 启用调试模式
export LOG_LEVEL=DEBUG
python src/notification/webhooks/run_webhook_server.py --log-level DEBUG
```

## 性能优化

### 配置建议

1. **并发处理**: 根据负载调整worker数量
2. **缓存策略**: 合理使用Redis缓存
3. **数据库优化**: 配置连接池和索引
4. **负载均衡**: 使用Nginx进行负载均衡

### 扩展部署

```yaml
# docker-compose.yml 扩展配置
services:
  wechat-webhook:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

## 安全最佳实践

1. **环境变量**: 敏感信息使用环境变量
2. **网络隔离**: 使用Docker网络隔离
3. **访问控制**: 配置防火墙和IP白名单
4. **SSL证书**: 生产环境使用HTTPS
5. **定期更新**: 及时更新依赖和镜像

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 支持微信企业号API和群机器人
- 实现消息状态跟踪
- 提供Docker部署方案
- 添加Nginx反向代理支持

## 支持和反馈

如有问题或建议，请联系开发团队或提交Issue。