#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置模块

提供项目统一的日志配置和管理功能，包括：
- 标准化日志配置
- 日志器工厂
- 性能优化的日志记录
- 日志文件管理

Author: AI Assistant
Date: 2024
"""

import os
import sys
import logging
import logging.config
import logging.handlers
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from datetime import datetime, timedelta
import json
import threading
from functools import wraps
from collections import defaultdict
import time
import glob


class LoggingConfig:
    """统一日志配置管理器"""

    DEFAULT_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d [%(funcName)s] - %(message)s [PID:%(process)d TID:%(thread)d]',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': 'logs/其他日志/application.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/其他日志/errors.log',
                'maxBytes': 10485760,
                'backupCount': 10,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False
            },
            'error': {
                'handlers': ['error_file'],
                'level': 'ERROR',
                'propagate': False
            }
        }
    }

    def __init__(
            self,
            config_path: Optional[str] = None,
            logs_dir: str = 'logs'):
        self.config_path = config_path
        self.logs_dir = Path(logs_dir)
        self.config = self._load_config()
        self._ensure_logs_directory()
        self._configured = False
        self._lock = threading.Lock()

    def _load_config(self) -> Dict[str, Any]:
        """加载日志配置"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.endswith('.json'):
                        return json.load(f)
                    # 可以扩展支持YAML等格式
            except Exception as e:
                print(
                    f"Warning: Failed to load logging config from {
                        self.config_path}: {e}")

        return self.DEFAULT_CONFIG.copy()

    def _ensure_logs_directory(self):
        """确保日志目录存在"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / 'archive').mkdir(exist_ok=True)
        (self.logs_dir / 'temp').mkdir(exist_ok=True)

    def configure(self, level: Optional[str] = None,
                  console_enabled: bool = True,
                  file_enabled: bool = True,
                  performance_mode: bool = False):
        """配置日志系统"""
        with self._lock:
            if self._configured:
                return

            # 更新配置
            if level:
                self.config['loggers']['']['level'] = level.upper()

            # 更新文件路径为绝对路径
            for handler_name, handler_config in self.config['handlers'].items(
            ):
                if 'filename' in handler_config:
                    filename = handler_config['filename']
                    if not os.path.isabs(filename):
                        handler_config['filename'] = str(
                            self.logs_dir / os.path.basename(filename))

            # 根据性能模式调整配置
            if performance_mode:
                self._optimize_for_performance()

            # 配置处理器
            handlers = []
            if console_enabled:
                handlers.append('console')
            if file_enabled:
                handlers.append('file')

            self.config['loggers']['']['handlers'] = handlers

            # 应用配置
            logging.config.dictConfig(self.config)
            self._configured = True

    def _optimize_for_performance(self):
        """性能模式优化"""
        # 减少文件日志级别
        if 'file' in self.config['handlers']:
            self.config['handlers']['file']['level'] = 'WARNING'

        # 使用简单格式
        for handler_name in ['console', 'file']:
            if handler_name in self.config['handlers']:
                self.config['handlers'][handler_name]['formatter'] = 'simple'

    def get_logger(self, name: str) -> 'StandardLogger':
        """获取标准日志器"""
        if not self._configured:
            self.configure()

        return StandardLogger(name)


class StandardLogger:
    """标准日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.trace_id = None
        self._performance_mode = False
        self._debug_enabled = self.logger.isEnabledFor(logging.DEBUG)

    def set_trace_id(self, trace_id: str):
        """设置追踪ID"""
        self.trace_id = trace_id

    def set_performance_mode(self, enabled: bool):
        """设置性能模式"""
        self._performance_mode = enabled

    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日志消息"""
        if self.trace_id:
            kwargs['trace_id'] = self.trace_id

        if kwargs:
            context = ' '.join([f'{k}={v}' for k, v in kwargs.items()])
            return f"{message} [{context}]"
        return message

    def debug(self, message: str, **kwargs):
        """记录调试信息"""
        if self._debug_enabled and not self._performance_mode:
            self.logger.debug(self._format_message(message, **kwargs))

    def debug_if_enabled(self, message_func: Callable[[], str], **kwargs):
        """仅在DEBUG级别启用时才执行消息构建"""
        if self._debug_enabled and not self._performance_mode:
            self.debug(message_func(), **kwargs)

    def info(self, message: str, **kwargs):
        """记录一般信息"""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs):
        """记录警告信息"""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, error: Exception = None, **kwargs):
        """记录错误信息"""
        if error:
            kwargs['error_type'] = error.__class__.__name__
            kwargs['error_message'] = str(error)
        self.logger.error(
            self._format_message(
                message,
                **kwargs),
            exc_info=error)

    def critical(self, message: str, error: Exception = None, **kwargs):
        """记录严重错误"""
        if error:
            kwargs['error_type'] = error.__class__.__name__
            kwargs['error_message'] = str(error)
        self.logger.critical(
            self._format_message(
                message,
                **kwargs),
            exc_info=error)

    def bulk_log(self, level: int, messages: List[str]):
        """批量日志记录"""
        if self.logger.isEnabledFor(level):
            combined_message = '\n'.join(messages)
            self.logger.log(
                level, f"Bulk log ({
                    len(messages)} entries):\n{combined_message}")


class PerformanceLogger(StandardLogger):
    """性能优化的日志记录器"""

    def __init__(self, name: str, buffer_size: int = 100):
        super().__init__(name)
        self.buffer_size = buffer_size
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.last_flush = time.time()
        self.flush_interval = 5.0  # 5秒

    def _should_flush(self) -> bool:
        """判断是否应该刷新缓冲区"""
        return (len(self.buffer) >= self.buffer_size or
                time.time() - self.last_flush >= self.flush_interval)

    def _flush_buffer(self):
        """刷新缓冲区"""
        if self.buffer:
            self.bulk_log(logging.INFO, self.buffer)
            self.buffer.clear()
            self.last_flush = time.time()

    def buffered_log(self, message: str, **kwargs):
        """缓冲日志记录"""
        formatted_message = self._format_message(message, **kwargs)

        with self.buffer_lock:
            self.buffer.append(formatted_message)
            if self._should_flush():
                self._flush_buffer()

    def flush(self):
        """手动刷新缓冲区"""
        with self.buffer_lock:
            self._flush_buffer()


class LogCleaner:
    """日志清理器"""

    def __init__(self, logs_dir: str = 'logs'):
        self.logs_dir = Path(logs_dir)
        self.logger = StandardLogger('LogCleaner')
        self.retention_config = {
            'application': 30,  # 保留30天
            'errors': 90,       # 保留90天
            'performance': 7,   # 保留7天
        }

    def cleanup_old_logs(self, dry_run: bool = False):
        """清理过期日志"""
        self.logger.info("开始清理过期日志", dry_run=dry_run)

        total_cleaned = 0
        total_size_freed = 0

        for log_type, retention_days in self.retention_config.items():
            cleaned, size_freed = self._cleanup_log_type(
                log_type, retention_days, dry_run)
            total_cleaned += cleaned
            total_size_freed += size_freed

        self.logger.info(
            "日志清理完成",
            files_cleaned=total_cleaned,
            size_freed_mb=f"{total_size_freed / 1024 / 1024:.2f}"
        )

    def _cleanup_log_type(
            self,
            log_type: str,
            retention_days: int,
            dry_run: bool) -> tuple:
        """清理特定类型的过期日志"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        log_pattern = str(self.logs_dir / f"{log_type}*.log*")

        cleaned_count = 0
        size_freed = 0

        for log_file in glob.glob(log_pattern):
            file_path = Path(log_file)
            if self._is_file_old(file_path, cutoff_date):
                file_size = file_path.stat().st_size

                if dry_run:
                    self.logger.info(f"[DRY RUN] 将删除文件: {file_path}")
                else:
                    try:
                        file_path.unlink()
                        self.logger.debug(f"已删除日志文件: {file_path}")
                    except Exception as e:
                        self.logger.error(f"删除日志文件失败: {file_path}", error=e)
                        continue

                cleaned_count += 1
                size_freed += file_size

        return cleaned_count, size_freed

    def _is_file_old(self, file_path: Path, cutoff_date: datetime) -> bool:
        """判断文件是否过期"""
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime < cutoff_date
        except Exception:
            return False


# 全局日志配置实例
_global_config = None
_config_lock = threading.Lock()


def initialize_logging(config_path: Optional[str] = None,
                       logs_dir: str = 'logs',
                       level: str = 'INFO',
                       console_enabled: bool = True,
                       file_enabled: bool = True,
                       performance_mode: bool = False):
    """初始化全局日志配置"""
    global _global_config

    with _config_lock:
        if _global_config is None:
            _global_config = LoggingConfig(config_path, logs_dir)

        _global_config.configure(
            level=level,
            console_enabled=console_enabled,
            file_enabled=file_enabled,
            performance_mode=performance_mode
        )


def get_logger(name: str) -> StandardLogger:
    """获取标准日志器"""
    global _global_config

    if _global_config is None:
        initialize_logging()

    return _global_config.get_logger(name)


def get_performance_logger(
        name: str,
        buffer_size: int = 100) -> PerformanceLogger:
    """获取性能优化的日志器"""
    if _global_config is None:
        initialize_logging()

    return PerformanceLogger(name, buffer_size)


def cleanup_logs(dry_run: bool = False):
    """清理过期日志"""
    cleaner = LogCleaner()
    cleaner.cleanup_old_logs(dry_run)


# 日志装饰器
def log_function_call(logger: Optional[StandardLogger] = None,
                      level: int = logging.INFO,
                      include_args: bool = False,
                      include_result: bool = False):
    """函数调用日志装饰器"""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"

            # 记录函数开始
            log_data = {'function': func_name}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)

            logger.logger.log(
                level, logger._format_message(
                    "函数调用开始", **log_data))

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录函数完成
                log_data['duration'] = f"{duration:.3f}s"
                if include_result:
                    log_data['result'] = str(result)[:200]  # 限制结果长度

                logger.logger.log(
                    level, logger._format_message(
                        "函数调用完成", **log_data))
                return result

            except Exception as e:
                duration = time.time() - start_time
                log_data['duration'] = f"{duration:.3f}s"
                log_data['error'] = str(e)

                logger.logger.log(
                    logging.ERROR, logger._format_message(
                        "函数调用异常", **log_data))
                raise

        return wrapper
    return decorator


if __name__ == '__main__':
    # 测试代码
    initialize_logging(level='DEBUG')

    logger = get_logger('test')
    logger.info("测试日志记录", test_param="value")
    logger.debug("调试信息")
    logger.warning("警告信息")

    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.error("捕获异常", error=e)

    # 测试性能日志器
    perf_logger = get_performance_logger('performance_test')
    for i in range(10):
        perf_logger.buffered_log(f"性能测试消息 {i}")
    perf_logger.flush()

    print("日志测试完成")
