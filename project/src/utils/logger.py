#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 日志工具
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class LoggerConfig:
    """日志配置"""

    def __init__(self):
        # 默认配置
        self.level = "INFO"
        self.format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        self.rotation = "10 MB"
        self.retention = "30 days"
        self.compression = "zip"
        self.backtrace = True
        self.diagnose = True

        # 文件路径
        self.log_dir = Path("logs")
        self.log_file = "pingao_ai.log"
        self.error_file = "pingao_ai_error.log"

        # 控制台输出
        self.console_enabled = True
        self.console_level = "INFO"

        # 文件输出
        self.file_enabled = True
        self.file_level = "DEBUG"

        # 错误文件
        self.error_file_enabled = True
        self.error_file_level = "ERROR"

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
        """设置日志器"""
        try:
            # 创建日志目录
            self.config.log_dir.mkdir(parents=True, exist_ok=True)

            # 移除默认处理器
            logger.remove()

            # 添加控制台处理器
            if self.config.console_enabled:
                logger.add(
                    sys.stderr,
                    format=self.config.format,
                    level=self.config.console_level,
                    colorize=True,
                    backtrace=self.config.backtrace,
                    diagnose=self.config.diagnose,
                )

            # 添加文件处理器
            if self.config.file_enabled:
                log_file_path = self.config.log_dir / self.config.log_file
                logger.add(
                    log_file_path,
                    format=self.config.format,
                    level=self.config.file_level,
                    rotation=self.config.rotation,
                    retention=self.config.retention,
                    compression=self.config.compression,
                    backtrace=self.config.backtrace,
                    diagnose=self.config.diagnose,
                    encoding="utf-8",
                )

            # 添加错误文件处理器
            if self.config.error_file_enabled:
                error_file_path = self.config.log_dir / self.config.error_file
                logger.add(
                    error_file_path,
                    format=self.config.format,
                    level=self.config.error_file_level,
                    rotation=self.config.rotation,
                    retention=self.config.retention,
                    compression=self.config.compression,
                    backtrace=self.config.backtrace,
                    diagnose=self.config.diagnose,
                    encoding="utf-8",
                )

            # 添加性能日志处理器
            if self.config.performance_enabled:
                perf_file_path = self.config.log_dir / self.config.performance_file
                logger.add(
                    perf_file_path,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                    level="INFO",
                    filter=lambda record: "PERFORMANCE" in record["extra"],
                    rotation="1 day",
                    retention="7 days",
                    encoding="utf-8",
                )

            # 添加审计日志处理器
            if self.config.audit_enabled:
                audit_file_path = self.config.log_dir / self.config.audit_file
                logger.add(
                    audit_file_path,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                    level="INFO",
                    filter=lambda record: "AUDIT" in record["extra"],
                    rotation="1 day",
                    retention="30 days",
                    encoding="utf-8",
                )

        except Exception as e:
            print(f"设置日志器失败: {e}")
            # 使用基本配置
            logger.add(sys.stderr, level="INFO")

    def get_logger(self):
        """获取日志器"""
        return logger.bind(name=self.name)

    def debug(self, message: str, **kwargs):
        """调试日志"""
        logger.bind(name=self.name).debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """信息日志"""
        logger.bind(name=self.name).info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """警告日志"""
        logger.bind(name=self.name).warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """错误日志"""
        logger.bind(name=self.name).error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        logger.bind(name=self.name).critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """异常日志"""
        logger.bind(name=self.name).exception(message, **kwargs)

    def performance(self, message: str, **kwargs):
        """性能日志"""
        logger.bind(name=self.name, PERFORMANCE=True).info(message, **kwargs)

    def audit(self, message: str, **kwargs):
        """审计日志"""
        logger.bind(name=self.name, AUDIT=True).info(message, **kwargs)


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
    """设置全局日志配置

    Args:
        config: 日志配置对象
        level: 日志级别
        log_dir: 日志目录
        console_enabled: 是否启用控制台输出
        file_enabled: 是否启用文件输出

    Returns:
        LoggerConfig: 日志配置
    """
    global _global_config

    try:
        # 使用提供的配置或创建新配置
        if config is None:
            config = LoggerConfig()

        # 应用参数覆盖
        if level is not None:
            config.level = level
            config.console_level = level
            config.file_level = level

        if log_dir is not None:
            config.log_dir = Path(log_dir)

        if console_enabled is not None:
            config.console_enabled = console_enabled

        if file_enabled is not None:
            config.file_enabled = file_enabled

        _global_config = config

        # 清空现有日志器，强制重新初始化
        _loggers.clear()

        # 创建根日志器以验证配置
        get_logger("root")

        return config

    except Exception as e:
        print(f"设置日志配置失败: {e}")
        # 返回默认配置
        _global_config = LoggerConfig()
        return _global_config


def get_logger(name: str) -> CustomLogger:
    """获取日志器

    Args:
        name: 日志器名称

    Returns:
        CustomLogger: 日志器实例
    """
    global _loggers, _global_config

    try:
        # 如果日志器已存在，直接返回
        if name in _loggers:
            return _loggers[name]

        # 使用全局配置或默认配置
        config = _global_config or LoggerConfig()

        # 创建新的日志器
        custom_logger = CustomLogger(name, config)
        _loggers[name] = custom_logger

        return custom_logger

    except Exception as e:
        print(f"获取日志器失败: {e}")
        # 返回基本日志器
        if name not in _loggers:
            _loggers[name] = CustomLogger(name, LoggerConfig())
        return _loggers[name]


def get_log_files() -> Dict[str, str]:
    """获取日志文件路径

    Returns:
        Dict[str, str]: 日志文件路径字典
    """
    try:
        config = _global_config or LoggerConfig()

        log_files = {}

        if config.file_enabled:
            log_files["main"] = str(config.log_dir / config.log_file)

        if config.error_file_enabled:
            log_files["error"] = str(config.log_dir / config.error_file)

        if config.performance_enabled:
            log_files["performance"] = str(config.log_dir / config.performance_file)

        if config.audit_enabled:
            log_files["audit"] = str(config.log_dir / config.audit_file)

        return log_files

    except Exception as e:
        print(f"获取日志文件路径失败: {e}")
        return {}


def cleanup_old_logs(days: int = 30):
    """清理旧日志文件

    Args:
        days: 保留天数
    """
    try:
        config = _global_config or LoggerConfig()
        log_dir = config.log_dir

        if not log_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        deleted_count = 0
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"删除日志文件失败 {log_file}: {e}")

        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 个旧日志文件")

    except Exception as e:
        print(f"清理旧日志失败: {e}")


def set_log_level(level: str):
    """设置日志级别

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        global _global_config

        if _global_config is None:
            _global_config = LoggerConfig()

        _global_config.level = level.upper()
        _global_config.console_level = level.upper()
        _global_config.file_level = level.upper()

        # 重新设置所有日志器
        _loggers.clear()

        logger.info(f"日志级别已设置为: {level.upper()}")

    except Exception as e:
        print(f"设置日志级别失败: {e}")


def enable_debug_mode():
    """启用调试模式"""
    try:
        set_log_level("DEBUG")

        global _global_config
        if _global_config:
            _global_config.backtrace = True
            _global_config.diagnose = True

        logger.info("调试模式已启用")

    except Exception as e:
        print(f"启用调试模式失败: {e}")


def disable_console_logging():
    """禁用控制台日志输出"""
    try:
        global _global_config

        if _global_config is None:
            _global_config = LoggerConfig()

        _global_config.console_enabled = False

        # 重新设置所有日志器
        _loggers.clear()

        print("控制台日志输出已禁用")

    except Exception as e:
        print(f"禁用控制台日志失败: {e}")


def get_logger_stats() -> Dict[str, Any]:
    """获取日志器统计信息

    Returns:
        Dict[str, Any]: 统计信息
    """
    try:
        config = _global_config or LoggerConfig()

        stats = {
            "loggers_count": len(_loggers),
            "logger_names": list(_loggers.keys()),
            "config": {
                "level": config.level,
                "log_dir": str(config.log_dir),
                "console_enabled": config.console_enabled,
                "file_enabled": config.file_enabled,
                "error_file_enabled": config.error_file_enabled,
                "performance_enabled": config.performance_enabled,
                "audit_enabled": config.audit_enabled,
            },
            "log_files": get_log_files(),
        }

        # 获取日志文件大小
        for name, path in stats["log_files"].items():
            try:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    stats["config"][
                        f"{name}_file_size"
                    ] = f"{size / 1024 / 1024:.2f} MB"
                else:
                    stats["config"][f"{name}_file_size"] = "不存在"
            except Exception:
                stats["config"][f"{name}_file_size"] = "未知"

        return stats

    except Exception as e:
        print(f"获取日志器统计失败: {e}")
        return {}


# 兼容性函数
def getLogger(name: str) -> CustomLogger:
    """获取日志器（兼容标准库）

    Args:
        name: 日志器名称

    Returns:
        CustomLogger: 日志器实例
    """
    return get_logger(name)
