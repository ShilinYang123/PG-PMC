# PG-Dev AI设计助理 - 基于Creo的自然语言小家电设计系统

<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Python-3.11+-brightgreen.svg" alt="Python">
  <img src="https://img.shields.io/badge/Creo-API-orange.svg" alt="Creo API">
  <img src="https://img.shields.io/badge/AI-GPT4%20%7C%20Claude-purple.svg" alt="AI">
</div>

## 📋 项目简介

**PG-Dev AI设计助理是一个革命性的CAD自动化系统，通过自然语言交互直接控制Creo软件进行3D建模。**

本系统为江门市品高电器实业有限公司量身定制，旨在降低CAD操作门槛，提升产品设计效率。设计师只需用自然语言描述设计需求，AI助理即可自动在Creo中生成相应的3D模型，实现从设计想法到3D模型的无缝转换。

### ✨ 核心特性

#### 🎯 自然语言交互
- **智能语言理解**：基于GPT-4/Claude等大语言模型，准确理解设计意图
- **多模态输入支持**：支持文字描述、草图识别、参数输入等多种交互方式
- **上下文记忆**：保持对话历史，支持渐进式设计和修改
- **专业术语识别**：针对小家电行业优化，理解专业设计术语

#### 🔧 Creo API集成
- **深度API集成**：基于Creo COM接口和Pro/TOOLKIT，实现完整的建模控制
- **实时操作反馈**：同步显示建模过程，提供即时的视觉反馈
- **参数化建模**：支持参数驱动的智能建模，便于后续修改
- **装配体管理**：自动生成装配关系，支持复杂产品结构

#### 🏗️ 智能建模引擎
- **几何体自动生成**：根据描述自动创建基础几何体和复杂特征
- **设计规则引擎**：内置小家电设计规范，确保设计合规性
- **材料工艺建议**：基于产品类型推荐合适的材料和工艺
- **工程图自动化**：自动生成标准工程图纸和技术文档

## 🏗️ 技术架构

### 核心技术栈
- **Python 3.11+** - 主要开发语言
- **Creo API** - CAD软件集成接口
  - COM接口 (pywin32, comtypes)
  - Pro/TOOLKIT集成
- **AI语言模型** - 自然语言处理
  - OpenAI GPT-4
  - Anthropic Claude
  - 本地Transformers模型

### CAD集成层
- **Windows COM** - Creo软件控制
- **几何计算** - OpenCASCADE, FreeCAD
- **参数解析** - 自然语言到CAD参数转换
- **实时同步** - 建模过程可视化

### 开发工具
- **代码质量** - Black, Flake8, MyPy, Bandit
- **测试框架** - Pytest, Coverage
- **版本控制** - Git, Pre-commit hooks
- **文档生成** - 自动化技术文档

## 🚀 快速开始

### 环境要求

- **操作系统**：Windows 10/11 (64位)
- **Python**：3.11+ 
- **Creo软件**：Creo Parametric 7.0+
- **内存**：建议16GB以上
- **显卡**：支持OpenGL的独立显卡

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/pingao-company/ai-design-assistant.git
cd ai-design-assistant

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件，配置API密钥和Creo路径

# 5. 测试Creo连接
python src/creo/creo_connector.py --test
```

### 配置说明

#### 1. 环境变量配置 (.env)
```bash
# AI模型配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
AI_MODEL=gpt-4  # 或 claude-3-sonnet

# Creo配置
CREO_INSTALL_PATH=C:\Program Files\PTC\Creo 9.0.0.0
CREO_WORKING_DIR=C:\CreoWork
CREO_CONNECTION_TIMEOUT=30

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/ai_assistant.log
```

#### 2. Creo软件配置
- 确保Creo Parametric已正确安装
- 启用COM接口支持
- 配置工作目录权限

### 使用方法

#### 1. 启动AI设计助理
```bash
# 启动主程序
python src/main.py

# 或使用聊天界面
python src/ui/chat_interface.py
```

#### 2. 基本使用示例
```python
from src.core.ai_assistant import AIDesignAssistant

# 初始化助理
assistant = AIDesignAssistant()

# 连接Creo
assistant.connect_creo()

# 自然语言建模
response = assistant.process_command(
    "创建一个直径50mm，高度100mm的圆柱体"
)

print(response.message)
```

#### 3. 支持的设计指令
- **基础几何体**："创建一个长100宽50高30的长方体"
- **圆柱体**："做一个直径80高度120的圆柱"
- **特征操作**："在顶面添加一个直径20的圆孔"
- **材料设置**："将材料设置为ABS塑料"
- **装配操作**："将零件A与零件B装配"

## 📚 文档

- [开发任务书](./docs/01-设计/开发任务书.md)
- [技术方案](./docs/02-架构设计/技术方案.md)
- [系统架构设计](./docs/02-架构设计/系统架构设计.md)
- [API 文档](./docs/04-API文档/)
- [用户手册](./docs/05-用户手册/)
- [故障排除指南](./docs/06-故障排除/)

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/

# 生成覆盖率报告
python -m pytest --cov=src tests/

# 测试Creo连接
python tests/test_creo_connection.py

# 测试AI模型
python tests/test_ai_models.py
```

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
- [x] 核心模块开发（AI、Creo、几何、配置）
- [x] 工具模块开发（文件、验证、加密、性能）
- [x] 依赖管理和环境配置
- [x] CI/CD 流水线
- 🚧 测试用例编写
- ⏳ 用户界面优化
- ⏳ 性能调优和稳定性测试
- ⏳ 生产环境部署

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
- **技术负责人**: AI设计助理开发团队
- **产品经理**: 小家电设计专家

## 🆘 支持

如果您遇到任何问题或有疑问，请通过以下方式联系我们：

- 📧 邮箱: support@pingao.com
- 🐛 问题报告: [GitHub Issues](https://github.com/pingao-company/ai-design-assistant/issues)
- 📖 文档: [在线文档](https://docs.pingao.com/ai-design-assistant)

## 🔧 故障排除

### 常见问题

1. **Creo连接失败**
   - 检查Creo是否正在运行
   - 验证COM接口是否启用
   - 确认工作目录权限

2. **AI模型响应慢**
   - 检查网络连接
   - 验证API密钥配置
   - 考虑使用本地模型

3. **依赖安装失败**
   - 更新pip版本
   - 使用国内镜像源
   - 检查Python版本兼容性

更多详细信息请参考 [故障排除指南](./docs/06-故障排除/)

## 🔄 技术架构

本项目采用模块化架构设计，具有以下特性：

### 🏗️ 核心架构

- **AI引擎**: OpenAI GPT-4 / Anthropic Claude
- **CAD集成**: Creo Parametric COM API
- **自然语言处理**: Transformers + LangChain
- **几何计算**: NumPy + SciPy + OpenCASCADE
- **数据处理**: Pandas + Pydantic
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
├── ai/             # AI和自然语言处理
├── creo/           # Creo API集成
├── geometry/       # 几何计算和建模
├── config/         # 配置管理
├── ui/             # 用户界面
└── utils/          # 工具模块
```

### 🔧 扩展开发

```bash
# 添加新的AI模型支持
cp src/ai/openai_client.py src/ai/custom_model.py

# 扩展几何体类型
cp src/geometry/cylinder.py src/geometry/custom_shape.py

# 添加新的Creo功能
cp src/creo/basic_operations.py src/creo/advanced_operations.py
```

### 📋 定制化配置

- [ ] 配置AI模型API密钥
- [ ] 设置Creo安装路径
- [ ] 配置工作目录权限
- [ ] 自定义几何体库
- [ ] 设置日志级别
- [ ] 配置性能监控
- [ ] 定制用户界面

通过模块化设计，系统具有良好的可扩展性和可维护性，便于后续功能扩展和定制开发。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和社区成员！

---

**PG-Dev AI设计助理** - 让设计更智能，让创造更简单 🚀

<div align="center">
  <p>用 ❤️ 构建于江门市品高电器实业有限公司</p>
  <p>© 2024 PG-Dev Electric Appliance Co., Ltd. All rights reserved.</p>
</div>