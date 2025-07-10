#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 配置设置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AppSettings:
    """应用基础设置"""
    name: str = "PG-Dev AI设计助理"
    version: str = "1.0.0"
    description: str = "基于AI的Creo参数化设计助理"
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"  # development, production, testing


@dataclass
class ServerSettings:
    """服务器设置"""
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = True
    access_log: bool = True
    

@dataclass
class SQLiteSettings:
    """SQLite数据库设置"""
    path: str = "data/pgdev.db"
    timeout: int = 30
    check_same_thread: bool = False
    

@dataclass
class PostgreSQLSettings:
    """PostgreSQL数据库设置"""
    host: str = "localhost"
    port: int = 5432
    name: str = "pgdev"
    user: str = "pgdev_user"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    

@dataclass
class DatabaseSettings:
    """数据库设置"""
    type: str = "sqlite"  # sqlite, postgresql
    sqlite: SQLiteSettings = field(default_factory=SQLiteSettings)
    postgresql: PostgreSQLSettings = field(default_factory=PostgreSQLSettings)
    

@dataclass
class StorageSettings:
    """文件存储设置"""
    temp_dir: str = "temp"
    upload_dir: str = "uploads"
    backup_dir: str = "backups"
    max_file_size: int = 100  # MB
    allowed_extensions: List[str] = field(
        default_factory=lambda: [".prt", ".asm", ".drw", ".step", ".stp", ".iges", ".igs", ".stl"]
    )
    

@dataclass
class CreoSettings:
    """Creo相关设置"""
    install_path: str = r"C:\Program Files\PTC\Creo 7.0\Common Files\x86e_win64\bin"
    executable: str = "parametric.exe"
    startup_args: List[str] = field(
        default_factory=lambda: ["-g:no_graphics", "-i:rpc_input"]
    )
    connection_timeout: int = 30
    operation_timeout: int = 60
    max_retries: int = 3
    working_directory: str = r"C:\PG-Dev\CreoWork"
    config_file: str = "config.pro"
    startup_mode: str = "windowed"  # windowed, minimized, hidden
    api_version: str = "7.0"
    auto_start: bool = False
    auto_save: bool = True
    auto_save_interval: int = 5
    unit_system: str = "mmNs"  # mmNs, mmKs, inlbm, inlbf
    default_material: str = "PTC_SYSTEM_MTRL_STEEL"


@dataclass
class OpenAISettings:
    """OpenAI相关设置"""
    api_key: str = ""
    model: str = "gpt-4"
    base_url: str = "https://api.openai.com/v1"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AnthropicSettings:
    """Anthropic相关设置"""
    api_key: str = ""
    model: str = "claude-3-sonnet-20240229"
    base_url: str = "https://api.anthropic.com"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AISettings:
    """AI相关设置"""
    openai: OpenAISettings = field(default_factory=OpenAISettings)
    anthropic: AnthropicSettings = field(default_factory=AnthropicSettings)
    
    # 通用设置
    default_provider: str = "openai"  # openai, anthropic
    language: str = "zh-CN"  # zh-CN, en-US
    
    # 设计知识库
    knowledge_base_path: str = "data/knowledge_base"
    
    # 缓存设置
    enable_cache: bool = True
    cache_size: int = 1000
    cache_ttl: int = 3600  # 秒


@dataclass
class UISettings:
    """用户界面设置"""

    # 主题
    theme: str = "dark"  # dark, light, auto

    # 语言
    language: str = "zh-CN"

    # 字体设置
    font_family: str = "Microsoft YaHei"
    font_size: int = 12

    # 窗口设置
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False

    # 聊天界面设置
    chat_history_limit: int = 100
    auto_scroll: bool = True
    show_timestamps: bool = True

    # 3D预览设置
    enable_3d_preview: bool = True
    preview_quality: str = "medium"  # low, medium, high

    # 快捷键
    shortcuts: Dict[str, str] = field(
        default_factory=lambda: {
            "new_chat": "Ctrl+N",
            "save_model": "Ctrl+S",
            "undo": "Ctrl+Z",
            "redo": "Ctrl+Y",
            "zoom_fit": "F",
            "toggle_preview": "F3",
        }
    )

    # 通知设置
    enable_notifications: bool = True
    notification_sound: bool = False


@dataclass
class LoggingSettings:
    """日志设置"""

    # 日志级别
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # 日志文件路径
    log_file: str = "logs/pgdev_ai_assistant.log"

    # 日志格式
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 日志文件大小限制（MB）
    max_file_size: int = 10

    # 保留的日志文件数量
    backup_count: int = 5

    # 是否输出到控制台
    console_output: bool = True

    # 是否启用彩色输出
    colored_output: bool = True


@dataclass
class SecuritySettings:
    """安全设置"""

    # API密钥加密
    encrypt_api_keys: bool = True

    # 加密密钥
    encryption_key: str = ""

    # 会话超时（分钟）
    session_timeout: int = 60

    # 最大文件大小（MB）
    max_file_size: int = 100

    # 允许的文件类型
    allowed_file_types: List[str] = field(
        default_factory=lambda: [
            ".prt",
            ".asm",
            ".drw",
            ".step",
            ".stp",
            ".iges",
            ".igs",
            ".stl",
        ]
    )

    # 工作目录限制
    restrict_working_directory: bool = True

    # 备份设置
    auto_backup: bool = True
    backup_interval: int = 30  # 分钟
    max_backups: int = 10


@dataclass
class CacheSettings:
    """缓存设置"""
    enabled: bool = True
    ttl: int = 3600  # 秒
    max_size: int = 1000
    

@dataclass
class ConcurrencySettings:
    """并发设置"""
    max_workers: int = 4
    thread_pool_size: int = 4
    enable_async: bool = True
    

@dataclass
class PerformanceSettings:
    """性能设置"""
    cache: CacheSettings = field(default_factory=CacheSettings)
    concurrency: ConcurrencySettings = field(default_factory=ConcurrencySettings)
    
    # 内存和资源限制
    memory_limit: int = 2048  # MB
    max_file_size: int = 100  # MB
    
    # 几何处理
    geometry_simplification_threshold: float = 0.01
    render_quality: str = "medium"  # low, medium, high, ultra
    
    # 预加载设置
    preload_models: bool = False
    preload_textures: bool = False
    

@dataclass
class FeaturesSettings:
    """功能开关设置"""
    chat_interface: bool = True
    design_interpreter: bool = True
    parameter_parser: bool = True
    geometry_creator: bool = True
    real_time_preview: bool = True
    file_upload: bool = True
    batch_processing: bool = False
    

@dataclass
class DevelopmentSettings:
    """开发设置"""
    hot_reload: bool = True
    debug_toolbar: bool = True
    profiling: bool = False
    mock_creo: bool = False
    test_mode: bool = False


@dataclass
class Settings:
    """主配置类"""
    
    # 各模块设置
    app: AppSettings = field(default_factory=AppSettings)
    server: ServerSettings = field(default_factory=ServerSettings)
    ai: AISettings = field(default_factory=AISettings)
    creo: CreoSettings = field(default_factory=CreoSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    features: FeaturesSettings = field(default_factory=FeaturesSettings)
    development: DevelopmentSettings = field(default_factory=DevelopmentSettings)
    ui: UISettings = field(default_factory=UISettings)
    
    # 配置文件路径（向后兼容）
    config_file: str = "config/settings.yaml"
    
    # 目录设置（向后兼容）
    data_directory: str = "data"
    temp_directory: str = "temp"
    plugins_directory: str = "plugins"
    
    @property
    def app_name(self) -> str:
        """应用名称（向后兼容）"""
        return self.app.name
        
    @property
    def app_version(self) -> str:
        """应用版本（向后兼容）"""
        return self.app.version
        
    @property
    def debug_mode(self) -> bool:
        """调试模式（向后兼容）"""
        return self.app.debug

    def __post_init__(self):
        """初始化后处理"""
        # 确保目录存在
        self._ensure_directories()

        # 设置环境变量
        self._setup_environment()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_directory,
            self.temp_directory,
            self.plugins_directory,
            Path(self.logging.log_file).parent,
            self.ai.knowledge_base_path,
            self.creo.working_directory,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _setup_environment(self):
        """设置环境变量"""
        # 设置Creo环境变量
        if self.creo.install_path:
            creo_bin_path = Path(self.creo.install_path)
            if creo_bin_path.exists():
                current_path = os.environ.get("PATH", "")
                if str(creo_bin_path) not in current_path:
                    os.environ["PATH"] = f"{creo_bin_path};{current_path}"

        # 设置工作目录
        os.environ["PINGAO_WORK_DIR"] = self.creo.working_directory
        os.environ["PINGAO_DATA_DIR"] = self.data_directory
        os.environ["PINGAO_TEMP_DIR"] = self.temp_directory

    def get_creo_executable_path(self) -> str:
        """获取Creo可执行文件完整路径"""
        return str(Path(self.creo.install_path) / self.creo.executable)

    def get_log_file_path(self) -> str:
        """获取日志文件完整路径"""
        return str(Path(self.logging.log_file).resolve())

    def get_knowledge_base_path(self) -> str:
        """获取知识库路径"""
        return str(Path(self.ai.knowledge_base_path).resolve())

    def is_creo_available(self) -> bool:
        """检查Creo是否可用"""
        creo_exe = Path(self.get_creo_executable_path())
        return creo_exe.exists() and creo_exe.is_file()

    def validate(self) -> List[str]:
        """验证配置

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        # 验证应用设置
        if not self.app.name:
            errors.append("应用名称不能为空")
        if not self.app.version:
            errors.append("应用版本不能为空")

        # 验证服务器设置
        if self.server.port <= 0 or self.server.port > 65535:
            errors.append("服务器端口必须在1-65535范围内")
        if self.server.workers <= 0:
            errors.append("服务器工作进程数必须大于0")

        # 验证Creo设置
        if not self.is_creo_available():
            errors.append(f"Creo可执行文件不存在: {self.get_creo_executable_path()}")
        if self.creo.connection_timeout <= 0:
            errors.append("Creo连接超时时间必须大于0")
        if self.creo.operation_timeout <= 0:
            errors.append("Creo操作超时时间必须大于0")

        # 验证AI设置
        if (
            not self.ai.openai.api_key
            and not self.ai.anthropic.api_key
        ):
            errors.append("必须配置至少一个AI服务的API密钥")
        if self.ai.openai.max_tokens <= 0:
            errors.append("OpenAI最大令牌数必须大于0")
        if self.ai.anthropic.max_tokens <= 0:
            errors.append("Anthropic最大令牌数必须大于0")

        # 验证数据库设置
        if self.database.type not in ["sqlite", "postgresql"]:
            errors.append("数据库类型必须是sqlite或postgresql")
        if self.database.type == "postgresql":
            if not self.database.postgresql.host:
                errors.append("PostgreSQL主机地址不能为空")
            if not self.database.postgresql.name:
                errors.append("PostgreSQL数据库名不能为空")
            if not self.database.postgresql.user:
                errors.append("PostgreSQL用户名不能为空")

        # 验证存储设置
        if self.storage.max_file_size <= 0:
            errors.append("最大文件大小必须大于0")

        # 验证UI设置
        if self.ui.window_width <= 0 or self.ui.window_height <= 0:
            errors.append("窗口尺寸必须大于0")

        # 验证性能设置
        if self.performance.concurrency.max_workers <= 0:
            errors.append("最大工作线程数必须大于0")
        if self.performance.memory_limit <= 0:
            errors.append("内存限制必须大于0")
        if self.performance.cache.ttl <= 0:
            errors.append("缓存TTL必须大于0")

        # 验证安全设置
        if self.security.session_timeout <= 0:
            errors.append("会话超时时间必须大于0")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        from dataclasses import asdict

        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """从字典创建设置对象"""

        # 递归创建嵌套的dataclass对象
        def create_dataclass(cls_type, data_dict):
            if not isinstance(data_dict, dict):
                return data_dict

            field_types = {
                f.name: f.type for f in cls_type.__dataclass_fields__.values()
            }
            kwargs = {}

            for key, value in data_dict.items():
                if key in field_types:
                    field_type = field_types[key]
                    if hasattr(field_type, "__dataclass_fields__"):
                        kwargs[key] = create_dataclass(field_type, value)
                    else:
                        kwargs[key] = value

            return cls_type(**kwargs)

        return create_dataclass(cls, data)
