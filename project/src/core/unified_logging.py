#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志系统架构

基于规范与流程.md第十四章日志管理规范，统一项目中的所有日志系统。
解决多套日志系统冲突、重复输出和格式不一致问题。

设计原则：
1. 严格遵循既定的日志管理规范
2. 统一日志格式和输出策略
3. 集中化配置管理
4. 避免日志重复输出
5. 支持性能优化和调试模式

作者：技术负责人
创建时间：2025-01-27
"""

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import threading
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict


class UnifiedLoggingSystem:
    """
    统一日志系统

    基于规范与流程.md第十四章日志管理规范的统一日志架构，
    替代项目中的多套日志系统，确保架构一致性。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式确保全局唯一的日志系统"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化统一日志系统"""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._loggers = {}
        self._config_loaded = False
        self._project_root = self._get_project_root()
        self._logs_dir = self._project_root / "logs"

        # 确保日志目录结构符合规范
        self._ensure_log_directories()

        # 加载默认配置
        self._load_default_config()

    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        try:
            # 尝试从config_loader获取
            from tools.config_loader import ConfigLoader

            config_loader = ConfigLoader()
            return Path(config_loader.get_project_root())
        except Exception:
            # 备用方案：从当前文件位置推断
            current_file = Path(__file__)
            # 从 project/src/core/unified_logging.py 推断到项目根目录
            return current_file.parent.parent.parent.parent

    def _ensure_log_directories(self):
        """确保日志目录结构符合规范与流程.md第十四章要求"""
        required_dirs = [
            "工作记录",
            "检查报告",
            "其他日志",
            "archive",
            "temp",
            "error_detection",
        ]

        for dir_name in required_dirs:
            dir_path = self._logs_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_default_config(self):
        """加载默认日志配置，严格遵循规范要求"""
        self._default_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": (
                        "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d "
                        "[%(funcName)s] - %(message)s [PID:%(process)d TID:%(thread)d]"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "simple": {"format": "%(levelname)s - %(message)s"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
                "application_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(self._logs_dir / "其他日志" / "application.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(self._logs_dir / "其他日志" / "errors.log"),
                    "maxBytes": 10485760,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "finish_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(
                        self._logs_dir
                        / "工作记录"
                        / f"finish_py_{datetime.now().strftime('%Y%m%d')}.log"
                    ),
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
                "check_structure_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(
                        self._logs_dir
                        / "检查报告"
                        / f"structure_check_{datetime.now().strftime('%Y%m%d')}.log"
                    ),
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console", "application_file"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "finish": {
                    "handlers": ["console", "finish_file", "error_file"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "enhanced_checker": {
                    "handlers": ["console", "check_structure_file", "error_file"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "error": {
                    "handlers": ["error_file"],
                    "level": "ERROR",
                    "propagate": False,
                },
            },
        }

        # 应用配置
        logging.config.dictConfig(self._default_config)
        self._config_loaded = True

    def get_logger(self, name: str, logger_type: str = "standard") -> logging.Logger:
        """
        获取统一配置的日志器

        Args:
            name: 日志器名称
            logger_type: 日志器类型 (standard, finish, enhanced_checker)

        Returns:
            配置好的日志器实例
        """
        if not self._config_loaded:
            self._load_default_config()

        # 根据类型映射到配置中的logger名称
        logger_mapping = {
            "standard": name,
            "finish": "finish",
            "enhanced_checker": "enhanced_checker",
            "error": "error",
        }

        logger_name = logger_mapping.get(logger_type, name)

        if logger_name not in self._loggers:
            self._loggers[logger_name] = logging.getLogger(logger_name)

            # 确保logger不会传播到父logger，避免重复输出
            self._loggers[logger_name].propagate = False

        return self._loggers[logger_name]

    def cleanup_old_logs(self, retention_days: int = 7):
        """
        清理过期日志文件，遵循规范与流程.md的清理策略

        Args:
            retention_days: 保留天数，默认7天
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_count = 0

        for log_subdir in self._logs_dir.iterdir():
            if log_subdir.is_dir():
                for log_file in log_subdir.glob("*.log"):
                    try:
                        if log_file.stat().st_mtime < cutoff_date.timestamp():
                            log_file.unlink()
                            cleaned_count += 1
                    except Exception as e:
                        # 记录清理失败，但不中断整个清理过程
                        error_logger = self.get_logger("error", "error")
                        error_logger.warning(f"清理日志文件失败 {log_file}: {e}")

        if cleaned_count > 0:
            app_logger = self.get_logger("unified_logging")
            app_logger.info(f"已清理 {cleaned_count} 个过期日志文件")

    def shutdown(self):
        """关闭日志系统，清理资源"""
        logging.shutdown()
        self._loggers.clear()
        self._config_loaded = False


# 全局统一日志系统实例
_unified_logging = UnifiedLoggingSystem()


def get_logger(name: str, logger_type: str = "standard") -> logging.Logger:
    """
    获取统一配置的日志器（全局函数接口）

    这是项目中获取日志器的统一入口，替代所有其他日志获取方式。

    Args:
        name: 日志器名称
        logger_type: 日志器类型

    Returns:
        配置好的日志器实例
    """
    return _unified_logging.get_logger(name, logger_type)


def initialize_logging():
    """
    初始化统一日志系统

    在应用启动时调用，确保日志系统正确配置。
    """
    global _unified_logging
    if not _unified_logging._config_loaded:
        _unified_logging._load_default_config()

    # 执行日志清理
    _unified_logging.cleanup_old_logs()

    # 记录初始化完成
    logger = get_logger("unified_logging")
    logger.info("统一日志系统初始化完成")
    logger.info(f"项目根目录: {_unified_logging._project_root}")
    logger.info(f"日志目录: {_unified_logging._logs_dir}")


def cleanup_logs(retention_days: int = 7):
    """
    清理过期日志文件（全局函数接口）

    Args:
        retention_days: 保留天数
    """
    _unified_logging.cleanup_old_logs(retention_days)


def shutdown_logging():
    """
    关闭日志系统（全局函数接口）
    """
    _unified_logging.shutdown()


def log_function_call(logger_name: str = None, level: int = logging.INFO):
    """
    函数调用日志装饰器

    Args:
        logger_name: 日志器名称，默认使用函数所在模块名
        level: 日志级别
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger_name
            if logger_name is None:
                logger_name = func.__module__

            logger = get_logger(logger_name)

            # 记录函数调用开始
            logger.log(level, f"函数调用开始: {func.__name__}")

            try:
                result = func(*args, **kwargs)
                logger.log(level, f"函数调用完成: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"函数调用异常: {func.__name__}", exc_info=True)
                raise

        return wrapper

    return decorator


if __name__ == "__main__":
    # 测试统一日志系统
    initialize_logging()

    # 测试不同类型的日志器
    app_logger = get_logger("test_app")
    finish_logger = get_logger("test_finish", "finish")
    checker_logger = get_logger("test_checker", "enhanced_checker")

    app_logger.info("应用日志测试")
    finish_logger.info("完成脚本日志测试")
    checker_logger.info("结构检查日志测试")

    app_logger.debug("调试信息")
    app_logger.warning("警告信息")
    app_logger.error("错误信息")

    print("统一日志系统测试完成")
