# -*- coding: utf-8 -*-
"""
性能监控模块
提供执行时间跟踪、内存使用监控和性能报告生成功能

作者: 雨俊
版本: 1.0.0
更新日期: 2025-07-08
"""

import time
import threading
import psutil
import json
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

# from pathlib import Path  # unused
from contextlib import contextmanager
import logging

# 配置日志（已在主程序中配置）
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标数据类"""

    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    thread_id: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "memory_before_mb": round(self.memory_before, 2),
            "memory_after_mb": round(self.memory_after, 2),
            "memory_peak_mb": round(self.memory_peak, 2),
            "memory_delta_mb": round(self.memory_after - self.memory_before, 2),
            "thread_id": self.thread_id,
            "timestamp": self.timestamp,
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self._lock = threading.Lock()
        self._process = psutil.Process()
        self._active_operations: Dict[str, Dict[str, Any]] = {}

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            return self._process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.warning(f"获取内存使用量失败: {e}")
            return 0.0

    @contextmanager
    def track_operation(self, operation_name: str):
        """上下文管理器，用于跟踪操作性能"""
        start_time = time.time()
        memory_before = self._get_memory_usage()
        thread_id = threading.get_ident()

        # 记录开始状态
        operation_key = f"{operation_name}_{thread_id}_{start_time}"
        self._active_operations[operation_key] = {
            "start_time": start_time,
            "memory_before": memory_before,
            "memory_peak": memory_before,
        }

        try:
            yield self
        finally:
            end_time = time.time()
            memory_after = self._get_memory_usage()

            # 获取峰值内存
            operation_data = self._active_operations.pop(operation_key, {})
            memory_peak = operation_data.get("memory_peak", memory_after)

            # 创建性能指标
            metric = PerformanceMetric(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                thread_id=thread_id,
            )

            # 线程安全地添加指标
            with self._lock:
                self.metrics.append(metric)

            logger.debug(f"操作 '{operation_name}' 完成，耗时: {metric.duration:.3f}s")

    def start_operation(self, operation_name: str) -> str:
        """开始跟踪操作（手动模式）"""
        start_time = time.time()
        memory_before = self._get_memory_usage()
        thread_id = threading.get_ident()

        operation_key = f"{operation_name}_{thread_id}_{start_time}"
        self._active_operations[operation_key] = {
            "operation_name": operation_name,
            "start_time": start_time,
            "memory_before": memory_before,
            "memory_peak": memory_before,
            "thread_id": thread_id,
        }

        return operation_key

    def end_operation(self, operation_key: str):
        """结束跟踪操作（手动模式）"""
        if operation_key not in self._active_operations:
            logger.warning(f"未找到操作键: {operation_key}")
            return

        end_time = time.time()
        memory_after = self._get_memory_usage()

        operation_data = self._active_operations.pop(operation_key)

        metric = PerformanceMetric(
            operation=operation_data["operation_name"],
            start_time=operation_data["start_time"],
            end_time=end_time,
            duration=end_time - operation_data["start_time"],
            memory_before=operation_data["memory_before"],
            memory_after=memory_after,
            memory_peak=operation_data["memory_peak"],
            thread_id=operation_data["thread_id"],
        )

        with self._lock:
            self.metrics.append(metric)

    def update_memory_peak(self):
        """更新活动操作的峰值内存"""
        current_memory = self._get_memory_usage()
        for operation_data in self._active_operations.values():
            if current_memory > operation_data["memory_peak"]:
                operation_data["memory_peak"] = current_memory

    def get_metrics_by_operation(self, operation_name: str) -> List[PerformanceMetric]:
        """按操作名称获取指标"""
        with self._lock:
            return [
                metric for metric in self.metrics if metric.operation == operation_name
            ]

    def get_average_duration(self, operation_name: str) -> float:
        """获取操作的平均执行时间"""
        metrics = self.get_metrics_by_operation(operation_name)
        if not metrics:
            return 0.0
        return sum(metric.duration for metric in metrics) / len(metrics)

    def get_total_duration(self, operation_name: str = None) -> float:
        """获取总执行时间"""
        with self._lock:
            if operation_name:
                metrics = [m for m in self.metrics if m.operation == operation_name]
            else:
                metrics = self.metrics
            return sum(metric.duration for metric in metrics)

    def get_memory_statistics(self) -> Dict[str, float]:
        """获取内存使用统计"""
        with self._lock:
            if not self.metrics:
                return {"min": 0, "max": 0, "avg": 0, "peak": 0}

            memory_values = [metric.memory_after for metric in self.metrics]
            peak_values = [metric.memory_peak for metric in self.metrics]

            return {
                "min_mb": round(min(memory_values), 2),
                "max_mb": round(max(memory_values), 2),
                "avg_mb": round(sum(memory_values) / len(memory_values), 2),
                "peak_mb": round(max(peak_values), 2),
            }

    def generate_performance_report(
        self, include_details: bool = False
    ) -> Dict[str, Any]:
        """生成性能报告"""
        with self._lock:
            if not self.metrics:
                return {
                    "summary": "暂无性能数据",
                    "total_operations": 0,
                    "total_duration": 0,
                    "memory_stats": self.get_memory_statistics(),
                }

            # 按操作分组统计
            operation_stats = {}
            for metric in self.metrics:
                op_name = metric.operation
                if op_name not in operation_stats:
                    operation_stats[op_name] = {
                        "count": 0,
                        "total_duration": 0,
                        "min_duration": float("inf"),
                        "max_duration": 0,
                        "avg_memory_delta": 0,
                        "total_memory_delta": 0,
                    }

                stats = operation_stats[op_name]
                stats["count"] += 1
                stats["total_duration"] += metric.duration
                stats["min_duration"] = min(stats["min_duration"], metric.duration)
                stats["max_duration"] = max(stats["max_duration"], metric.duration)

                memory_delta = metric.memory_after - metric.memory_before
                stats["total_memory_delta"] += memory_delta

            # 计算平均值
            for stats in operation_stats.values():
                stats["avg_duration"] = stats["total_duration"] / stats["count"]
                stats["avg_memory_delta"] = stats["total_memory_delta"] / stats["count"]
                # 格式化数值
                for key in [
                    "total_duration",
                    "min_duration",
                    "max_duration",
                    "avg_duration",
                ]:
                    stats[key] = round(stats[key], 3)
                for key in ["avg_memory_delta", "total_memory_delta"]:
                    stats[key] = round(stats[key], 2)

            report = {
                "summary": f"共执行 {len(self.metrics)} 个操作",
                "total_operations": len(self.metrics),
                "total_duration": round(sum(m.duration for m in self.metrics), 3),
                "memory_stats": self.get_memory_statistics(),
                "operation_stats": operation_stats,
                "generated_at": datetime.now().isoformat(),
            }

            if include_details:
                report["detailed_metrics"] = [
                    metric.to_dict() for metric in self.metrics
                ]

            return report

    def save_report(self, file_path: str, include_details: bool = False):
        """保存性能报告到文件"""
        report = self.generate_performance_report(include_details)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"性能报告已保存至: {file_path}")
        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")

    def clear_metrics(self):
        """清空所有性能指标"""
        with self._lock:
            self.metrics.clear()
            self._active_operations.clear()
        logger.info("性能指标已清空")

    def get_slow_operations(self, threshold: float = 1.0) -> List[PerformanceMetric]:
        """获取执行时间超过阈值的慢操作"""
        with self._lock:
            return [metric for metric in self.metrics if metric.duration > threshold]

    def get_memory_intensive_operations(
        self, threshold: float = 100.0
    ) -> List[PerformanceMetric]:
        """获取内存使用超过阈值的操作"""
        with self._lock:
            return [
                metric
                for metric in self.metrics
                if (metric.memory_after - metric.memory_before) > threshold
            ]


# 全局性能监控器实例
_global_monitor = None


def get_global_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def track_performance(operation_name: str):
    """装饰器：自动跟踪函数性能"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_global_monitor()
            with monitor.track_operation(f"{func.__name__}_{operation_name}"):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# 测试代码
if __name__ == "__main__":
    # 创建性能监控器
    monitor = PerformanceMonitor()

    # 测试上下文管理器模式
    print("测试性能监控功能...")

    with monitor.track_operation("文件扫描测试"):
        time.sleep(0.1)  # 模拟文件扫描

    with monitor.track_operation("配置加载测试"):
        time.sleep(0.05)  # 模拟配置加载

    # 测试手动模式
    op_key = monitor.start_operation("手动操作测试")
    time.sleep(0.02)
    monitor.end_operation(op_key)

    # 生成报告
    report = monitor.generate_performance_report(include_details=True)
    print("\n性能报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 保存报告
    monitor.save_report("performance_report.json")

    print("\n性能监控模块测试完成！")
