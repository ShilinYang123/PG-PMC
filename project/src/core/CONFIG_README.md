# 统一配置管理系统

本项目采用统一配置管理系统，整合了分散的配置文件和配置逻辑，提供了一套完整的配置管理解决方案。

## 🏗️ 系统架构

### 核心组件

1. **ConfigCenter** (`config_center.py`) - 统一配置管理中心
2. **ConfigMigration** (`config_migration.py`) - 配置迁移工具
3. **ConfigCLI** (`config_cli.py`) - 命令行管理工具
4. **ConfigManager** (`config/config_manager.py`) - 兼容层（已弃用）

### 配置文件结构

```
project/
├── config/
│   ├── default.yaml          # 默认配置
│   ├── settings.yaml          # 主配置文件
│   ├── user_settings.yaml     # 用户配置
│   └── README.md
├── .env                       # 环境变量
├── .env.local                 # 本地环境变量
└── .env.production            # 生产环境变量
```

## 🚀 快速开始

### 1. 基本使用

```python
from src.core.config_center import get_config_center, get_config, set_config

# 获取配置中心实例
config_center = get_config_center()

# 获取配置值
app_name = get_config("app.name")
server_port = get_config("server.port", 8000)

# 设置配置值
set_config("app.debug", True)
set_config("server.host", "0.0.0.0")

# 重新加载配置
config_center.reload_config()
```

### 2. 配置优先级

配置加载按以下优先级（高到低）：

1. **环境变量** - 最高优先级
2. **用户配置文件** (`user_settings.yaml`)
3. **主配置文件** (`settings.yaml`)
4. **默认配置文件** (`default.yaml`)
5. **内置默认值** - 最低优先级

### 3. 环境变量映射

环境变量使用下划线分隔，自动映射到配置键：

```bash
# 环境变量
APP_NAME=MyApp
SERVER_PORT=8080
DATABASE_SQLITE_PATH=/data/app.db

# 对应配置键
app.name
server.port
database.sqlite.path
```

## 🛠️ 配置管理

### 命令行工具

```bash
# 显示所有配置
python -m src.core.config_cli show

# 获取特定配置
python -m src.core.config_cli get app.name

# 设置配置值
python -m src.core.config_cli set app.debug true

# 验证配置
python -m src.core.config_cli validate

# 备份配置
python -m src.core.config_cli backup

# 恢复配置
python -m src.core.config_cli restore backup_20231201_120000.yaml

# 导出配置
python -m src.core.config_cli export --format json --output config.json

# 导入配置
python -m src.core.config_cli import config.json
```

### 配置迁移

```bash
# 扫描现有配置文件
python src/core/migrate_config.py --scan-only

# 干运行迁移（查看迁移计划）
python src/core/migrate_config.py --dry-run

# 执行迁移（带备份）
python src/core/migrate_config.py --backup --force
```

## 📝 配置文件格式

### YAML 配置文件

```yaml
# settings.yaml
app:
  name: "PG-Dev"
  version: "1.0.0"
  debug: false
  environment: "development"

server:
  host: "127.0.0.1"
  port: 8000
  workers: 4

database:
  type: "sqlite"
  sqlite:
    path: "data/app.db"
    timeout: 30
  postgresql:
    host: "localhost"
    port: 5432
    database: "pgdev"
    username: "postgres"
    password: "${DB_PASSWORD}"  # 环境变量引用

ai:
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"
    max_tokens: 4000
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet"
    max_tokens: 4000

storage:
  temp_dir: "temp"
  upload_dir: "uploads"
  data_dir: "data"
  max_file_size: 104857600  # 100MB
  allowed_extensions:
    - ".txt"
    - ".md"
    - ".json"
    - ".yaml"
```

### 环境变量文件

```bash
# .env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
WORKERS=4

# AI API 密钥
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 数据库配置
DB_TYPE=sqlite
DB_SQLITE_PATH=data/app.db
DB_PASSWORD=your_password

# Creo 集成
CREO_INSTALL_PATH=C:/PTC/Creo
CREO_TIMEOUT=300
CREO_WORK_DIR=temp/creo
```

## 🔧 高级功能

### 1. 配置验证

```python
from src.core.config_center import get_config_center

config_center = get_config_center()

# 添加验证规则
config_center.add_validation_rule(
    "server.port",
    lambda x: isinstance(x, int) and 1024 <= x <= 65535,
    "端口必须是1024-65535之间的整数"
)

# 验证配置
errors = config_center.validate_config()
if errors:
    for error in errors:
        print(f"验证错误: {error}")
```

### 2. 配置热重载

```python
# 监听配置文件变化并自动重载
config_center.enable_auto_reload()

# 手动重载
config_center.reload_config()
```

### 3. 配置备份和恢复

```python
# 创建备份
backup_file = config_center.backup_config()
print(f"备份已创建: {backup_file}")

# 恢复备份
config_center.restore_config(backup_file)
```

### 4. 配置导入导出

```python
# 导出配置
config_center.export_config("config_export.json", format="json")
config_center.export_config("config_export.yaml", format="yaml")

# 导入配置
config_center.import_config("config_import.json")
```

## 🔒 安全特性

### 1. 敏感信息加密

```python
# 配置中心自动处理敏感信息
# 支持环境变量引用
api_key = get_config("ai.openai.api_key")  # 自动从环境变量获取

# 支持加密存储
config_center.encrypt_sensitive_config("database.password", "secret123")
```

### 2. 配置访问控制

```python
# 只读配置项
config_center.set_readonly("app.version")

# 敏感配置项（不会在日志中显示）
config_center.mark_sensitive("ai.openai.api_key")
```

## 📊 监控和日志

### 配置变更日志

```python
# 配置变更会自动记录
# 查看变更历史
history = config_center.get_change_history()
for change in history:
    print(f"{change.timestamp}: {change.key} = {change.value}")
```

### 配置使用统计

```python
# 获取配置使用统计
stats = config_center.get_usage_stats()
print(f"最常访问的配置: {stats.most_accessed}")
print(f"未使用的配置: {stats.unused_configs}")
```

## 🚨 故障排除

### 常见问题

1. **配置文件不存在**
   ```
   解决方案: 运行配置迁移脚本或手动创建配置文件
   ```

2. **环境变量未生效**
   ```
   检查: 环境变量名称格式（使用下划线分隔）
   检查: .env 文件是否正确加载
   ```

3. **配置验证失败**
   ```
   检查: 配置值类型和格式
   检查: 必需配置项是否存在
   ```

### 调试模式

```python
# 启用调试模式
config_center.enable_debug()

# 查看配置加载过程
config_center.debug_config_loading()
```

## 🔄 迁移指南

### 从旧配置系统迁移

1. **备份现有配置**
   ```bash
   cp -r project/config project/config.backup
   ```

2. **运行迁移脚本**
   ```bash
   python src/core/migrate_config.py --backup --force
   ```

3. **更新代码引用**
   ```python
   # 旧方式
   from src.config.config_manager import ConfigManager
   config = ConfigManager().get_setting("app.name")
   
   # 新方式
   from src.core.config_center import get_config
   config = get_config("app.name")
   ```

4. **测试和验证**
   ```bash
   python -m src.core.config_cli validate
   ```

## 📚 API 参考

### ConfigCenter 类

```python
class ConfigCenter:
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]
    def get_config(self, key: str, default: Any = None) -> Any
    def set_config(self, key: str, value: Any, save: bool = True) -> bool
    def reload_config(self) -> bool
    def backup_config(self) -> str
    def restore_config(self, backup_file: str) -> bool
    def validate_config(self) -> List[str]
    def export_config(self, file_path: str, format: str = "yaml") -> bool
    def import_config(self, file_path: str) -> bool
```

### 便捷函数

```python
def get_config_center() -> ConfigCenter
def get_config(key: str, default: Any = None) -> Any
def set_config(key: str, value: Any, save: bool = True) -> bool
def reload_config() -> bool
```

## 🤝 贡献指南

1. 遵循现有代码风格
2. 添加适当的测试
3. 更新文档
4. 提交前运行配置验证

## 📄 许可证

本项目采用 MIT 许可证。