# 3AI 工作室 - 智能化项目管理平台

<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Node.js-18+-brightgreen.svg" alt="Node.js">
  <img src="https://img.shields.io/badge/Python-3.11+-brightgreen.svg" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-blue.svg" alt="TypeScript">
</div>

## 📋 项目简介

**3AI 工作室项目的核心价值在于构建一个标准化、可复用的企业级项目开发框架模板。**

本项目既是一个完整的智能项目管理平台，更是一个经过精心设计的**项目开发框架模板**，所有的架构设计、工具配置、文档体系都围绕模板化复用这个核心理念来构建，为未来新项目的快速启动提供完整的基础架构。

### ✨ 核心特性

#### 🏗️ 模板化框架特性
- 📦 **开箱即用**: 零配置启动，完整的开发工具链
- 🎯 **标准化结构**: 规范化目录组织和统一命名规范
- 🚀 **快速启动**: 节省 80% 的项目初始化时间
- 📚 **文档完备**: 完整的开发指南和技术文档
- 🔧 **生产就绪**: 容器化部署和环境隔离
- ♻️ **可复用性**: 高内聚、低耦合的模块化设计

#### 💼 应用平台特性
- 🤖 **AI 驱动**: 智能任务分配、进度预测和风险评估
- 🎯 **项目管理**: 完整的项目生命周期管理
- 👥 **团队协作**: 实时协作和沟通工具
- 📊 **数据分析**: 深度项目数据分析和可视化
- 🔒 **安全可靠**: 企业级安全保障
- 🌐 **响应式设计**: 支持多设备访问

## 🏗️ 技术架构

### 前端技术栈
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全的 JavaScript
- **Vite** - 现代化构建工具
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Zustand** - 轻量级状态管理
- **React Query** - 数据获取和缓存

### 后端技术栈
- **FastAPI** - 现代化 Python Web 框架
- **SQLAlchemy** - Python SQL 工具包和 ORM
- **PostgreSQL** - 关系型数据库
- **Redis** - 内存数据库和缓存
- **Celery** - 分布式任务队列

### 开发工具
- **Docker** - 容器化部署
- **GitHub Actions** - CI/CD 流水线
- **ESLint & Prettier** - 代码质量工具
- **Jest & Pytest** - 测试框架
- **Husky** - Git 钩子管理

## 🚀 项目初始化脚本

本项目提供了一个位于 `tools/init_project.py` 的项目初始化脚本，旨在帮助您快速搭建一个符合规范的新项目骨架。

### 功能

- **创建标准目录结构**: 根据 `project_config.yaml` 中定义的 `init_project.core_directories` 和 `init_project.core_files` 自动生成核心目录和文件。
- **复制模板文件**: 如果在 `init_project.core_files` 中为文件指定了 `template`，脚本会从模板路径复制文件内容到新项目中。
- **初始化 Git 仓库**: 在新项目根目录下自动执行 `git init`。
- **灵活配置**: 通过命令行参数 `--name` 指定新项目的名称，通过 `--config` 指定配置文件路径（默认为 `docs/03-管理/project_config.yaml`）。

### 使用方法

1.  **确保环境**: Python 3.x 环境，并已安装 `PyYAML` 依赖 (通常在项目依赖中已包含)。
2.  **运行脚本**:
    在项目根目录 (`S:\3AI`)下执行以下命令：

    ```bash
    python -m tools.init_project --name <新项目名称>
    ```
    例如，要创建一个名为 `my_new_app` 的项目：
    ```bash
    python -m tools.init_project --name my_new_app
    ```
    新项目将在当前工作目录下创建 (例如 `S:\3AI/my_new_app`)。

3.  **自定义配置 (可选)**:
    如果您的项目配置文件不在默认位置，或者您想使用特定的配置文件，可以通过 `--config` 参数指定：
    ```bash
    python -m tools.init_project --name <新项目名称> --config path/to/your/custom_config.yaml
    ```

### 注意事项

-   脚本会检查目标项目目录是否已存在，如果存在且不为空，则会提示并可能中止以防止意外覆盖。
-   确保 `project_config.yaml` 文件中的 `init_project` 部分配置正确，特别是 `core_directories` 和 `core_files`。
-   如果 Git 初始化失败，请检查您的系统中是否已正确安装并配置了 Git。

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (可选)

### 本地开发

1. **克隆项目**
   ```bash
   git clone https://github.com/your-org/3ai-studio.git
   cd 3ai-studio
   ```

2. **环境配置**
   ```bash
   # 复制环境变量文件
   cp .env.example .env
   
   # 编辑环境变量
   nano .env
   ```

3. **安装依赖**
   ```bash
   # 运行初始化脚本
   chmod +x scripts/init-project.sh
   ./scripts/init-project.sh
   ```

4. **启动开发服务器**
   ```bash
   # 启动所有服务
   npm run dev
   
   # 或分别启动
   npm run dev:client  # 前端服务 (http://localhost:3000)
   npm run dev:server  # 后端服务 (http://localhost:8000)
   ```

### Docker 开发

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f
```

### VS Code 开发容器

1. 安装 "Remote - Containers" 扩展
2. 打开项目文件夹
3. 按 `Ctrl+Shift+P` 并选择 "Remote-Containers: Reopen in Container"

## 📚 文档

- [开发任务书](./docs/01-设计/开发任务书.md)
- [架构设计](./docs/02-架构设计/)
- [开发指南](./docs/03-开发指南/)
- [API 文档](./docs/04-API文档/)
- [部署指南](./docs/05-部署指南/)

## 🧪 测试

```bash
# 运行所有测试
npm test

# 运行前端测试
npm run test:client

# 运行后端测试
npm run test:server

# 生成覆盖率报告
npm run test:coverage
```

## 🔧 构建和部署

### 本地构建

```bash
# 构建前端
npm run build:client

# 构建后端
npm run build:server

# 构建所有
npm run build
```

### Docker 部署

```bash
# 构建生产镜像
docker build -t 3ai-studio .

# 启动生产环境
docker-compose up -d
```

## 📊 项目状态

### 开发进度

- [x] 项目初始化和配置
- [x] 基础架构搭建
- [x] 开发环境配置
- [x] CI/CD 流水线
- [ ] 用户认证系统
- [ ] 项目管理模块
- [ ] 任务管理系统
- [ ] AI 功能集成
- [ ] 数据分析面板

### 代码质量

[![CI/CD](https://github.com/your-org/3ai-studio/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-org/3ai-studio/actions)
[![codecov](https://codecov.io/gh/your-org/3ai-studio/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/3ai-studio)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=your-org_3ai-studio&metric=alert_status)](https://sonarcloud.io/dashboard?id=your-org_3ai-studio)

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](./CONTRIBUTING.md) 了解详细信息。

### 开发流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 遵循 ESLint 和 Prettier 配置
- 编写有意义的提交信息
- 添加适当的测试用例
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](./LICENSE) 文件了解详情。

## 👥 团队

- **项目负责人**: [您的姓名](mailto:your.email@example.com)
- **技术架构师**: [技术负责人](mailto:tech.lead@example.com)
- **前端开发**: [前端负责人](mailto:frontend@example.com)
- **后端开发**: [后端负责人](mailto:backend@example.com)

## 🆘 支持

如果您遇到任何问题或有疑问，请通过以下方式联系我们：

- 📧 邮箱: support@3ai-studio.com
- 💬 讨论: [GitHub Discussions](https://github.com/your-org/3ai-studio/discussions)
- 🐛 问题报告: [GitHub Issues](https://github.com/your-org/3ai-studio/issues)
- 📖 文档: [项目文档](https://docs.3ai-studio.com)

## 🔄 项目模板化使用

**这是本项目的核心价值所在！** 整个项目围绕模板化复用这个核心理念设计，为企业和团队提供标准化的项目开发框架：

### 📋 使用步骤

1. **复制项目目录**
   ```bash
   cp -r 3AI-Studio your-new-project
   cd your-new-project
   ```

2. **修改项目配置**
   - 更新 `package.json` 中的项目名称和描述
   - 修改 `README.md` 中的项目信息
   - 更新 `.env.example` 中的配置项
   - 调整 `docker-compose.yml` 中的服务名称

3. **重写项目文档**
   - 更新 `docs/01-项目规划/` 中的需求分析和项目目标
   - 重写 `docs/01-项目规划/项目实施行动计划.md`
   - 修改 `docs/02-技术设计/系统架构设计.md`
   - 调整技术路线和开发计划

4. **初始化新项目**
   ```bash
   # 运行项目初始化脚本
   ./scripts/init-project.sh
   
   # 安装依赖
   npm install
   pip install -r requirements.txt
   ```

### 🎯 框架优势

- ✅ **完整的开发环境配置** - Docker、VS Code Dev Container
- ✅ **标准化的项目结构** - 前后端分离、文档规范
- ✅ **自动化的 CI/CD 流水线** - GitHub Actions
- ✅ **代码质量保证** - ESLint、Prettier、测试框架
- ✅ **详细的开发文档** - 包含故障排除指南
- ✅ **健康检查和监控** - 生产环境就绪

通过使用这个模板，新项目可以快速启动，专注于业务逻辑开发，而无需重复搭建基础设施。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和社区成员！

---

<div align="center">
  <p>用 ❤️ 构建于 3AI 工作室</p>
  <p>© 2024 3AI Studio. All rights reserved.</p>
</div>