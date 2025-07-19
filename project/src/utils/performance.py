#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-PMC AI设计助理 - 性能监控工具
"""

import functools
import gc
import json
import sys
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from src.utils.logger import get_logger


@dataclass
class PerformanceMetrics:
    """性能指标"""

    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    process_count: int = 0
    thread_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_usage_percent": self.disk_usage_percent,
            "disk_read_mb": self.disk_read_mb,
            "disk_write_mb": self.disk_write_mb,
            "network_sent_mb": self.network_sent_mb,
            "network_recv_mb": self.network_recv_mb,
            "process_count": self.process_count,
            "thread_count": self.thread_count,
        }


@dataclass
class FunctionMetrics:
    """函数性能指标"""

    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: Optional[datetime] = None
    error_count: int = 0

    def add_call(self, execution_time: float, has_error: bool = False):
        """添加函数调用记录"""
        self.call_count += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.call_count
        self.last_call_time = datetime.now()

        if has_error:
            self.error_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "call_count": self.call_count,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0.0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "last_call_time": (
                self.last_call_time.isoformat() if self.last_call_time else None
            ),
            "error_count": self.error_count,
            "error_rate": (
                self.error_count / self.call_count if self.call_count > 0 else 0.0
            ),
        }


class PerformanceTimer:
    """性能计时器"""

    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
        self.logger = get_logger(self.__class__.__name__)

    def start(self):
        """开始计时"""
        self.start_time = time.perf_counter()
        return self

    def stop(self) -> float:
        """停止计时

        Returns:
            float: 经过的时间（秒）
        """
        if self.start_time is None:
            raise ValueError("计时器未启动")

        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time

        if self.name:
            self.logger.debug(f"{self.name} 执行时间: {self.elapsed_time:.4f}秒")

        return self.elapsed_time

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class SystemMonitor:
    """系统监控器"""

    def __init__(self, interval: float = 1.0, max_history: int = 1000):
        self.interval = interval
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_thread = None
        self.logger = get_logger(self.__class__.__name__)

        # 初始化网络和磁盘计数器
        self._last_net_io = None
        self._last_disk_io = None
        self._last_time = None

    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前系统指标

        Returns:
            PerformanceMetrics: 当前系统指标
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # 磁盘使用率（根目录）
            disk_usage = psutil.disk_usage("/")
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100

            # 磁盘IO
            current_disk_io = psutil.disk_io_counters()
            disk_read_mb = 0.0
            disk_write_mb = 0.0

            if self._last_disk_io and self._last_time:
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    disk_read_mb = (
                        (current_disk_io.read_bytes - self._last_disk_io.read_bytes)
                        / (1024 * 1024)
                        / time_delta
                    )
                    disk_write_mb = (
                        (current_disk_io.write_bytes - self._last_disk_io.write_bytes)
                        / (1024 * 1024)
                        / time_delta
                    )

            self._last_disk_io = current_disk_io

            # 网络IO
            current_net_io = psutil.net_io_counters()
            network_sent_mb = 0.0
            network_recv_mb = 0.0

            if self._last_net_io and self._last_time:
                time_delta = time.time() - self._last_time
                if time_delta > 0:
                    network_sent_mb = (
                        (current_net_io.bytes_sent - self._last_net_io.bytes_sent)
                        / (1024 * 1024)
                        / time_delta
                    )
                    network_recv_mb = (
                        (current_net_io.bytes_recv - self._last_net_io.bytes_recv)
                        / (1024 * 1024)
                        / time_delta
                    )

            self._last_net_io = current_net_io
            self._last_time = time.time()

            # 进程和线程数
            process_count = len(psutil.pids())
            thread_count = threading.active_count()

            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_read_mb=disk_read_mb,
                disk_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                process_count=process_count,
                thread_count=thread_count,
            )

        except Exception as e:
            self.logger.error(f"获取系统指标失败: {e}")
            return PerformanceMetrics()

    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            self.logger.warning("监控已在运行")
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("系统监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("系统监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"监控循环出错: {e}")
                time.sleep(self.interval)

    def get_metrics_history(
        self, duration_minutes: Optional[int] = None
    ) -> List[PerformanceMetrics]:
        """获取指标历史

        Args:
            duration_minutes: 获取最近多少分钟的数据，None表示获取所有数据

        Returns:
            List[PerformanceMetrics]: 指标历史列表
        """
        if duration_minutes is None:
            return list(self.metrics_history)

        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_average_metrics(
        self, duration_minutes: Optional[int] = None
    ) -> Dict[str, float]:
        """获取平均指标

        Args:
            duration_minutes: 计算最近多少分钟的平均值，None表示计算所有数据

        Returns:
            Dict[str, float]: 平均指标字典
        """
        history = self.get_metrics_history(duration_minutes)

        if not history:
            return {}

        total_cpu = sum(m.cpu_percent for m in history)
        total_memory = sum(m.memory_percent for m in history)
        total_disk = sum(m.disk_usage_percent for m in history)
        count = len(history)

        return {
            "avg_cpu_percent": total_cpu / count,
            "avg_memory_percent": total_memory / count,
            "avg_disk_usage_percent": total_disk / count,
            "sample_count": count,
        }

    def export_metrics(self, file_path: Path, duration_minutes: Optional[int] = None):
        """导出指标到文件

        Args:
            file_path: 导出文件路径
            duration_minutes: 导出最近多少分钟的数据
        """
        try:
            history = self.get_metrics_history(duration_minutes)
            data = {
                "export_time": datetime.now().isoformat(),
                "duration_minutes": duration_minutes,
                "metrics_count": len(history),
                "metrics": [m.to_dict() for m in history],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"指标导出完成: {file_path}")

        except Exception as e:
            self.logger.error(f"指标导出失败: {e}")


class FunctionProfiler:
    """函数性能分析器"""

    def __init__(self):
        self.function_metrics: Dict[str, FunctionMetrics] = {}
        self.logger = get_logger(self.__class__.__name__)
        self._lock = threading.Lock()

    def profile(self, func_name: Optional[str] = None):
        """函数性能分析装饰器

        Args:
            func_name: 函数名称，如果为None则使用函数的__name__
        """

        def decorator(func: Callable) -> Callable:
            name = func_name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                has_error = False

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    has_error = True
                    raise
                finally:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    with self._lock:
                        if name not in self.function_metrics:
                            self.function_metrics[name] = FunctionMetrics(name=name)

                        self.function_metrics[name].add_call(execution_time, has_error)

            return wrapper

        return decorator

    @contextmanager
    def profile_block(self, block_name: str):
        """代码块性能分析上下文管理器

        Args:
            block_name: 代码块名称
        """
        start_time = time.perf_counter()
        has_error = False

        try:
            yield
        except Exception:
            has_error = True
            raise
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            with self._lock:
                if block_name not in self.function_metrics:
                    self.function_metrics[block_name] = FunctionMetrics(name=block_name)

                self.function_metrics[block_name].add_call(execution_time, has_error)

    def get_metrics(
        self, func_name: Optional[str] = None
    ) -> Union[FunctionMetrics, Dict[str, FunctionMetrics]]:
        """获取函数指标

        Args:
            func_name: 函数名称，如果为None则返回所有函数的指标

        Returns:
            Union[FunctionMetrics, Dict[str, FunctionMetrics]]: 函数指标
        """
        with self._lock:
            if func_name:
                return self.function_metrics.get(func_name)
            else:
                return self.function_metrics.copy()

    def get_top_functions(
        self, metric: str = "total_time", limit: int = 10
    ) -> List[FunctionMetrics]:
        """获取性能排名前N的函数

        Args:
            metric: 排序指标（total_time, avg_time, call_count, error_count）
            limit: 返回数量限制

        Returns:
            List[FunctionMetrics]: 排序后的函数指标列表
        """
        with self._lock:
            metrics_list = list(self.function_metrics.values())

            if metric == "total_time":
                metrics_list.sort(key=lambda x: x.total_time, reverse=True)
            elif metric == "avg_time":
                metrics_list.sort(key=lambda x: x.avg_time, reverse=True)
            elif metric == "call_count":
                metrics_list.sort(key=lambda x: x.call_count, reverse=True)
            elif metric == "error_count":
                metrics_list.sort(key=lambda x: x.error_count, reverse=True)
            else:
                raise ValueError(f"不支持的排序指标: {metric}")

            return metrics_list[:limit]

    def reset_metrics(self, func_name: Optional[str] = None):
        """重置函数指标

        Args:
            func_name: 函数名称，如果为None则重置所有函数的指标
        """
        with self._lock:
            if func_name:
                if func_name in self.function_metrics:
                    del self.function_metrics[func_name]
            else:
                self.function_metrics.clear()

    def export_report(self, file_path: Path):
        """导出性能报告

        Args:
            file_path: 报告文件路径
        """
        try:
            with self._lock:
                report_data = {
                    "export_time": datetime.now().isoformat(),
                    "total_functions": len(self.function_metrics),
                    "functions": {
                        name: metrics.to_dict()
                        for name, metrics in self.function_metrics.items()
                    },
                }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"性能报告导出完成: {file_path}")

        except Exception as e:
            self.logger.error(f"性能报告导出失败: {e}")


class MemoryProfiler:
    """内存分析器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况

        Returns:
            Dict[str, float]: 内存使用信息（MB）
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / (1024 * 1024),  # 物理内存
                "vms_mb": memory_info.vms / (1024 * 1024),  # 虚拟内存
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            }

        except Exception as e:
            self.logger.error(f"获取内存使用情况失败: {e}")
            return {}

    def force_garbage_collection(self) -> Dict[str, int]:
        """强制垃圾回收

        Returns:
            Dict[str, int]: 垃圾回收统计信息
        """
        try:
            # 获取回收前的对象数量
            before_objects = len(gc.get_objects())

            # 执行垃圾回收
            collected = gc.collect()

            # 获取回收后的对象数量
            after_objects = len(gc.get_objects())

            stats = {
                "collected_objects": collected,
                "objects_before": before_objects,
                "objects_after": after_objects,
                "objects_freed": before_objects - after_objects,
            }

            self.logger.info(f"垃圾回收完成: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"垃圾回收失败: {e}")
            return {}

    @contextmanager
    def memory_monitor(self, operation_name: str = ""):
        """内存监控上下文管理器

        Args:
            operation_name: 操作名称
        """
        before_memory = self.get_memory_usage()
        start_time = time.perf_counter()

        try:
            yield
        finally:
            end_time = time.perf_counter()
            after_memory = self.get_memory_usage()

            if before_memory and after_memory:
                memory_diff = after_memory["rss_mb"] - before_memory["rss_mb"]
                execution_time = end_time - start_time

                self.logger.info(
                    f"内存监控 {operation_name}: "
                    f"内存变化={memory_diff:.2f}MB, "
                    f"执行时间={execution_time:.4f}秒, "
                    f"当前内存={after_memory['rss_mb']:.2f}MB"
                )


# 全局实例
system_monitor = SystemMonitor()
function_profiler = FunctionProfiler()
memory_profiler = MemoryProfiler()


# 便捷装饰器
def profile_performance(func_name: Optional[str] = None):
    """性能分析装饰器

    Args:
        func_name: 函数名称
    """
    return function_profiler.profile(func_name)


@contextmanager
def timer(name: str = ""):
    """计时器上下文管理器

    Args:
        name: 计时器名称
    """
    with PerformanceTimer(name) as t:
        yield t


@contextmanager
def profile_block(block_name: str):
    """代码块性能分析上下文管理器

    Args:
        block_name: 代码块名称
    """
    with function_profiler.profile_block(block_name):
        yield


@contextmanager
def monitor_memory(operation_name: str = ""):
    """内存监控上下文管理器

    Args:
        operation_name: 操作名称
    """
    with memory_profiler.memory_monitor(operation_name):
        yield


def get_system_info() -> Dict[str, Any]:
    """获取系统信息

    Returns:
        Dict[str, Any]: 系统信息
    """
    try:
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }
    except Exception as e:
        logger = get_logger("get_system_info")
        logger.error(f"获取系统信息失败: {e}")
        return {}
