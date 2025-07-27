# PG-PMC 统一配置管理中心

## 概述

PG-PMC 统一配置管理中心是一个完整的配置管理解决方案，提供了从基础配置管理到高级功能（如配置验证、热重载、模板生成、同步管理等）的全套工具。

## 主要特性

### 🔧 核心功能
- **统一配置管理**: 集中管理所有配置信息
- **环境管理**: 支持开发、测试、生产等多环境配置
- **路径管理**: 统一管理项目路径和目录结构
- **配置验证**: 自动验证配置的完整性和正确性

### 🚀 高级功能
- **配置热重载**: 实时监控配置文件变更并自动重载
- **配置模板**: 生成不同环境和场景的配置模板
- **配置同步**: 在不同环境和服务之间同步配置
- **配置迁移**: 自动迁移和升级配置格式
- **命令行工具**: 提供完整的CLI工具集

### 📊 管理功能
- **健康检查**: 实时监控配置系统状态
- **备份恢复**: 配置的备份和恢复功能
- **版本控制**: 配置变更的版本管理
- **审计日志**: 配置操作的完整审计记录

## 快速开始

### 1. 基本使用

```python
from config import quick_setup, get_config, set_config

# 快速设置配置系统
quick_setup('development')

# 获取配置
app_name = get_config('project.name')
db_url = get_config('database.url')

# 设置配置
set_config('app.debug', True)
```

### 2. 环境管理

```python
from config import (
    set_environment, 
    get_current_environment,
    is_development, 
    is_production
)

# 切换环境
set_environment('production')

# 检查当前环境
print(f"当前环境: {get_current_environment()}")
print(f"是否生产环境: {is_production()}")
```

### 3. 配置验证

```python
from config import validate_config, validate_paths

# 验证配置
if validate_config():
    print("✅ 配置验证通过")
else:
    print("❌ 配置验证失败")

# 验证路径
path_result = validate_paths()
print(f"有效路径: {len(path_result['valid'])}")
print(f"缺失路径: {len(path_result['missing'])}")
```

### 4. 配置监控

```python
from config import (
    start_config_watching,
    stop_config_watching,
    add_config_change_callback
)

# 定义变更回调
def on_config_change(file_path, event_type):
    print(f"配置文件 {file_path} 发生 {event_type} 事件")

# 添加回调并启动监控
add_config_change_callback(on_config_change)
start_config_watching()

# 停止监控
stop_config_watching()
```

## 模块结构

```
config/
├── __init__.py              # 主入口，导出所有公共接口
├── config_manager.py        # 核心配置管理器
├── environment.py           # 环境管理
├── path_manager.py          # 路径管理
├── settings.py              # 应用设置管理
├── validator.py             # 基础配置验证器
├── config_validator.py      # 高级配置验证器
├── config_migrator.py       # 配置迁移工具
├── default_config.py        # 默认配置提供者
├── config_cli.py            # 命令行工具
├── config_watcher.py        # 配置热重载监控
├── config_templates.py      # 配置模板生成器
├── config_sync.py           # 配置同步管理器
├── example_usage.py         # 使用示例
└── README.md               # 本文档
```

## 详细功能说明

### 配置管理器 (ConfigManager)

核心配置管理器负责：
- 加载和保存配置文件
- 配置的获取和设置
- 配置格式的标准化
- 配置的导出和导入

```python
from config import get_config_manager

config_manager = get_config_manager()
config_manager.load_config('custom_config.yaml')
config_manager.save_config()
```

### 环境管理器 (EnvironmentManager)

环境管理器提供：
- 多环境配置支持
- 环境间的配置切换
- 环境特定的配置覆盖
- 环境变量的管理

```python
from config import get_environment_manager

env_manager = get_environment_manager()
env_manager.set_environment('testing')
env_config = env_manager.get_environment_config()
```

### 路径管理器 (PathManager)

路径管理器负责：
- 项目路径的统一管理
- 路径的验证和创建
- 相对路径和绝对路径的转换
- 路径权限的检查

```python
from config import get_path_manager, get_project_path

# 获取项目路径
project_root = get_project_path('root')
logs_dir = get_project_path('logs')
config_dir = get_project_path('config')

# 路径管理器操作
path_manager = get_path_manager()
path_manager.create_missing_directories()
```

### 配置验证器 (ConfigValidator)

配置验证器提供：
- 配置完整性检查
- 配置格式验证
- 依赖关系验证
- 安全性检查

```python
from config import NewConfigValidator

validator = NewConfigValidator()
result = validator.validate_all()

if result['valid']:
    print("✅ 所有配置验证通过")
else:
    print(f"❌ 发现 {len(result['errors'])} 个错误")
    for error in result['errors']:
        print(f"  - {error}")
```

### 配置迁移器 (ConfigMigrator)

配置迁移器负责：
- 旧配置格式的迁移
- 配置结构的升级
- 数据的转换和清理
- 迁移过程的回滚

```python
from config import ConfigMigrator

migrator = ConfigMigrator()
migrator.migrate_alembic_config()
migrator.create_env_file()
```

### 配置监控器 (ConfigWatcher)

配置监控器提供：
- 实时文件监控
- 配置变更检测
- 自动重载机制
- 变更事件回调

```python
from config import ConfigWatcher, get_config_watcher

watcher = get_config_watcher()
watcher.start_watching()

# 添加自定义回调
def my_callback(file_path, event_type):
    print(f"配置变更: {file_path}")

watcher.add_callback(my_callback)
```

### 配置模板生成器 (ConfigTemplateGenerator)

模板生成器支持：
- 多种环境模板
- 自定义模板创建
- 模板的保存和加载
- 批量模板生成

```python
from config import ConfigTemplateGenerator, generate_template

# 生成开发环境模板
dev_template = generate_template('development')

# 生成生产环境模板
prod_template = generate_template('production')

# 生成Docker模板
docker_template = generate_template('docker')
```

### 配置同步管理器 (ConfigSyncManager)

同步管理器提供：
- 多目标同步支持
- 双向同步机制
- 同步历史记录
- 冲突解决策略

```python
from config import ConfigSyncManager, get_sync_manager

sync_manager = get_sync_manager()

# 添加同步目标
sync_manager.add_sync_target('file', '/path/to/backup')
sync_manager.add_sync_target('git', 'https://github.com/user/config-repo')

# 执行同步
sync_manager.sync_to_target('file')
sync_manager.sync_from_target('git')
```

## 命令行工具

配置管理中心提供了完整的CLI工具：

```bash
# 显示当前配置
python -m config.config_cli show

# 验证配置
python -m config.config_cli validate

# 迁移配置
python -m config.config_cli migrate

# 创建.env文件
python -m config.config_cli create-env

# 导出配置
python -m config.config_cli export --format json

# 显示路径信息
python -m config.config_cli paths

# 健康检查
python -m config.config_cli health

# 重置配置
python -m config.config_cli reset

# 备份配置
python -m config.config_cli backup
```

## 配置文件格式

### 主配置文件 (project_config.yaml)

```yaml
project:
  name: "PG-PMC"
  version: "1.0.0"
  description: "项目管理中心"

environment:
  current: "development"
  debug: true
  
database:
  development:
    url: "sqlite:///./dev.db"
    echo: true
  production:
    url: "postgresql://user:pass@localhost/prod"
    echo: false

server:
  host: "0.0.0.0"
  port: 8000
  workers: 1

security:
  secret_key: "your-secret-key"
  algorithm: "HS256"
  access_token_expire_minutes: 30

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
  max_size: "10MB"
  backup_count: 5
```

### 环境变量文件 (.env)

```bash
# 项目配置
PG_PMC_PROJECT_NAME=PG-PMC
PG_PMC_VERSION=1.0.0
PG_PMC_ENVIRONMENT=development

# 数据库配置
PG_PMC_DATABASE_URL=sqlite:///./dev.db
PG_PMC_DATABASE_ECHO=true

# 服务器配置
PG_PMC_SERVER_HOST=0.0.0.0
PG_PMC_SERVER_PORT=8000

# 安全配置
PG_PMC_SECRET_KEY=your-secret-key
PG_PMC_ALGORITHM=HS256
```

## 最佳实践

### 1. 配置组织

- 使用分层配置结构
- 将敏感信息放在环境变量中
- 为不同环境创建专门的配置段
- 使用有意义的配置键名

### 2. 环境管理

- 明确区分开发、测试、生产环境
- 使用环境特定的配置覆盖
- 避免在代码中硬编码环境相关配置
- 使用环境变量控制敏感配置

### 3. 安全考虑

- 不要在配置文件中存储明文密码
- 使用环境变量或密钥管理服务
- 定期轮换密钥和令牌
- 限制配置文件的访问权限

### 4. 性能优化

- 缓存频繁访问的配置
- 避免在热路径中进行配置验证
- 使用配置预加载减少I/O操作
- 合理设置配置监控的检查间隔

### 5. 维护管理

- 定期备份配置文件
- 使用版本控制管理配置变更
- 建立配置变更的审批流程
- 监控配置系统的健康状态

## 故障排除

### 常见问题

1. **配置文件找不到**
   ```python
   # 检查配置文件路径
   from config import get_config_manager
   config_manager = get_config_manager()
   print(f"配置文件路径: {config_manager.config_file}")
   ```

2. **路径权限错误**
   ```python
   # 检查路径权限
   from config import validate_paths
   result = validate_paths()
   if result['permission_errors']:
       print("权限错误的路径:")
       for path in result['permission_errors']:
           print(f"  - {path}")
   ```

3. **配置验证失败**
   ```python
   # 详细的配置验证
   from config import NewConfigValidator
   validator = NewConfigValidator()
   result = validator.validate_all()
   
   if not result['valid']:
       print("配置错误:")
       for error in result['errors']:
           print(f"  - {error}")
   ```

4. **环境切换问题**
   ```python
   # 检查环境状态
   from config import get_current_environment, get_system_status
   print(f"当前环境: {get_current_environment()}")
   
   status = get_system_status()
   print(f"系统状态: {status['overall_health']}")
   ```

### 调试模式

启用调试模式获取更多信息：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from config import quick_setup
quick_setup('development', enable_validation=True)
```

### 重置配置

如果配置系统出现严重问题，可以重置：

```python
from config import cleanup_config_system, initialize_config_system

# 清理现有配置
cleanup_config_system()

# 重新初始化
result = initialize_config_system(auto_migrate=True)
if result['success']:
    print("✅ 配置系统重置成功")
```

## 扩展开发

### 自定义配置验证器

```python
from config.config_validator import ConfigValidator

class CustomValidator(ConfigValidator):
    def validate_custom_rules(self) -> dict:
        """自定义验证规则"""
        errors = []
        warnings = []
        
        # 添加自定义验证逻辑
        config = self.config_manager.get_config()
        
        if not config.get('custom_section'):
            errors.append("缺少自定义配置段")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
```

### 自定义同步目标

```python
from config.config_sync import ConfigSyncManager, SyncTarget

class CustomSyncTarget(SyncTarget):
    def __init__(self, target_config: dict):
        super().__init__('custom', target_config)
    
    def push_config(self, config: dict) -> bool:
        """推送配置到自定义目标"""
        # 实现自定义推送逻辑
        return True
    
    def pull_config(self) -> dict:
        """从自定义目标拉取配置"""
        # 实现自定义拉取逻辑
        return {}
```

## 版本历史

- **v1.0.0** (当前版本)
  - 完整的配置管理功能
  - 环境管理和路径管理
  - 配置验证和迁移
  - 配置热重载和监控
  - 配置模板和同步
  - 命令行工具

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

- 项目主页: [PG-PMC](https://github.com/your-org/pg-pmc)
- 问题反馈: [Issues](https://github.com/your-org/pg-pmc/issues)
- 邮箱: support@pg-pmc.com

---

**PG-PMC 统一配置管理中心** - 让配置管理变得简单而强大！