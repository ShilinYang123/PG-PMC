#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 统一配置管理中心

本模块提供统一的配置管理功能，整合项目中分散的配置文件和配置逻辑。

主要功能：
1. 统一配置文件管理
2. 环境变量处理
3. 配置验证和默认值
4. 配置热重载
5. 配置加密和安全
6. 路径管理规范化

作者: 雨俊
创建时间: 2025-01-10
"""

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from dotenv import load_dotenv

try:
    from core.unified_logging import get_logger
except ImportError:
    # 简单的logger替代
    class SimpleLogger:
        def error(self, msg):
            print(f"ERROR: {msg}")

        def info(self, msg):
            print(f"INFO: {msg}")

        def warning(self, msg):
            print(f"WARNING: {msg}")

        def debug(self, msg):
            print(f"DEBUG: {msg}")

    def get_logger(name):
        return SimpleLogger()


@dataclass
class ConfigPaths:
    """配置路径管理"""

    # 项目根目录
    project_root: Path = field(default_factory=lambda: Path.cwd())

    # 配置目录
    config_dir: Path = field(default_factory=lambda: Path("config"))

    # 主配置文件
    main_config: str = "settings.yaml"
    default_config: str = "default.yaml"
    user_config: str = "user_settings.yaml"

    # 环境变量文件
    env_files: List[str] = field(
        default_factory=lambda: [
            ".env.local",
            ".env",
            ".env.development",
            ".env.production",
            ".env.testing",
        ]
    )

    # 备份目录
    backup_dir: Path = field(default_factory=lambda: Path("config/backups"))

    # 日志目录
    log_dir: Path = field(default_factory=lambda: Path("logs"))

    # 数据目录
    data_dir: Path = field(default_factory=lambda: Path("data"))

    # 临时目录
    temp_dir: Path = field(default_factory=lambda: Path("temp"))

    # 上传目录
    upload_dir: Path = field(default_factory=lambda: Path("uploads"))

    def __post_init__(self):
        """初始化后处理"""
        # 确保所有路径都是绝对路径
        self.project_root = self.project_root.resolve()
        self.config_dir = self.project_root / self.config_dir
        self.backup_dir = self.project_root / self.backup_dir
        self.log_dir = self.project_root / self.log_dir
        self.data_dir = self.project_root / self.data_dir
        self.temp_dir = self.project_root / self.temp_dir
        self.upload_dir = self.project_root / self.upload_dir

    def get_config_file(self, config_type: str = "main") -> Path:
        """获取配置文件路径"""
        config_files = {
            "main": self.main_config,
            "default": self.default_config,
            "user": self.user_config,
        }

        if config_type not in config_files:
            raise ValueError(f"未知的配置类型: {config_type}")

        return self.config_dir / config_files[config_type]

    def ensure_directories(self) -> None:
        """确保所有必要目录存在"""
        directories = [
            self.config_dir,
            self.backup_dir,
            self.log_dir,
            self.data_dir,
            self.temp_dir,
            self.upload_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class ConfigValidationRule:
    """配置验证规则"""

    key_path: str
    required: bool = False
    data_type: type = str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None


class ConfigCenter:
    """统一配置管理中心

    提供统一的配置管理功能，整合项目中分散的配置文件和配置逻辑。
    """

    def __init__(self, project_root: Optional[Path] = None):
        """初始化配置中心

        Args:
            project_root: 项目根目录路径
        """
        self.logger = get_logger(self.__class__.__name__)

        # 初始化路径管理
        if project_root:
            self.paths = ConfigPaths(project_root=project_root)
        else:
            self.paths = ConfigPaths()

        # 确保目录存在
        self.paths.ensure_directories()

        # 配置缓存
        self._config_cache: Dict[str, Any] = {}
        self._config_loaded = False

        # 验证规则
        self._validation_rules: List[ConfigValidationRule] = []
        self._setup_default_validation_rules()

        # 环境变量缓存
        self._env_cache: Dict[str, str] = {}

        self.logger.info(f"配置中心已初始化，项目根目录: {self.paths.project_root}")

    def _setup_default_validation_rules(self) -> None:
        """设置默认验证规则"""
        default_rules = [
            ConfigValidationRule(
                key_path="app.name",
                required=True,
                data_type=str,
                error_message="应用名称不能为空",
            ),
            ConfigValidationRule(
                key_path="app.version",
                required=True,
                data_type=str,
                pattern=r"^\d+\.\d+\.\d+$",
                error_message="版本号格式应为 x.y.z",
            ),
            ConfigValidationRule(
                key_path="server.port",
                required=True,
                data_type=int,
                min_value=1,
                max_value=65535,
                error_message="服务器端口必须在 1-65535 范围内",
            ),
            ConfigValidationRule(
                key_path="logging.level",
                required=True,
                data_type=str,
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                error_message="日志级别必须是有效值",
            ),
            ConfigValidationRule(
                key_path="storage.max_file_size",
                required=True,
                data_type=int,
                min_value=1,
                error_message="最大文件大小必须大于0",
            ),
        ]

        self._validation_rules.extend(default_rules)

    def load_environment_variables(self) -> None:
        """加载环境变量

        按优先级顺序加载环境变量文件：
        1. .env.local (最高优先级)
        2. .env
        3. .env.{ENVIRONMENT}
        """
        try:
            self.logger.info("开始加载环境变量")

            # 获取当前环境
            current_env = os.getenv("ENVIRONMENT", "development")

            # 按优先级逆序加载，后加载的会覆盖先加载的
            env_files_to_load = [f".env.{current_env}", ".env", ".env.local"]

            loaded_files = []
            for env_file in env_files_to_load:
                env_path = self.paths.project_root / env_file
                if env_path.exists():
                    self.logger.info(f"加载环境变量文件: {env_file}")
                    load_dotenv(env_path, override=True)
                    loaded_files.append(env_file)

            # 缓存环境变量
            self._env_cache = dict(os.environ)

            if loaded_files:
                self.logger.info(f"✅ 已加载环境变量文件: {', '.join(loaded_files)}")
            else:
                self.logger.warning("⚠️ 未找到任何环境变量文件")

        except Exception as e:
            self.logger.error(f"❌ 加载环境变量失败: {e}")

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载配置

        配置加载优先级：
        1. 用户配置文件 (user_settings.yaml)
        2. 主配置文件 (settings.yaml)
        3. 默认配置文件 (default.yaml)
        4. 内置默认配置

        环境变量会覆盖配置文件中的对应设置

        Args:
            force_reload: 是否强制重新加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        if self._config_loaded and not force_reload:
            return self._config_cache

        try:
            self.logger.info("开始加载配置")

            # 重新加载环境变量
            self.load_environment_variables()

            # 按优先级加载配置文件
            config_data = {}

            # 1. 加载默认配置
            default_config_path = self.paths.get_config_file("default")
            if default_config_path.exists():
                self.logger.info(f"加载默认配置: {default_config_path}")
                default_data = self._load_yaml_file(default_config_path)
                if default_data:
                    config_data.update(default_data)

            # 2. 加载主配置文件
            main_config_path = self.paths.get_config_file("main")
            if main_config_path.exists():
                self.logger.info(f"加载主配置: {main_config_path}")
                main_data = self._load_yaml_file(main_config_path)
                if main_data:
                    config_data = self._deep_merge_dict(config_data, main_data)

            # 3. 加载用户配置
            user_config_path = self.paths.get_config_file("user")
            if user_config_path.exists():
                self.logger.info(f"加载用户配置: {user_config_path}")
                user_data = self._load_yaml_file(user_config_path)
                if user_data:
                    config_data = self._deep_merge_dict(config_data, user_data)

            # 4. 如果没有任何配置文件，创建默认配置
            if not config_data:
                self.logger.info("创建默认配置")
                config_data = self._get_default_config()
                self._save_default_config(config_data)

            # 5. 应用环境变量覆盖
            config_data = self._apply_environment_overrides(config_data)

            # 6. 验证配置
            validation_errors = self._validate_config(config_data)
            if validation_errors:
                self.logger.warning(f"配置验证发现问题: {len(validation_errors)} 个")
                for error in validation_errors:
                    self.logger.warning(f"  - {error}")

            # 7. 规范化路径
            config_data = self._normalize_paths(config_data)

            # 缓存配置
            self._config_cache = config_data
            self._config_loaded = True

            self.logger.info("✅ 配置加载完成")
            return config_data

        except Exception as e:
            self.logger.error(f"❌ 加载配置失败: {e}")
            # 返回默认配置
            default_config = self._get_default_config()
            self._config_cache = default_config
            return default_config

    def get_config(self, key_path: str = None, default: Any = None) -> Any:
        """获取配置值

        Args:
            key_path: 配置键路径，如 'app.name' 或 'server.port'
            default: 默认值

        Returns:
            Any: 配置值
        """
        config = self.load_config()

        if key_path is None:
            return config

        # 解析键路径
        keys = key_path.split(".")
        value = config

        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def set_config(self, key_path: str, value: Any, save_to_user: bool = True) -> bool:
        """设置配置值

        Args:
            key_path: 配置键路径
            value: 配置值
            save_to_user: 是否保存到用户配置文件

        Returns:
            bool: 设置是否成功
        """
        try:
            # 更新缓存
            config = self.load_config()
            keys = key_path.split(".")

            # 导航到目标位置
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # 设置值
            current[keys[-1]] = value

            # 验证新配置
            validation_errors = self._validate_config(config)
            if validation_errors:
                self.logger.warning(f"配置验证警告: {validation_errors}")

            # 保存到文件
            if save_to_user:
                success = self._save_config_to_file(config, "user")
                if success:
                    self.logger.info(f"✅ 配置已更新: {key_path} = {value}")
                return success

            return True

        except Exception as e:
            self.logger.error(f"❌ 设置配置失败: {e}")
            return False

    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置

        Returns:
            Dict[str, Any]: 重新加载的配置
        """
        self.logger.info("重新加载配置")
        self._config_loaded = False
        self._config_cache.clear()
        return self.load_config(force_reload=True)

    def backup_config(self, backup_name: Optional[str] = None) -> bool:
        """备份当前配置

        Args:
            backup_name: 备份名称，如果为None则使用时间戳

        Returns:
            bool: 备份是否成功
        """
        try:
            from datetime import datetime

            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"config_backup_{timestamp}"

            backup_path = self.paths.backup_dir / f"{backup_name}.yaml"

            # 获取当前配置
            config = self.load_config()

            # 保存备份
            success = self._save_yaml_file(config, backup_path)

            if success:
                self.logger.info(f"✅ 配置已备份: {backup_path}")

            return success

        except Exception as e:
            self.logger.error(f"❌ 备份配置失败: {e}")
            return False

    def restore_config(self, backup_name: str) -> bool:
        """恢复配置

        Args:
            backup_name: 备份名称

        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_path = self.paths.backup_dir / f"{backup_name}.yaml"

            if not backup_path.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False

            # 加载备份配置
            backup_config = self._load_yaml_file(backup_path)
            if not backup_config:
                self.logger.error(f"无法加载备份配置: {backup_path}")
                return False

            # 保存到用户配置
            success = self._save_config_to_file(backup_config, "user")

            if success:
                # 重新加载配置
                self.reload_config()
                self.logger.info(f"✅ 配置已恢复: {backup_name}")

            return success

        except Exception as e:
            self.logger.error(f"❌ 恢复配置失败: {e}")
            return False

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息

        Returns:
            Dict[str, Any]: 配置信息
        """
        return {
            "project_root": str(self.paths.project_root),
            "config_dir": str(self.paths.config_dir),
            "config_files": {
                "main": str(self.paths.get_config_file("main")),
                "default": str(self.paths.get_config_file("default")),
                "user": str(self.paths.get_config_file("user")),
            },
            "config_exists": {
                "main": self.paths.get_config_file("main").exists(),
                "default": self.paths.get_config_file("default").exists(),
                "user": self.paths.get_config_file("user").exists(),
            },
            "environment": os.getenv("ENVIRONMENT", "development"),
            "config_loaded": self._config_loaded,
            "validation_rules_count": len(self._validation_rules),
        }

    def add_validation_rule(self, rule: ConfigValidationRule) -> None:
        """添加验证规则

        Args:
            rule: 验证规则
        """
        self._validation_rules.append(rule)
        self.logger.info(f"已添加验证规则: {rule.key_path}")

    def _load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """加载YAML文件

        Args:
            file_path: YAML文件路径

        Returns:
            Optional[Dict[str, Any]]: 配置数据
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            self.logger.error(f"加载YAML文件失败 {file_path}: {e}")
            return None

    def _save_yaml_file(self, data: Dict[str, Any], file_path: Path) -> bool:
        """保存YAML文件

        Args:
            data: 配置数据
            file_path: 文件路径

        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    indent=2,
                )
            return True
        except Exception as e:
            self.logger.error(f"保存YAML文件失败 {file_path}: {e}")
            return False

    def _save_config_to_file(self, config: Dict[str, Any], config_type: str) -> bool:
        """保存配置到文件

        Args:
            config: 配置数据
            config_type: 配置类型 (main, default, user)

        Returns:
            bool: 保存是否成功
        """
        try:
            config_path = self.paths.get_config_file(config_type)
            return self._save_yaml_file(config, config_path)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def _deep_merge_dict(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并字典

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            Dict[str, Any]: 合并后的字典
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    def _apply_environment_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """应用环境变量覆盖

        Args:
            config: 配置字典

        Returns:
            Dict[str, Any]: 应用环境变量后的配置
        """
        # 定义环境变量到配置路径的映射
        env_mappings = {
            "DEBUG": "app.debug",
            "LOG_LEVEL": "app.log_level",
            "SERVER_HOST": "server.host",
            "SERVER_PORT": "server.port",
            "DATABASE_URL": "database.url",
            "OPENAI_API_KEY": "ai.openai.api_key",
            "ANTHROPIC_API_KEY": "ai.anthropic.api_key",
            "CREO_INSTALL_PATH": "creo.install_path",
            "TEMP_DIR": "storage.temp_dir",
            "UPLOAD_DIR": "storage.upload_dir",
            "MAX_FILE_SIZE": "storage.max_file_size",
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 类型转换
                if env_var in ["SERVER_PORT", "MAX_FILE_SIZE"]:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                elif env_var == "DEBUG":
                    env_value = env_value.lower() in ("true", "1", "yes", "on")

                # 设置配置值
                keys = config_path.split(".")
                current = config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = env_value

                self.logger.debug(f"环境变量覆盖: {config_path} = {env_value}")

        return config

    def _validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置

        Args:
            config: 配置字典

        Returns:
            List[str]: 验证错误列表
        """
        errors = []

        for rule in self._validation_rules:
            try:
                # 获取配置值
                keys = rule.key_path.split(".")
                value = config

                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                # 检查必需项
                if rule.required and value is None:
                    errors.append(
                        rule.error_message or f"必需配置项缺失: {rule.key_path}"
                    )
                    continue

                if value is None:
                    continue

                # 检查数据类型
                if not isinstance(value, rule.data_type):
                    errors.append(
                        rule.error_message or f"配置项类型错误: {rule.key_path}"
                    )
                    continue

                # 检查数值范围
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(
                        rule.error_message or f"配置项值过小: {rule.key_path}"
                    )

                if rule.max_value is not None and value > rule.max_value:
                    errors.append(
                        rule.error_message or f"配置项值过大: {rule.key_path}"
                    )

                # 检查允许值
                if rule.allowed_values and value not in rule.allowed_values:
                    errors.append(
                        rule.error_message or f"配置项值不在允许范围内: {rule.key_path}"
                    )

                # 检查正则模式
                if rule.pattern and isinstance(value, str):
                    import re

                    if not re.match(rule.pattern, value):
                        errors.append(
                            rule.error_message or f"配置项格式错误: {rule.key_path}"
                        )

                # 自定义验证
                if rule.custom_validator:
                    try:
                        if not rule.custom_validator(value):
                            errors.append(
                                rule.error_message or f"配置项验证失败: {rule.key_path}"
                            )
                    except Exception as e:
                        errors.append(f"配置项验证异常: {rule.key_path} - {e}")

            except Exception as e:
                errors.append(f"验证规则执行异常: {rule.key_path} - {e}")

        return errors

    def _normalize_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """规范化路径配置

        Args:
            config: 配置字典

        Returns:
            Dict[str, Any]: 规范化后的配置
        """
        # 需要规范化的路径配置
        path_configs = [
            "storage.temp_dir",
            "storage.upload_dir",
            "storage.backup_dir",
            "logging.file",
            "database.sqlite.path",
            "creo.working_directory",
            "ai.knowledge_base_path",
        ]

        for path_config in path_configs:
            keys = path_config.split(".")
            current = config

            # 导航到目标位置
            for key in keys[:-1]:
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    break
            else:
                # 规范化路径
                final_key = keys[-1]
                if final_key in current and current[final_key]:
                    path_value = current[final_key]
                    if isinstance(path_value, str):
                        # 转换为绝对路径
                        if not Path(path_value).is_absolute():
                            current[final_key] = str(
                                self.paths.project_root / path_value
                            )

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "app": {
                "name": "PG-Dev AI设计助理",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
                "environment": "development",
            },
            "server": {"host": "localhost", "port": 8000, "workers": 1},
            "ai": {
                "openai": {
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "timeout": 30,
                },
                "anthropic": {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "timeout": 30,
                },
            },
            "creo": {
                "install_path": "",
                "connection_timeout": 30,
                "operation_timeout": 120,
                "auto_start": False,
            },
            "database": {"sqlite": {"path": "data/app.db"}},
            "storage": {
                "temp_dir": "temp",
                "upload_dir": "uploads",
                "max_file_size": 100,
                "allowed_extensions": [
                    ".prt",
                    ".asm",
                    ".drw",
                    ".step",
                    ".iges",
                    ".stl",
                ],
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
                "rotation": "1 day",
                "retention": "30 days",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            },
            "security": {
                "session_timeout": 60,
                "max_login_attempts": 5,
                "lockout_duration": 15,
            },
            "performance": {
                "cache": {"enabled": True, "ttl": 3600, "max_size": 1000},
                "concurrency": {"max_workers": 4, "queue_size": 100},
            },
        }

    def _save_default_config(self, config: Dict[str, Any]) -> None:
        """保存默认配置

        Args:
            config: 配置数据
        """
        try:
            default_config_path = self.paths.get_config_file("default")
            success = self._save_yaml_file(config, default_config_path)

            if success:
                self.logger.info(f"✅ 默认配置已保存: {default_config_path}")

        except Exception as e:
            self.logger.error(f"❌ 保存默认配置失败: {e}")


# 全局配置中心实例
_config_center: Optional[ConfigCenter] = None


def get_config_center(project_root: Optional[Path] = None) -> ConfigCenter:
    """获取全局配置中心实例

    Args:
        project_root: 项目根目录路径

    Returns:
        ConfigCenter: 配置中心实例
    """
    global _config_center

    if _config_center is None:
        _config_center = ConfigCenter(project_root)

    return _config_center


def get_config(key_path: str = None, default: Any = None) -> Any:
    """获取配置值（便捷函数）

    Args:
        key_path: 配置键路径
        default: 默认值

    Returns:
        Any: 配置值
    """
    config_center = get_config_center()
    return config_center.get_config(key_path, default)


def set_config(key_path: str, value: Any, save_to_user: bool = True) -> bool:
    """设置配置值（便捷函数）

    Args:
        key_path: 配置键路径
        value: 配置值
        save_to_user: 是否保存到用户配置文件

    Returns:
        bool: 设置是否成功
    """
    config_center = get_config_center()
    return config_center.set_config(key_path, value, save_to_user)


def reload_config() -> Dict[str, Any]:
    """重新加载配置（便捷函数）

    Returns:
        Dict[str, Any]: 重新加载的配置
    """
    config_center = get_config_center()
    return config_center.reload_config()


if __name__ == "__main__":
    # 测试代码
    config_center = ConfigCenter()

    # 加载配置
    config = config_center.load_config()
    print("配置加载完成")

    # 获取配置信息
    info = config_center.get_config_info()
    print(f"配置信息: {info}")

    # 测试配置获取
    app_name = config_center.get_config("app.name")
    print(f"应用名称: {app_name}")

    # 测试配置设置
    success = config_center.set_config("app.debug", True)
    print(f"设置配置: {success}")
