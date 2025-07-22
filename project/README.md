# PG-PMC 智能追踪系统 - AI Agent驱动的生产管理平台

<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.11+-brightgreen.svg" alt="Python">
  <img src="https://img.shields.io/badge/AI-Agent-orange.svg" alt="AI Agent">
  <img src="https://img.shields.io/badge/PMC-Production-purple.svg" alt="PMC">
</div>

## 📋 项目简介

**PG-PMC智能追踪系统是一个AI Agent驱动的生产管理平台，专注于小家电行业的计划排程、预警提醒和闭环跟踪。**

本系统为3AI电器实业有限公司量身定制，通过智能化算法和多模态交互，实现生产过程的自动化管理，提升生产效率95%以上，降低人工成本，优化资源配置。

### ✨ 核心特性

#### 🤖 AI智能排程
- **LSTM预测算法**：基于历史数据预测生产需求和交期
- **遗传算法优化**：智能优化生产排程，提升资源利用率
- **多约束求解**：综合考虑设备、人员、物料等多重约束
- **动态调整**：实时响应生产变化，自动调整排程计划

#### 📊 智能预警系统
- **多维度监控**：实时监控生产进度、质量、设备状态
- **预警模型**：基于机器学习的异常检测和风险预警
- **多模态提醒**：支持微信、短信、邮件等多种提醒方式
- **分级预警**：根据紧急程度自动分级处理

#### 🔄 闭环跟踪机制
- **全流程追踪**：从订单到交付的全生产流程跟踪
- **IoT数据集成**：集成生产设备和传感器数据
- **实时反馈**：生产状态实时反馈和数据更新
- **自动纠偏**：发现偏差时自动触发纠正措施

## 🏗️ 技术架构

### 核心技术栈
- **AI层**: TensorFlow/PyTorch, LSTM预测, 遗传算法优化
- **数据层**: MySQL, MongoDB, Redis缓存
- **后端**: Python 3.11+, FastAPI, SQLAlchemy
- **前端**: React, TypeScript, Ant Design
- **接口层**: WeChat API, Twilio, IoT集成
- **部署**: Docker, Kubernetes, 云服务器

### PMC智能引擎
- **消息队列** - RabbitMQ/Kafka
- **机器学习** - 预测模型和异常检测
- **数据分析** - 生产数据挖掘
- **实时监控** - IoT设备数据采集

### 系统架构图
```
用户输入 → 数据采集 → AI预测 → 排程生成 → 预警触发 → 多模态提醒 → 闭环确认
    ↓           ↓         ↓         ↓         ↓         ↓         ↓
管理界面 ← 数据处理 ← 算法引擎 ← 排程优化 ← 预警系统 ← 消息推送 ← 状态反馈
```

### 开发工具
- **IDE**: VS Code + Python扩展
- **版本控制**: Git
- **容器化**: Docker + Dev Container
- **测试框架**: pytest, unittest
- **代码质量**: flake8, black, mypy

## 🛠️ 环境要求

### 系统要求
- **操作系统**: Linux/Windows/macOS
- **Python版本**: 3.11+
- **内存**: 16GB+ (推荐32GB)
- **硬盘**: 50GB可用空间
- **数据库**: MySQL 8.0+, MongoDB 5.0+

### 软件依赖
- **数据库**: MySQL, MongoDB, Redis
- **消息队列**: RabbitMQ或Kafka
- **Python环境**: 建议使用Anaconda或虚拟环境
- **Git**: 用于版本控制
- **Docker**: 推荐，用于容器化部署

## 🚀 快速开始

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/pg-pmc-tracking.git
cd pg-pmc-tracking

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库和API密钥

# 5. 初始化数据库
python scripts/init_database.py

# 6. 启动服务
python src/main.py
```

### 配置说明

#### 1. 环境变量配置 (.env)
```bash
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=pmc_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=pmc_tracking

# MongoDB配置
MONGODB_URI=mongodb://localhost:27017/pmc_data

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# API配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_secret
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# 应用配置
APP_DEBUG=true
LOG_LEVEL=INFO
```

#### 2. 数据库配置
- 安装并配置MySQL数据库
- 安装并配置MongoDB
- 安装并配置Redis缓存
- 运行数据库初始化脚本

### 使用方法

#### 1. 启动PMC智能追踪系统
```bash
# 启动主程序
python src/main.py

# 或使用Web界面
python src/ui/web_interface.py
```

#### 2. 基本使用示例
```python
from src.core.pmc_system import PMCTrackingSystem

# 初始化系统
system = PMCTrackingSystem()

# 连接数据库
system.connect_database()

# 智能排程
response = system.generate_schedule(
    "为下周小家电生产线制定最优排程计划"
)

print(response.schedule_plan)
```

#### 3. 支持的管理指令
- **生产排程**："为A产品线安排下周生产计划"
- **预警监控**："监控B产品线的生产进度"
- **资源优化**："优化设备利用率和人员配置"
- **质量跟踪**："跟踪产品质量数据和异常"
- **交期管理**："预测订单交期和风险评估"

## 📚 文档

### 技术文档
- [📖 API文档](docs/api.md) - 详细的API接口说明
- [🏗️ 架构设计](docs/architecture.md) - 系统架构和设计思路
- [🔧 开发指南](docs/development.md) - 开发环境搭建和贡献指南
- [🎯 用户手册](docs/user-guide.md) - 详细的使用说明

### PMC系统文档
- [🤖 AI算法文档](docs/ai-algorithms.md) - LSTM和遗传算法说明
- [📊 数据模型](docs/data-models.md) - 数据库设计和数据流
- [🔔 预警系统](docs/alert-system.md) - 预警机制和配置
- [🛠️ 故障排除](docs/troubleshooting.md) - 常见问题解决方案

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 生成覆盖率报告
python -m pytest --cov=src tests/

# 测试数据库连接
python tests/test_database.py

# 测试AI模型
python tests/test_ai_models.py

# 测试排程算法
python tests/test_scheduling.py
```

### 测试覆盖率
- **目标覆盖率**: 90%+
- **核心模块**: 95%+
- **集成测试**: 完整的端到端测试

## 🔧 部署

### 生产环境部署

```bash
# 1. 环境检查
python src/config/environment.py --check

# 2. 安装生产依赖
pip install -r requirements.txt

# 3. 配置生产环境变量
cp .env.production .env

# 4. 启动服务
python src/main.py --mode=production
```

### Windows服务部署

```bash
# 安装为Windows服务
python scripts/install_service.py

# 启动服务
net start PGDevAIAssistant

# 停止服务
net stop PGDevAIAssistant
```

## 📊 项目状态

### 开发进度

- [x] 项目初始化和架构设计
- [x] 核心PMC模块开发（排程、预警、追踪）
- [x] AI算法集成（LSTM预测、遗传算法）
- [x] 数据库设计和配置
- [x] 基础Web界面开发
- 🚧 多模态提醒系统
- 🚧 IoT设备集成
- ⏳ 移动端应用开发
- ⏳ 生产环境部署和优化

## 🗺️ 开发路线图

### 第一阶段 ✅ (基础版)
- [x] 核心数据模型设计
- [x] 基础排程算法
- [x] 数据库架构搭建
- [x] 基础预警功能
- [x] 简单的Web界面
- [x] 配置管理系统
- [x] 日志和错误处理
- [x] 基础测试框架

### 第二阶段 🚧 (增强版)
- [ ] LSTM预测模型集成
- [ ] 遗传算法优化引擎
- [ ] 多模态提醒系统
- [ ] IoT设备数据集成
- [ ] 高级预警规则引擎
- [ ] 生产数据可视化
- [ ] 移动端应用
- [ ] 性能监控和优化

### 第三阶段 📋 (智能版)
- [ ] 深度学习异常检测
- [ ] 智能决策支持系统
- [ ] 自动化闭环控制
- [ ] 云端部署和扩展
- [ ] 多工厂协同管理
- [ ] 供应链集成
- [ ] 企业级权限管理
- [ ] 第三方ERP系统集成

### 代码质量

[![CI/CD](https://github.com/pgdev-company/ai-design-assistant/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/pgdev-company/ai-design-assistant/actions)
[![codecov](https://codecov.io/gh/pgdev-company/ai-design-assistant/branch/main/graph/badge.svg)](https://codecov.io/gh/pgdev-company/ai-design-assistant)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=pgdev-company_ai-design-assistant&metric=alert_status)](https://sonarcloud.io/dashboard?id=pgdev-company_ai-design-assistant)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](./CONTRIBUTING.md) 了解详细信息。

### 开发流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型注解（Type Hints）
- 编写单元测试和集成测试
- 更新相关文档和注释
- 遵循 Git 提交规范

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装代码格式化工具
pip install black isort flake8 mypy

# 运行代码检查
black src/
isort src/
flake8 src/
mypy src/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](./LICENSE) 文件了解详情。

## 👥 团队

- **项目负责人**: PinGao Team
- **技术负责人**: PMC智能追踪系统开发团队
- **产品经理**: 生产管理专家

## 🆘 支持

如果您遇到任何问题或有疑问，请通过以下方式联系我们：

- 📧 邮箱: support@pingao.com
- 🐛 问题报告: [GitHub Issues](https://github.com/pingao-company/pg-pmc-tracking/issues)
- 📖 文档: [在线文档](https://docs.pingao.com/pg-pmc-tracking)

## 🔧 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接配置和权限
   - 确认网络连接状态

2. **预警系统异常**
   - 检查IoT设备连接状态
   - 验证预警规则配置
   - 查看系统日志详情

3. **依赖安装失败**
   - 更新pip版本
   - 使用国内镜像源
   - 检查Python版本兼容性

更多详细信息请参考 [故障排除指南](./docs/06-故障排除/)

## 🔄 技术架构

本项目采用微服务架构设计，具有以下特性：

### 🏗️ 核心架构

- **AI引擎**: TensorFlow / PyTorch
- **数据库**: MySQL + MongoDB + Redis
- **消息队列**: RabbitMQ / Apache Kafka
- **IoT集成**: MQTT + RESTful API
- **数据处理**: Pandas + NumPy + SciPy
- **配置管理**: YAML + 环境变量

### 🛠️ 开发工具

- **代码质量**: Black, isort, Flake8, MyPy
- **测试框架**: Pytest + Coverage
- **日志系统**: Loguru + Rich
- **性能监控**: 内置性能分析器
- **安全加密**: Cryptography + 安全存储

### 📦 模块结构

```
src/
├── core/           # 核心应用逻辑
├── ai/             # AI算法和预测模型
├── database/       # 数据库操作和管理
├── scheduling/     # 智能排程算法
├── warning/        # 预警系统
├── tracking/       # 追踪和监控
├── config/         # 配置管理
├── ui/             # 用户界面
└── utils/          # 工具模块
```

### 🔧 扩展开发

```bash
# 添加新的AI算法模型
cp src/ai/lstm_model.py src/ai/custom_model.py

# 扩展预警规则
cp src/warning/basic_rules.py src/warning/custom_rules.py

# 添加新的IoT设备支持
cp src/tracking/basic_device.py src/tracking/custom_device.py
```

### 📋 定制化配置

- [ ] 配置数据库连接参数
- [ ] 设置AI模型训练参数
- [ ] 配置IoT设备接入
- [ ] 自定义预警规则
- [ ] 设置日志级别
- [ ] 配置性能监控
- [ ] 定制用户界面

通过微服务架构设计，系统具有良好的可扩展性和可维护性，便于后续功能扩展和定制开发。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和社区成员！

---

**PG-PMC智能追踪系统** - 让生产更智能，让管理更高效 🚀

<div align="center">
  <p>用 ❤️ 构建于3AI电器实业有限公司</p>
  <p>© 2024 PG-PMC Electric Appliance Co., Ltd. All rights reserved.</p>
</div>