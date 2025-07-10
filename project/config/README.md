# PG-Dev AI设计助理 - 配置管理

本目录包含PG-Dev AI设计助理的所有配置文件。配置系统采用分层设计，支持环境变量覆盖，确保灵活性和安全性。

## 配置文件结构

```
config/
├── settings.yaml          # 主配置文件
├── default.yaml           # 默认配置文件（备份和参考）
├── user_settings.yaml     # 用户自定义配置模板
└── README.md              # 本文档

项目根目录/
├── .env                   # 主环境变量文件
├── .env.local             # 本地开发环境变量
├── .env.production        # 生产环境变量
└── .env.template          # 环境变量模板（在docs/03-管理/）
```

## 配置加载优先级

配置系统按以下优先级加载配置（后者覆盖前者）：

1. **内置默认配置** - 代码中定义的默认值
2. **default.yaml** - 默认配置文件
3. **settings.yaml** - 主配置文件
4. **user_settings.yaml** - 用户自定义配置
5. **环境变量** - 最高优先级

### 环境变量加载顺序

1. `.env.{ENVIRONMENT}` - 特定环境的配置（如 .env.production）
2. `.env` - 通用环境变量
3. `.env.local` - 本地开发环境变量（最高优先级）

## 配置文件说明

### settings.yaml
主配置文件，包含应用的核心配置。结构如下：

```yaml
# 应用基础设置
app:
  name: "PG-Dev AI设计助理"
  version: "1.0.0"
  debug: false
  log_level: "INFO"
  environment: "development"

# 服务器设置
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1
  reload: true

# AI模型设置
ai:
  openai:
    api_key: ""  # 通过环境变量设置
    model: "gpt-4"
    max_tokens: 2048
    temperature: 0.7
    timeout: 30
  anthropic:
    api_key: ""  # 通过环境变量设置
    model: "claude-3-sonnet-20240229"
    max_tokens: 2048
    temperature: 0.7
    timeout: 30
  default_provider: "openai"

# Creo集成设置
creo:
  install_path: "C:\\Program Files\\PTC\\Creo 7.0\\Common Files\\x86e_win64\\bin"
  connection_timeout: 30
  operation_timeout: 60
  auto_start: false

# 数据库设置
database:
  type: "sqlite"
  sqlite:
    path: "data/pgdev.db"
    timeout: 30
  postgresql:
    host: "localhost"
    port: 5432
    name: "pgdev"
    user: "pgdev_user"
    password: ""  # 通过环境变量设置

# 文件存储设置
storage:
  temp_dir: "temp"
  upload_dir: "uploads"
  backup_dir: "backups"
  max_file_size: 100  # MB

# 日志设置
logging:
  level: "INFO"
  log_file: "logs/pgdev_ai_assistant.log"
  max_file_size: 10  # MB
  backup_count: 5

# 安全设置
security:
  secret_key: ""  # 通过环境变量设置
  jwt_secret_key: ""  # 通过环境变量设置
  session_timeout: 60  # 分钟
  encrypt_api_keys: true

# 性能设置
performance:
  cache:
    enabled: true
    ttl: 3600
    max_size: 1000
  concurrency:
    max_workers: 4
    thread_pool_size: 4
  memory_limit: 2048  # MB

# 功能开关
features:
  chat_interface: true
  design_interpreter: true
  parameter_parser: true
  geometry_creator: true
  real_time_preview: true
  file_upload: true
  batch_processing: false

# 开发设置
development:
  hot_reload: true
  debug_toolbar: true
  profiling: false
  mock_creo: false
  test_mode: false

# UI设置
ui:
  theme: "dark"
  language: "zh-CN"
  window_width: 1200
  window_height: 800
```

### 环境变量

敏感信息（如API密钥、密码等）应通过环境变量设置，而不是直接写在配置文件中。

主要环境变量：

```bash
# 应用设置
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development

# 服务器设置
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
WORKERS=1

# AI API密钥
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Creo设置
CREO_INSTALL_PATH="C:\Program Files\PTC\Creo 7.0\Common Files\x86e_win64\bin"
CREO_AUTO_START=false

# 数据库设置
DATABASE_TYPE=sqlite
DATABASE_PATH=data/pgdev.db
# PostgreSQL（如果使用）
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=pgdev
DATABASE_USER=pgdev_user
DATABASE_PASSWORD=your_password_here

# 安全设置
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# 功能开关
ENABLE_CHAT_INTERFACE=true
ENABLE_DESIGN_INTERPRETER=true
ENABLE_REAL_TIME_PREVIEW=true

# 开发设置
HOT_RELOAD=true
DEBUG_TOOLBAR=true
PROFILING=false
```

## 使用方法

### 1. 初始化配置

```bash
# 初始化所有配置文件
python scripts/init_config.py

# 强制覆盖已存在的文件
python scripts/init_config.py --force

# 仅创建用户配置模板
python scripts/init_config.py --template-only
```

### 2. 检查配置完整性

```bash
# 检查配置文件完整性和正确性
python scripts/check_config.py
```

### 3. 在代码中使用配置

```python
from src.config.config_manager import ConfigManager

# 获取配置管理器实例
config_manager = ConfigManager()

# 加载配置
settings = config_manager.get_settings()

# 使用配置
print(f"应用名称: {settings.app.name}")
print(f"服务器端口: {settings.server.port}")
print(f"OpenAI模型: {settings.ai.openai.model}")

# 保存配置
config_manager.save_settings(settings)
```

### 4. 环境特定配置

```bash
# 设置环境
export ENVIRONMENT=production

# 或在Windows中
set ENVIRONMENT=production

# 应用会自动加载 .env.production 文件
```

## 配置验证

配置系统包含内置验证功能，会检查：

- 必需字段是否存在
- 数值范围是否合理
- 文件路径是否有效
- API密钥是否配置
- 端口号是否在有效范围内

验证错误会在应用启动时显示，并记录到日志中。

## 安全注意事项

1. **永远不要将API密钥等敏感信息提交到版本控制系统**
2. **使用环境变量存储敏感信息**
3. **定期轮换API密钥和密码**
4. **在生产环境中禁用调试模式**
5. **设置适当的文件权限**

## 故障排除

### 常见问题

1. **配置文件语法错误**
   - 检查YAML语法是否正确
   - 注意缩进和引号

2. **环境变量未生效**
   - 确认环境变量名称正确
   - 重启应用程序
   - 检查 .env 文件是否存在

3. **API密钥无效**
   - 验证API密钥是否正确
   - 检查API服务是否可用
   - 确认账户余额充足

4. **Creo连接失败**
   - 检查Creo安装路径
   - 确认Creo版本兼容性
   - 验证防火墙设置

### 调试技巧

1. **启用调试模式**
   ```bash
   export DEBUG=true
   ```

2. **查看详细日志**
   ```bash
   export LOG_LEVEL=DEBUG
   ```

3. **使用配置检查脚本**
   ```bash
   python scripts/check_config.py
   ```

## 配置迁移

如果需要从旧版本配置迁移，请：

1. 备份现有配置文件
2. 运行初始化脚本
3. 手动迁移自定义设置
4. 验证配置正确性

## 扩展配置

要添加新的配置项：

1. 在 `src/config/settings.py` 中添加新的数据类
2. 更新主配置文件模板
3. 添加环境变量映射（如需要）
4. 更新验证逻辑
5. 更新文档

## 支持

如果遇到配置相关问题，请：

1. 查看本文档
2. 运行配置检查脚本
3. 查看应用日志
4. 联系开发团队