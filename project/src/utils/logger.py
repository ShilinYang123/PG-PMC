#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 日志工具（统一日志系统包装器）

注意：此模块已重构为统一日志系统的包装器，保持向后兼容性。
新代码应直接使用 project.src.core.unified_logging 模块。
"""

import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

# 导入统一日志系统
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 这些导入必须在sys.path修改后进行
from project.src.core.unified_logging import (  # noqa: E402
    get_logger as unified_get_logger,
)
from project.src.core.unified_logging import initialize_logging  # noqa: E402

# 发出废弃警告
warnings.warn(
    "project.src.utils.logger 模块已废弃，请使用 project.src.core.unified_logging",
    DeprecationWarning,
    stacklevel=2,
)


class LoggerConfig:
    """日志配置（兼容性包装器）"""

    def __init__(self):
        # 为了向后兼容，保留配置属性但不实际使用
        self.level = "INFO"
        self.format = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
        self.rotation = "10 MB"
        self.retention = "30 days"
        self.compression = "zip"
        self.backtrace = True
        self.diagnose = True

        # 文件路径（统一日志系统会自动管理）
        self.log_dir = Path("logs")
        self.log_file = "application.log"
        self.error_file = "errors.log"

        # 控制台输出
        self.console_enabled = True
        self.console_level = "INFO"

        # 文件输出
        self.file_enabled = True
        self.file_level = "DEBUG"

        # 错误文件
        self.error_file_enabled = True
        self.error_file_level = "ERROR"

        # 发出废弃警告
        warnings.warn(
            "LoggerConfig 类已废弃，统一日志系统会自动管理配置",
            DeprecationWarning,
            stacklevel=2,
        )

        # 性能日志
        self.performance_enabled = True
        self.performance_file = "pingao_ai_performance.log"

        # 审计日志
        self.audit_enabled = True
        self.audit_file = "pingao_ai_audit.log"


class CustomLogger:
    """自定义日志器"""

    def __init__(self, name: str, config: LoggerConfig = None):
        self.name = name
        self.config = config or LoggerConfig()
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器（兼容性方法，实际由统一日志系统管理）"""
        # 此方法保留用于向后兼容，实际日志配置由统一日志系统管理
        # 初始化统一日志系统
        initialize_logging()
        # 获取统一日志系统的logger
        self._logger = unified_get_logger(self.name, "standard")

    def get_logger(self):
        """获取日志器"""
        return self._logger

    def debug(self, message: str, **kwargs):
        """调试日志"""
        self._logger.debug(f"[{self.name}] {message}")

    def info(self, message: str, **kwargs):
        """信息日志"""
        self._logger.info(f"[{self.name}] {message}")

    def warning(self, message: str, **kwargs):
        """警告日志"""
        self._logger.warning(f"[{self.name}] {message}")

    def error(self, message: str, **kwargs):
        """错误日志"""
        self._logger.error(f"[{self.name}] {message}")

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        self._logger.critical(f"[{self.name}] {message}")

    def exception(self, message: str, **kwargs):
        """异常日志"""
        self._logger.exception(f"[{self.name}] {message}")

    def performance(self, message: str, **kwargs):
        """性能日志"""
        self._logger.info(f"[PERF][{self.name}] {message}")

    def audit(self, message: str, **kwargs):
        """审计日志"""
        self._logger.info(f"[AUDIT][{self.name}] {message}")


# 全局日志器实例
_loggers: Dict[str, CustomLogger] = {}
_global_config: Optional[LoggerConfig] = None


def setup_logging(
    config: LoggerConfig = None,
    level: str = None,
    log_dir: str = None,
    console_enabled: bool = None,
    file_enabled: bool = None,
) -> LoggerConfig:
    """设置全局日志配置（兼容性包装器）

    Args:
        config: 日志配置对象（已废弃，仅保留兼容性）
        level: 日志级别（已废弃，仅保留兼容性）
        log_dir: 日志目录（已废弃，仅保留兼容性）
        console_enabled: 是否启用控制台输出（已废弃，仅保留兼容性）
        file_enabled: 是否启用文件输出（已废弃，仅保留兼容性）

    Returns:
        LoggerConfig: 日志配置（兼容性返回）
    """
    global _global_config

    warnings.warn(
        "project.src.utils.logger.setup_logging 已废弃，"
        "请使用 project.src.core.unified_logging.initialize_logging",
        DeprecationWarning,
        stacklevel=2,
    )

    # 初始化统一日志系统
    initialize_logging()

    # 为了兼容性，返回一个配置对象
    if config is None:
        config = LoggerConfig()

    _global_config = config
    return config


def get_logger(name: str):
    """获取日志器（兼容性包装器）

    Args:
        name: 日志器名称

    Returns:
        Logger: 日志器实例
    """
    warnings.warn(
        "project.src.utils.logger.get_logger 已废弃，"
        "请使用 project.src.core.unified_logging.get_logger",
        DeprecationWarning,
        stacklevel=2,
    )

    # 初始化统一日志系统
    initialize_logging()

    # 返回统一日志系统的logger
    return unified_get_logger(name, "standard")


def get_log_files() -> Dict[str, str]:
    """获取日志文件路径（兼容性包装器）

    Returns:
        Dict[str, str]: 日志文件路径字典
    """
    warnings.warn(
        "project.src.utils.logger.get_log_files 已废弃，日志文件由统一日志系统管理",
        DeprecationWarning,
        stacklevel=2,
    )

    # 返回统一日志系统的标准日志文件路径
    return {
        "main": "logs/application.log",
        "error": "logs/errors.log",
        "performance": "logs/performance.log",
        "audit": "logs/audit.log",
    }


def cleanup_old_logs(days: int = 30):
    """清理旧日志文件（兼容性包装器）

    Args:
        days: 保留天数（已废弃，统一日志系统自动管理）
    """
    warnings.warn(
        "project.src.utils.logger.cleanup_old_logs 已废弃，统一日志系统自动管理日志清理",
        DeprecationWarning,
        stacklevel=2,
    )

    # 统一日志系统会自动处理日志清理，此函数仅保留兼容性
    print(f"日志清理功能已由统一日志系统自动管理，保留天数: {days}天")


def set_log_level(level: str):
    """设置日志级别（兼容性包装器）

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)（已废弃）
    """
    warnings.warn(
        "project.src.utils.logger.set_log_level 已废弃，日志级别由统一日志系统管理",
        DeprecationWarning,
        stacklevel=2,
    )

    print(f"日志级别设置功能已由统一日志系统管理，请求级别: {level.upper()}")


def enable_debug_mode():
    """启用调试模式（兼容性包装器）"""
    warnings.warn(
        "project.src.utils.logger.enable_debug_mode 已废弃，调试模式由统一日志系统管理",
        DeprecationWarning,
        stacklevel=2,
    )

    print("调试模式功能已由统一日志系统管理")


def disable_console_logging():
    """禁用控制台日志输出（兼容性包装器）"""
    warnings.warn(
        "project.src.utils.logger.disable_console_logging 已废弃，控制台输出由统一日志系统管理",
        DeprecationWarning,
        stacklevel=2,
    )

    print("控制台日志输出功能已由统一日志系统管理")


def get_logger_stats() -> Dict[str, Any]:
    """获取日志器统计信息（兼容性包装器）

    Returns:
        Dict[str, Any]: 统计信息
    """
    warnings.warn(
        "project.src.utils.logger.get_logger_stats 已废弃，统计信息由统一日志系统管理",
        DeprecationWarning,
        stacklevel=2,
    )

    # 返回基本的兼容性统计信息
    return {
        "loggers_count": 0,
        "logger_names": [],
        "config": {
            "level": "INFO",
            "log_dir": "logs",
            "console_enabled": True,
            "file_enabled": True,
            "unified_logging": True,
        },
    }


# 兼容性函数
def getLogger(name: str):
    """获取日志器（兼容标准库，兼容性包装器）

    Args:
        name: 日志器名称

    Returns:
        Logger: 日志器实例
    """
    warnings.warn(
        "project.src.utils.logger.getLogger 已废弃，"
        "请使用 project.src.core.unified_logging.get_logger",
        DeprecationWarning,
        stacklevel=2,
    )

    return get_logger(name)


def get_performance_logger(name: str = "performance"):
    """获取性能日志器（兼容性包装器）"""
    warnings.warn(
        "project.src.utils.logger.get_performance_logger 已废弃，"
        "请使用 project.src.core.unified_logging.get_logger",
        DeprecationWarning,
        stacklevel=2,
    )

    # 初始化统一日志系统
    initialize_logging()

    # 返回性能日志器
    return unified_get_logger(name, "performance")


def get_audit_logger(name: str = "audit"):
    """获取审计日志器（兼容性包装器）"""
    warnings.warn(
        "project.src.utils.logger.get_audit_logger 已废弃，"
        "请使用 project.src.core.unified_logging.get_logger",
        DeprecationWarning,
        stacklevel=2,
    )

    # 初始化统一日志系统
    initialize_logging()

    # 返回审计日志器
    return unified_get_logger(name, "audit")


# 创建默认日志器实例
logger = get_logger("pingao_ai")
