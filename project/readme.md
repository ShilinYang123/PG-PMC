# PMC全流程管理系统

<div align="center">

![PMC Logo](https://via.placeholder.com/200x80/4F46E5/FFFFFF?text=PMC+System)

**现代化的生产管理与控制系统**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)](https://postgresql.org)

</div>

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [API文档](#api文档)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🚀 项目简介

PMC（Production Management & Control）全流程管理系统是一个现代化的生产管理平台，专为制造企业设计，提供从订单管理到生产控制的完整解决方案。

### 核心价值

- 🎯 **全流程管控**: 覆盖订单、物料、生产、质量全流程
- 📊 **数据驱动**: 实时数据分析，智能决策支持
- 🔄 **高效协同**: 多部门协同作业，提升整体效率
- 📱 **移动友好**: 响应式设计，支持移动端操作
- 🔒 **安全可靠**: 企业级安全保障，数据安全无忧

## 🏗️ 技术架构

### 前端技术栈
- **React 18** - 现代化前端框架
- **TypeScript** - 类型安全的JavaScript
- **Ant Design Pro** - 企业级UI组件库
- **ECharts** - 专业数据可视化图表库
- **Zustand** - 轻量级状态管理
- **Axios** - HTTP客户端

### 后端技术栈
- **Python 3.13** - 现代Python版本
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - ORM数据库操作
- **PostgreSQL** - 企业级关系数据库
- **Redis** - 高性能缓存数据库
- **Pydantic** - 数据验证和序列化

### 基础设施
- **Docker & Docker Compose** - 容器化部署
- **Nginx** - 反向代理和负载均衡
- **Alembic** - 数据库迁移管理
- **Loguru** - 结构化日志记录

## 📋 核心功能模块

### 1. 订单管理模块
- 订单录入与编辑
- 订单状态跟踪
- 客户信息管理
- 交期管理与预警

### 2. 生产计划模块
- 生产计划制定
- 资源分配优化
- 进度计划可视化
- 计划调整与优化

### 3. 物料管理模块
- 物料库存管理
- 采购计划制定
- 供应商管理
- 库存预警系统

### 4. 进度跟踪模块
- 实时生产进度
- 关键节点监控
- 异常预警处理
- 绩效分析报告

### 5. 图表可视化模块
- 生产看板展示
- 实时数据图表
- 趋势分析图表
- 自定义报表生成

### 6. 通知催办系统
- 微信消息推送
- 邮件自动发送
- 短信提醒功能
- 系统内消息通知

## 🚀 快速开始

### 环境要求
- **Python 3.13+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **PostgreSQL 15+**
- **Redis 7+**

### 1. 克隆项目
```bash
git clone <repository-url>
cd pmc-system
```

### 2. 环境配置
```bash
# 复制环境配置文件
copy .env.example .env

# 根据实际情况修改.env文件中的配置
```

### 3. 生产环境部署
```bash
# 使用Docker Compose一键启动
.\start.bat

# 或手动启动
docker-compose up -d
```

### 4. 开发环境启动
```bash
# 启动开发环境
.\dev.bat

# 或手动启动
# 1. 启动数据库
docker-compose up -d postgres redis

# 2. 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 3. 启动前端
cd frontend
npm install
npm start
```

## 📊 访问地址

### 生产环境
- **前端界面**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

### 开发环境
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 数据库连接
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🗂️ 项目结构

```
pmc-system/
├── backend/                 # 后端应用
│   ├── app/                # 应用核心代码
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── db/            # 数据库配置
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # 数据模式
│   │   └── services/      # 业务服务
│   ├── sql/               # SQL脚本
│   ├── static/            # 静态文件
│   ├── Dockerfile         # 后端容器配置
│   ├── main.py           # 应用入口
│   └── requirements.txt   # Python依赖
├── frontend/               # 前端应用
│   ├── public/            # 公共资源
│   ├── src/              # 源代码
│   │   ├── components/   # 组件库
│   │   ├── pages/        # 页面组件
│   │   └── config/       # 配置文件
│   ├── Dockerfile        # 前端容器配置
│   ├── nginx.conf        # Nginx配置
│   └── package.json      # Node.js依赖
├── nginx/                 # Nginx配置
│   ├── conf.d/           # 站点配置
│   └── nginx.conf        # 主配置
├── docker-compose.yml     # 容器编排配置
├── .env.example          # 环境配置示例
├── start.bat             # 生产环境启动脚本
├── dev.bat               # 开发环境启动脚本
└── README.md             # 项目文档
```

## 🔧 开发指南

### 后端开发
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python main.py

# 数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "描述"
```

### 前端开发
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 数据库管理
```bash
# 连接数据库
psql -h localhost -p 5432 -U pmc_user -d pmc_db

# 查看容器日志
docker-compose logs postgres

# 备份数据库
docker exec pmc-postgres pg_dump -U pmc_user pmc_db > backup.sql

# 恢复数据库
docker exec -i pmc-postgres psql -U pmc_user pmc_db < backup.sql
```

## 📈 监控与日志

### 应用监控
- **健康检查**: http://localhost:8000/health
- **系统指标**: 通过Docker容器状态监控
- **性能监控**: 集成APM工具（可选）

### 日志管理
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# 查看实时日志
docker-compose logs -f --tail=100
```

## 🔒 安全配置

### 生产环境安全检查清单
- [ ] 修改默认密码和密钥
- [ ] 配置HTTPS证书
- [ ] 设置防火墙规则
- [ ] 启用访问日志记录
- [ ] 配置备份策略
- [ ] 设置监控告警

### 环境变量安全
```bash
# 生产环境必须修改的配置
SECRET_KEY=生产环境密钥
JWT_SECRET_KEY=JWT密钥
DB_PASSWORD=数据库密码
REDIS_PASSWORD=Redis密码
```

## 🚀 部署指南

### Docker部署（推荐）
```bash
# 1. 准备环境
git clone <repository>
cd pmc-system
cp .env.example .env

# 2. 修改配置
# 编辑.env文件，设置生产环境配置

# 3. 启动服务
docker-compose up -d

# 4. 验证部署
curl http://localhost/health
```

### 传统部署
```bash
# 1. 安装依赖
# Python 3.13+, Node.js 18+, PostgreSQL, Redis

# 2. 配置数据库
# 创建数据库和用户

# 3. 部署后端
cd backend
pip install -r requirements.txt
gunicorn main:app --host 0.0.0.0 --port 8000

# 4. 部署前端
cd frontend
npm install
npm run build
# 配置Nginx服务静态文件
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

- **项目文档**: [Wiki](wiki)
- **问题反馈**: [Issues](issues)
- **技术讨论**: [Discussions](discussions)

## 🔄 版本历史

### v1.0.0 (2025-01-26)
- ✨ 初始版本发布
- 🏗️ 完整的基础架构搭建
- 📊 核心功能模块实现
- 🐳 Docker容器化部署
- 📖 完整的项目文档

---

**PMC全流程图表界面应用软件** - 让生产管理更智能、更高效！