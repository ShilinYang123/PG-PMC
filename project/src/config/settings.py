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
class CreoSettings:
    """Creo相关设置"""

    # Creo安装路径
    install_path: str = r"C:\Program Files\PTC\Creo 7.0\Common Files\x86e_win64\bin"

    # Creo可执行文件名
    executable: str = "parametric.exe"

    # 启动参数
    startup_args: List[str] = field(
        default_factory=lambda: ["-g:no_graphics", "-i:rpc_input"]
    )

    # 连接超时时间（秒）
    connection_timeout: int = 30

    # 重试次数
    max_retries: int = 3

    # 工作目录
    working_directory: str = r"C:\PG-Dev\CreoWork"

    # 配置文件路径
    config_file: str = "config.pro"

    # 启动模式
    startup_mode: str = "windowed"  # windowed, minimized, hidden

    # API版本
    api_version: str = "7.0"

    # 是否自动保存
    auto_save: bool = True

    # 自动保存间隔（分钟）
    auto_save_interval: int = 5

    # 单位系统
    unit_system: str = "mmNs"  # mmNs, mmKs, inlbm, inlbf

    # 默认材料
    default_material: str = "PTC_SYSTEM_MTRL_STEEL"


@dataclass
class AISettings:
    """AI相关设置"""

    # OpenAI设置
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"

    # Claude设置
    claude_api_key: str = ""
    claude_model: str = "claude-3-sonnet-20240229"

    # 本地模型设置
    local_model_path: str = ""
    use_local_model: bool = False

    # 语言处理设置
    language: str = "zh-CN"  # zh-CN, en-US
    max_tokens: int = 2048
    temperature: float = 0.7

    # 设计知识库
    knowledge_base_path: str = "data/knowledge_base"

    # 缓存设置
    enable_cache: bool = True
    cache_size: int = 1000
    cache_ttl: int = 3600  # 秒

    # 响应超时
    response_timeout: int = 30

    # 重试设置
    max_retries: int = 3
    retry_delay: float = 1.0


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
class PerformanceSettings:
    """性能设置"""

    # 最大并发任务数
    max_concurrent_tasks: int = 4

    # 内存限制（MB）
    memory_limit: int = 2048

    # 缓存大小（MB）
    cache_size: int = 512

    # 几何体简化阈值
    geometry_simplification_threshold: float = 0.01

    # 渲染质量
    render_quality: str = "medium"  # low, medium, high, ultra

    # 是否启用多线程
    enable_multithreading: bool = True

    # 线程池大小
    thread_pool_size: int = 4

    # 预加载设置
    preload_models: bool = False
    preload_textures: bool = False


@dataclass
class Settings:
    """主配置类"""

    # 应用信息
    app_name: str = "PG-Dev AI设计助理"
    app_version: str = "1.0.0"

    # 配置文件路径
    config_file: str = "config/settings.yaml"

    # 各模块设置
    creo: CreoSettings = field(default_factory=CreoSettings)
    ai: AISettings = field(default_factory=AISettings)
    ui: UISettings = field(default_factory=UISettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)

    # 开发模式
    debug_mode: bool = False

    # 数据目录
    data_directory: str = "data"

    # 临时目录
    temp_directory: str = "temp"

    # 插件目录
    plugins_directory: str = "plugins"

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

        # 验证Creo设置
        if not self.is_creo_available():
            errors.append(f"Creo可执行文件不存在: {self.get_creo_executable_path()}")

        if self.creo.connection_timeout <= 0:
            errors.append("Creo连接超时时间必须大于0")

        # 验证AI设置
        if (
            not self.ai.openai_api_key
            and not self.ai.claude_api_key
            and not self.ai.use_local_model
        ):
            errors.append("必须配置至少一个AI服务")

        if self.ai.max_tokens <= 0:
            errors.append("AI最大令牌数必须大于0")

        # 验证UI设置
        if self.ui.window_width <= 0 or self.ui.window_height <= 0:
            errors.append("窗口尺寸必须大于0")

        # 验证性能设置
        if self.performance.max_concurrent_tasks <= 0:
            errors.append("最大并发任务数必须大于0")

        if self.performance.memory_limit <= 0:
            errors.append("内存限制必须大于0")

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
