#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构检查工具专用异常类
提供结构化的错误处理和异常管理
"""

from typing import Dict, List, Any
import traceback


class StructureCheckError(Exception):
    """项目结构检查基础异常类"""

    def __init__(
        self, message: str, error_code: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(StructureCheckError):
    """配置相关错误"""

    def __init__(self, message: str, config_file: str = None, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR")
        self.details.update({"config_file": config_file, "config_key": config_key})


class FileSystemError(StructureCheckError):
    """文件系统相关错误"""

    def __init__(self, message: str, file_path: str = None, operation: str = None):
        super().__init__(message, "FILESYSTEM_ERROR")
        self.details.update(
            {"file_path": str(file_path) if file_path else None, "operation": operation}
        )


class ValidationError(StructureCheckError):
    """验证相关错误"""

    def __init__(
        self, message: str, validation_type: str = None, failed_items: List[str] = None
    ):
        super().__init__(message, "VALIDATION_ERROR")
        self.details.update(
            {"validation_type": validation_type, "failed_items": failed_items or []}
        )


class StandardParsingError(StructureCheckError):
    """标准文件解析错误"""

    def __init__(
        self, message: str, standard_file: str = None, line_number: int = None
    ):
        super().__init__(message, "STANDARD_PARSING_ERROR")
        self.details.update(
            {
                "standard_file": str(standard_file) if standard_file else None,
                "line_number": line_number,
            }
        )


class NamingConventionError(ValidationError):
    """命名规范错误"""

    def __init__(
        self, message: str, file_path: str = None, expected_pattern: str = None
    ):
        super().__init__(message, "NAMING_CONVENTION")
        self.details.update(
            {
                "file_path": str(file_path) if file_path else None,
                "expected_pattern": expected_pattern,
            }
        )


class ForbiddenItemError(ValidationError):
    """禁止项目错误"""

    def __init__(self, message: str, forbidden_path: str = None, pattern: str = None):
        super().__init__(message, "FORBIDDEN_ITEM")
        self.details.update(
            {
                "forbidden_path": str(forbidden_path) if forbidden_path else None,
                "pattern": pattern,
            }
        )


class MissingRequiredError(ValidationError):
    """缺少必需项错误"""

    def __init__(
        self, message: str, missing_type: str = None, missing_items: List[str] = None
    ):
        super().__init__(message, "MISSING_REQUIRED")
        self.details.update(
            {"missing_type": missing_type, "missing_items": missing_items or []}
        )


class PerformanceError(StructureCheckError):
    """性能相关错误"""

    def __init__(self, message: str, operation: str = None, duration: float = None):
        super().__init__(message, "PERFORMANCE_ERROR")
        self.details.update({"operation": operation, "duration": duration})


class ErrorCollector:
    """错误收集器，用于收集和管理检查过程中的所有错误"""

    def __init__(self):
        self.errors: List[StructureCheckError] = []
        self.warnings: List[StructureCheckError] = []
        self.info_messages: List[str] = []

    def add_error(self, error: StructureCheckError):
        """添加错误"""
        self.errors.append(error)

    def add_warning(self, warning: StructureCheckError):
        """添加警告"""
        self.warnings.append(warning)

    def add_info(self, message: str):
        """添加信息"""
        self.info_messages.append(message)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0

    def get_error_count(self) -> int:
        """获取错误数量"""
        return len(self.errors)

    def get_warning_count(self) -> int:
        """获取警告数量"""
        return len(self.warnings)

    def get_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_info": len(self.info_messages),
            "error_types": self._get_error_types(),
            "has_critical_errors": self._has_critical_errors(),
        }

    def _get_error_types(self) -> Dict[str, int]:
        """获取错误类型统计"""
        error_types = {}
        for error in self.errors:
            error_type = error.__class__.__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        return error_types

    def _has_critical_errors(self) -> bool:
        """是否有严重错误"""
        critical_types = [ConfigurationError, FileSystemError, StandardParsingError]
        return any(isinstance(error, tuple(critical_types)) for error in self.errors)

    def get_errors_by_type(self, error_type: type) -> List[StructureCheckError]:
        """按类型获取错误"""
        return [error for error in self.errors if isinstance(error, error_type)]

    def clear(self):
        """清空所有错误和警告"""
        self.errors.clear()
        self.warnings.clear()
        self.info_messages.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "summary": self.get_summary(),
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "info_messages": self.info_messages.copy(),
        }


class ErrorHandler:
    """错误处理器，提供统一的错误处理和报告功能"""

    def __init__(
        self, collector: ErrorCollector = None, enable_graceful_degradation: bool = True
    ):
        self.collector = collector or ErrorCollector()
        self.debug_mode = False
        self.enable_graceful_degradation = enable_graceful_degradation
        self.degradation_strategies = {
            ConfigurationError: self._handle_config_error,
            FileSystemError: self._handle_filesystem_error,
            StandardParsingError: self._handle_parsing_error,
            ValidationError: self._handle_validation_error,
            PerformanceError: self._handle_performance_error,
        }

    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled

    def handle_exception(
        self, exc: Exception, context: str = None, allow_degradation: bool = True
    ) -> tuple[StructureCheckError, bool]:
        """处理异常，转换为结构化错误

        Returns:
            tuple: (structured_error, should_continue)
        """
        if isinstance(exc, StructureCheckError):
            structured_error = exc
        else:
            # 将普通异常转换为结构化错误
            structured_error = StructureCheckError(
                message=str(exc),
                error_code="UNEXPECTED_ERROR",
                details={
                    "original_exception": exc.__class__.__name__,
                    "context": context,
                    "traceback": traceback.format_exc() if self.debug_mode else None,
                },
            )

        self.collector.add_error(structured_error)

        # 尝试优雅降级
        should_continue = True
        if self.enable_graceful_degradation and allow_degradation:
            should_continue = self._attempt_graceful_degradation(
                structured_error, context
            )

        return structured_error, should_continue

    def handle_validation_error(
        self, message: str, validation_type: str = None, failed_items: List[str] = None
    ) -> ValidationError:
        """处理验证错误"""
        error = ValidationError(message, validation_type, failed_items)
        self.collector.add_error(error)
        return error

    def handle_warning(
        self, message: str, warning_type: str = None
    ) -> StructureCheckError:
        """处理警告"""
        warning = StructureCheckError(message, warning_type or "WARNING")
        self.collector.add_warning(warning)
        return warning

    def handle_error(self, error, context: str = None):
        """处理错误的通用方法"""
        if isinstance(error, Exception):
            self.handle_exception(error, context)
        elif isinstance(error, StructureCheckError):
            self.collector.add_error(error)
        else:
            # 如果是字符串消息，创建一个通用错误
            structured_error = StructureCheckError(
                message=str(error),
                error_code="GENERAL_ERROR",
                details={"context": context} if context else None,
            )
            self.collector.add_error(structured_error)

    def safe_execute(
        self, func, *args, default_return=None, allow_degradation=True, **kwargs
    ):
        """安全执行函数，自动处理异常

        Args:
            func: 要执行的函数
            *args: 函数参数
            default_return: 异常时的默认返回值
            allow_degradation: 是否允许优雅降级
            **kwargs: 函数关键字参数

        Returns:
            函数返回值或默认值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error, should_continue = self.handle_exception(
                e, f"执行函数 {func.__name__}", allow_degradation
            )
            if should_continue:
                return default_return
            else:
                raise error

    def generate_error_report(self) -> str:
        """生成错误报告"""
        if not self.collector.has_errors() and not self.collector.has_warnings():
            return "✅ 检查完成，未发现问题"

        report_lines = []

        if self.collector.has_errors():
            report_lines.append(
                f"❌ 发现 {
                    self.collector.get_error_count()} 个错误:"
            )
            for i, error in enumerate(self.collector.errors, 1):
                report_lines.append(f"  {i}. {error}")
                if self.debug_mode and error.details:
                    report_lines.append(f"     详情: {error.details}")

        if self.collector.has_warnings():
            report_lines.append(
                f"⚠️ 发现 {
                    self.collector.get_warning_count()} 个警告:"
            )
            for i, warning in enumerate(self.collector.warnings, 1):
                report_lines.append(f"  {i}. {warning}")

        return "\n".join(report_lines)

    def _attempt_graceful_degradation(
        self, error: StructureCheckError, context: str = None
    ) -> bool:
        """尝试优雅降级处理

        Args:
            error: 结构化错误对象
            context: 错误上下文

        Returns:
            bool: 是否可以继续执行
        """
        # 查找对应的降级策略
        for exception_type, strategy in self.degradation_strategies.items():
            if isinstance(error, exception_type):
                return strategy(error, context)

        # 没有找到特定策略，使用默认策略
        return self._default_degradation_strategy(error, context)

    def _handle_config_error(
        self, error: ConfigurationError, context: str = None
    ) -> bool:
        """处理配置错误的降级策略"""
        if self.debug_mode:
            print(f"🔧 配置错误降级: {error.message}")

        # 配置错误通常可以使用默认值继续
        if "config_key" in error.details:
            print(f"   使用默认配置项: {error.details['config_key']}")

        return True  # 可以继续执行

    def _handle_filesystem_error(
        self, error: FileSystemError, context: str = None
    ) -> bool:
        """处理文件系统错误的降级策略"""
        if self.debug_mode:
            print(f"📁 文件系统错误降级: {error.message}")

        # 根据操作类型决定是否可以继续
        operation = error.details.get("operation", "")

        if operation in ["read", "scan", "access"]:
            print("   跳过无法访问的文件/目录")
            return True  # 可以继续执行
        elif operation in ["write", "create", "delete"]:
            print("   写操作失败，尝试替代方案")
            return True  # 可以尝试继续
        else:
            return False  # 未知操作，停止执行

    def _handle_parsing_error(
        self, error: StandardParsingError, context: str = None
    ) -> bool:
        """处理解析错误的降级策略"""
        if self.debug_mode:
            print(f"📄 解析错误降级: {error.message}")

        # 解析错误通常可以使用部分数据继续
        if "line_number" in error.details:
            print(f"   跳过第 {error.details['line_number']} 行，继续解析")

        return True  # 可以继续执行

    def _handle_validation_error(
        self, error: ValidationError, context: str = None
    ) -> bool:
        """处理验证错误的降级策略"""
        if self.debug_mode:
            print(f"✅ 验证错误降级: {error.message}")

        # 验证错误通常不影响继续执行
        validation_type = error.details.get("validation_type", "")

        if validation_type in ["naming_convention", "forbidden_item"]:
            print("   记录违规项目，继续检查")
            return True
        elif validation_type == "missing_required":
            print("   记录缺失项目，继续检查")
            return True
        else:
            return True  # 默认可以继续

    def _handle_performance_error(
        self, error: PerformanceError, context: str = None
    ) -> bool:
        """处理性能错误的降级策略"""
        if self.debug_mode:
            print(f"⚡ 性能错误降级: {error.message}")

        # 性能错误通常可以通过调整参数继续
        operation = error.details.get("operation", "")
        duration = error.details.get("duration", 0)

        if operation == "scan" and duration > 30:
            print("   扫描超时，尝试减少扫描深度")
            return True
        elif operation == "parse" and duration > 10:
            print("   解析超时，尝试简化解析")
            return True
        else:
            return True  # 默认可以继续

    def _default_degradation_strategy(
        self, error: StructureCheckError, context: str = None
    ) -> bool:
        """默认降级策略"""
        if self.debug_mode:
            print(f"🔄 默认降级策略: {error.message}")

        # 根据错误代码决定是否可以继续
        if error.error_code in ["WARNING", "INFO"]:
            return True
        elif error.error_code in ["CRITICAL_ERROR", "FATAL_ERROR"]:
            return False
        else:
            # 未知错误，保守处理
            return True


def create_error_handler(debug_mode: bool = False) -> ErrorHandler:
    """创建错误处理器"""
    handler = ErrorHandler()
    handler.set_debug_mode(debug_mode)
    return handler


# 预定义的常用错误创建函数


def config_not_found_error(config_file: str) -> ConfigurationError:
    """配置文件未找到错误"""
    return ConfigurationError(f"配置文件不存在: {config_file}", config_file=config_file)


def invalid_config_format_error(
    config_file: str, details: str = None
) -> ConfigurationError:
    """无效配置格式错误"""
    message = f"配置文件格式无效: {config_file}"
    if details:
        message += f" - {details}"
    return ConfigurationError(message, config_file=config_file)


def file_not_found_error(file_path: str, operation: str = "访问") -> FileSystemError:
    """文件未找到错误"""
    return FileSystemError(
        f"文件不存在: {file_path}", file_path=file_path, operation=operation
    )


def permission_denied_error(file_path: str, operation: str = "访问") -> FileSystemError:
    """权限拒绝错误"""
    return FileSystemError(
        f"权限不足，无法{operation}: {file_path}",
        file_path=file_path,
        operation=operation,
    )


def naming_violation_error(file_path: str, pattern: str) -> NamingConventionError:
    """命名规范违反错误"""
    return NamingConventionError(
        f"文件名不符合规范: {file_path}", file_path=file_path, expected_pattern=pattern
    )


def forbidden_item_error(item_path: str, pattern: str) -> ForbiddenItemError:
    """禁止项目错误"""
    return ForbiddenItemError(
        f"发现禁止的文件或目录: {item_path}", forbidden_path=item_path, pattern=pattern
    )


def missing_required_error(
    missing_type: str, missing_items: List[str]
) -> MissingRequiredError:
    """缺少必需项错误"""
    items_str = ", ".join(missing_items)
    return MissingRequiredError(
        f"缺少必需的{missing_type}: {items_str}",
        missing_type=missing_type,
        missing_items=missing_items,
    )
