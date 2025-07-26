#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理和日志系统使用示例

展示如何在项目中使用新的统一错误处理和日志记录系统。

Author: AI Assistant
Date: 2025
"""

from tools.enhanced_error_handling import (
    handle_errors, with_trace_id, retry_on_failure, measure_performance,
    get_error_handler, get_error_monitor, get_performance_monitor,
    TraceContext, error_context, EnhancedError, RecoverableError, CriticalError
)
from tools.logging_config import initialize_logging, get_logger, get_performance_logger
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入新的错误处理和日志模块


class ProjectService:
    """项目服务示例类"""

    def __init__(self):
        # 初始化日志系统
        initialize_logging(
            config_path=str(project_root / 'config' / 'logging_config.json'),
            level='INFO',
            console_enabled=True,
            file_enabled=True
        )

        # 获取日志器
        self.logger = get_logger(self.__class__.__name__)
        self.perf_logger = get_performance_logger('performance')

        # 获取错误处理器和监控器
        self.error_handler = get_error_handler()
        self.error_monitor = get_error_monitor()
        self.performance_monitor = get_performance_monitor()

        self.logger.info("ProjectService 初始化完成")

    @handle_errors(reraise=True)
    @with_trace_id()
    @measure_performance(warn_threshold=2.0)
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据的示例方法"""
        self.logger.info(
            "开始处理数据",
            data_size=len(data),
            data_keys=list(
                data.keys()))

        try:
            # 模拟数据验证
            validated_data = self._validate_data(data)

            # 模拟数据处理
            processed_data = self._process_validated_data(validated_data)

            # 模拟数据保存
            result = self._save_processed_data(processed_data)

            self.logger.info(
                "数据处理完成",
                result_id=result.get('id'),
                processing_time=result.get('processing_time'))
            return result

        except Exception as e:
            self.logger.error("数据处理失败", error=e, data_keys=list(data.keys()))
            raise

    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据"""
        self.logger.debug("开始数据验证")

        # 模拟验证逻辑
        if not data:
            raise RecoverableError(
                "数据为空",
                recovery_suggestion="请提供有效的数据",
                context={'data_type': type(data).__name__}
            )

        if 'required_field' not in data:
            raise EnhancedError(
                "缺少必需字段",
                error_code="MISSING_REQUIRED_FIELD",
                context={
                    'missing_field': 'required_field',
                    'available_fields': list(
                        data.keys())})

        # 模拟验证通过
        self.logger.debug("数据验证通过")
        return data

    @retry_on_failure(max_retries=3,
                      error_types=(ConnectionError, TimeoutError))
    def _process_validated_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理验证后的数据"""
        self.logger.debug("开始处理验证后的数据")

        # 模拟可能失败的网络操作
        if data.get('simulate_network_error'):
            import random
            if random.random() < 0.7:  # 70% 概率失败
                raise ConnectionError("模拟网络连接失败")

        # 模拟处理耗时
        processing_time = data.get('processing_time', 0.1)
        time.sleep(processing_time)

        # 模拟处理结果
        processed_data = {
            'original_data': data,
            'processed_at': time.time(),
            'processing_time': processing_time,
            'status': 'processed'
        }

        self.logger.debug("数据处理完成", processing_time=processing_time)
        return processed_data

    def _save_processed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """保存处理后的数据"""
        self.logger.debug("开始保存处理后的数据")

        # 模拟保存操作
        if data.get('simulate_save_error'):
            raise CriticalError(
                "数据保存失败",
                context={'data_size': len(str(data))}
            )

        # 模拟保存成功
        result = {
            'id': f"data_{int(time.time())}",
            'saved_at': time.time(),
            'processing_time': data.get('processing_time', 0),
            'status': 'saved'
        }

        self.logger.debug("数据保存完成", result_id=result['id'])
        return result

    def batch_process(
            self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理数据"""
        with TraceContext.trace_scope() as trace_id:
            self.logger.info(
                "开始批量处理",
                batch_size=len(data_list),
                trace_id=trace_id)

            results = []
            errors = []

            for i, data in enumerate(data_list):
                try:
                    with error_context({'batch_index': i, 'batch_size': len(data_list)}):
                        result = self.process_data(data)
                        results.append(result)

                        # 使用性能日志器记录批量处理进度
                        self.perf_logger.buffered_log(
                            f"批量处理进度: {i + 1}/{len(data_list)}",
                            progress=f"{(i + 1) / len(data_list) * 100:.1f}%"
                        )

                except Exception as e:
                    self.logger.warning(
                        f"批量处理中的单项失败", batch_index=i, error=str(e))
                    errors.append({'index': i, 'error': str(e), 'data': data})

            # 刷新性能日志缓冲区
            self.perf_logger.flush()

            self.logger.info(
                "批量处理完成",
                total_items=len(data_list),
                successful_items=len(results),
                failed_items=len(errors),
                trace_id=trace_id
            )

            return {
                'results': results,
                'errors': errors,
                'summary': {
                    'total': len(data_list),
                    'successful': len(results),
                    'failed': len(errors),
                    'success_rate': len(results) / len(data_list) * 100 if data_list else 0}}

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        self.logger.info("获取系统状态")

        # 获取错误统计
        error_stats = self.error_monitor.get_error_stats()

        # 获取性能统计
        performance_stats = self.performance_monitor.get_performance_stats()

        status = {
            'timestamp': time.time(),
            'error_statistics': error_stats,
            'performance_statistics': performance_stats,
            'system_health': self._calculate_system_health(
                error_stats,
                performance_stats)}

        self.logger.info(
            "系统状态获取完成",
            health_score=status['system_health']['score'])
        return status

    def _calculate_system_health(
            self, error_stats: Dict, performance_stats: Dict) -> Dict[str, Any]:
        """计算系统健康度"""
        # 简单的健康度计算逻辑
        total_errors = error_stats.get('total_errors', 0)
        error_types = error_stats.get('error_types', 0)

        # 基础分数
        health_score = 100

        # 根据错误数量扣分
        if total_errors > 0:
            health_score -= min(total_errors * 2, 50)  # 最多扣50分

        # 根据错误类型扣分
        if error_types > 0:
            health_score -= min(error_types * 5, 30)  # 最多扣30分

        # 根据性能统计调整
        for operation, stats in performance_stats.items():
            if isinstance(stats, dict) and 'slow_operations' in stats:
                slow_ops = stats.get('slow_operations', 0)
                if slow_ops > 0:
                    health_score -= min(slow_ops, 20)  # 最多扣20分

        health_score = max(health_score, 0)  # 确保不低于0

        # 确定健康等级
        if health_score >= 90:
            health_level = 'excellent'
        elif health_score >= 70:
            health_level = 'good'
        elif health_score >= 50:
            health_level = 'fair'
        else:
            health_level = 'poor'

        return {
            'score': health_score,
            'level': health_level,
            'factors': {
                'total_errors': total_errors,
                'error_types': error_types,
                'performance_issues': sum(
                    stats.get('slow_operations', 0) if isinstance(stats, dict) else 0
                    for stats in performance_stats.values()
                )
            }
        }


def demonstrate_error_handling():
    """演示错误处理功能"""
    print("=== 错误处理和日志系统演示 ===")

    # 创建服务实例
    service = ProjectService()

    # 演示正常处理
    print("\n1. 正常数据处理:")
    try:
        result = service.process_data({
            'required_field': 'test_value',
            'data': 'some_data',
            'processing_time': 0.1
        })
        print(f"处理成功: {result['id']}")
    except Exception as e:
        print(f"处理失败: {e}")

    # 演示可恢复错误
    print("\n2. 可恢复错误处理:")
    try:
        result = service.process_data({})
        print(f"处理成功: {result}")
    except RecoverableError as e:
        print(f"可恢复错误: {e.message}")
        print(f"恢复建议: {e.recovery_suggestion}")
    except Exception as e:
        print(f"其他错误: {e}")

    # 演示重试机制
    print("\n3. 重试机制演示:")
    try:
        result = service.process_data({
            'required_field': 'test_value',
            'simulate_network_error': True,
            'processing_time': 0.1
        })
        print(f"重试成功: {result['id']}")
    except Exception as e:
        print(f"重试失败: {e}")

    # 演示批量处理
    print("\n4. 批量处理演示:")
    test_data = [
        {'required_field': 'value1', 'processing_time': 0.1},
        {'required_field': 'value2', 'processing_time': 0.2},
        {},  # 这个会失败
        {'required_field': 'value3', 'simulate_save_error': True},  # 这个也会失败
        {'required_field': 'value4', 'processing_time': 0.1}
    ]

    batch_result = service.batch_process(test_data)
    print(f"批量处理完成:")
    print(f"  总数: {batch_result['summary']['total']}")
    print(f"  成功: {batch_result['summary']['successful']}")
    print(f"  失败: {batch_result['summary']['failed']}")
    print(f"  成功率: {batch_result['summary']['success_rate']:.1f}%")

    # 演示系统状态
    print("\n5. 系统状态:")
    status = service.get_system_status()
    health = status['system_health']
    print(f"系统健康度: {health['score']}/100 ({health['level']})")
    print(f"总错误数: {status['error_statistics']['total_errors']}")
    print(f"错误类型数: {status['error_statistics']['error_types']}")

    print("\n=== 演示完成 ===")


if __name__ == '__main__':
    demonstrate_error_handling()