# PMC全流程管理系统 - 部署指南

## 📋 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [生产环境部署](#生产环境部署)
- [开发环境部署](#开发环境部署)
- [配置说明](#配置说明)
- [监控与维护](#监控与维护)
- [故障排除](#故障排除)
- [安全配置](#安全配置)

## 🔧 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Windows 10/11, Linux, macOS
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 推荐配置
- **CPU**: 4核心或更多
- **内存**: 8GB RAM 或更多
- **存储**: 50GB SSD
- **网络**: 稳定的互联网连接

## 🚀 快速部署

### Windows 环境

```batch
# 1. 克隆项目
git clone <repository-url>
cd PG-PMC/project

# 2. 启动生产环境
start-docker.bat
```

### Linux/macOS 环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd PG-PMC/project

# 2. 使用 Makefile
make quick-start

# 或者手动执行
docker-compose build
docker-compose up -d
```

## 🏭 生产环境部署

### 1. 环境准备

```bash
# 创建生产环境配置
cp .env.example .env

# 编辑配置文件
vim .env
```

### 2. 关键配置项

```bash
# 安全配置
SECRET_KEY=your-super-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库配置
DB_PASSWORD=strong-database-password
REDIS_PASSWORD=strong-redis-password

# 环境设置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 3. 部署步骤

```bash
# 1. 构建镜像
docker-compose build --no-cache

# 2. 启动服务
docker-compose up -d

# 3. 检查服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 4. 数据库初始化

```bash
# 等待数据库启动
sleep 30

# 检查数据库连接
docker exec pmc_postgres pg_isready -U pmc_user

# 查看初始化日志
docker-compose logs postgres
```

## 🛠️ 开发环境部署

### Windows 环境

```batch
# 启动开发环境
start-dev.bat
```

### Linux/macOS 环境

```bash
# 使用 Makefile
make dev-quick-start

# 或者手动执行
docker-compose -f docker-compose.dev.yml build
docker-compose -f docker-compose.dev.yml up -d
```

### 开发环境特性

- ✅ 热重载（前端和后端）
- ✅ 调试模式
- ✅ 详细日志
- ✅ 数据库管理工具 (pgAdmin)
- ✅ Redis管理工具
- ✅ 代码质量工具

## ⚙️ 配置说明

### 环境变量文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `.env` | 生产环境 | 生产环境配置 |
| `.env.example` | 配置模板 | 配置示例和说明 |
| `.env.dev` | 开发环境 | 开发环境专用配置 |

### 端口配置

#### 生产环境
| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | Web服务器 |
| 前端 | 3000 | React应用 |
| 后端 | 8000 | FastAPI应用 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

#### 开发环境
| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3001 | React应用（开发） |
| 后端 | 8001 | FastAPI应用（开发） |
| PostgreSQL | 5433 | 数据库（开发） |
| Redis | 6380 | 缓存（开发） |
| pgAdmin | 5050 | 数据库管理 |
| Redis Commander | 8081 | Redis管理 |

## 📊 监控与维护

### 健康检查

```bash
# 检查所有服务状态
docker-compose ps

# 检查特定服务健康状态
docker inspect --format='{{.State.Health.Status}}' pmc_backend

# 访问健康检查端点
curl http://localhost:8000/health
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend

# 查看最近的日志
docker-compose logs --tail=100 backend
```

### 数据备份

```bash
# 数据库备份
docker exec pmc_postgres pg_dump -U pmc_user pmc_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 使用 Makefile
make backup
```

### 数据恢复

```bash
# 恢复数据库
docker exec -i pmc_postgres psql -U pmc_user -d pmc_db < backup_file.sql

# 使用 Makefile
make restore
```

## 🔧 故障排除

### 常见问题

#### 1. 服务启动失败

```bash
# 检查Docker状态
docker version
docker-compose version

# 查看详细错误
docker-compose logs

# 重新构建镜像
docker-compose build --no-cache
```

#### 2. 数据库连接失败

```bash
# 检查数据库状态
docker-compose logs postgres

# 测试数据库连接
docker exec pmc_postgres pg_isready -U pmc_user

# 进入数据库容器
docker exec -it pmc_postgres psql -U pmc_user -d pmc_db
```

#### 3. 前端无法访问后端

```bash
# 检查网络连接
docker network ls
docker network inspect pmc_network

# 检查CORS配置
echo $BACKEND_CORS_ORIGINS
```

#### 4. 内存不足

```bash
# 检查系统资源
docker stats

# 清理未使用的资源
docker system prune -f
```

### 调试命令

```bash
# 进入容器调试
docker exec -it pmc_backend bash
docker exec -it pmc_frontend sh
docker exec -it pmc_postgres psql -U pmc_user -d pmc_db

# 查看容器资源使用
docker stats

# 查看网络配置
docker network inspect pmc_network
```

## 🔒 安全配置

### 生产环境安全清单

- [ ] 更改默认密码
- [ ] 使用强密钥
- [ ] 配置HTTPS
- [ ] 设置防火墙规则
- [ ] 定期备份数据
- [ ] 监控系统日志
- [ ] 更新依赖包

### SSL/TLS 配置

```bash
# 生成自签名证书（仅用于测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# 启用HTTPS配置
# 编辑 nginx/conf.d/default.conf
# 取消注释HTTPS server块
```

### 环境变量安全

```bash
# 设置文件权限
chmod 600 .env

# 不要将.env文件提交到版本控制
echo ".env" >> .gitignore
```

## 📈 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);
CREATE INDEX CONCURRENTLY idx_orders_created_at ON orders(created_at);

-- 分析表统计信息
ANALYZE;
```

### 缓存配置

```bash
# Redis内存优化
# 在docker-compose.yml中添加
command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Nginx优化

```nginx
# 在nginx.conf中添加
worker_processes auto;
worker_connections 2048;

# 启用gzip压缩
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

## 🔄 更新部署

### 滚动更新

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose build

# 3. 滚动更新服务
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend

# 4. 验证更新
curl http://localhost:8000/health
```

### 回滚部署

```bash
# 1. 回滚到上一个版本
git checkout <previous-commit>

# 2. 重新构建和部署
docker-compose build
docker-compose up -d
```

## 📞 技术支持

如果遇到问题，请按以下步骤操作：

1. 查看本文档的故障排除部分
2. 检查系统日志和错误信息
3. 搜索已知问题和解决方案
4. 联系技术支持团队

---

**注意**: 本文档会随着系统更新而持续更新，请定期查看最新版本。