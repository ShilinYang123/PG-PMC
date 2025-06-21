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

    def __init__(self, message: str, error_code: str = None,
                 details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.details = details or {}
        self.timestamp = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(StructureCheckError):
    """配置相关错误"""

    def __init__(
            self,
            message: str,
            config_file: str = None,
            config_key: str = None):
        super().__init__(message, 'CONFIG_ERROR')
        self.details.update({
            'config_file': config_file,
            'config_key': config_key
        })


class FileSystemError(StructureCheckError):
    """文件系统相关错误"""

    def __init__(
            self,
            message: str,
            file_path: str = None,
            operation: str = None):
        super().__init__(message, 'FILESYSTEM_ERROR')
        self.details.update({
            'file_path': str(file_path) if file_path else None,
            'operation': operation
        })


class ValidationError(StructureCheckError):
    """验证相关错误"""

    def __init__(
            self,
            message: str,
            validation_type: str = None,
            failed_items: List[str] = None):
        super().__init__(message, 'VALIDATION_ERROR')
        self.details.update({
            'validation_type': validation_type,
            'failed_items': failed_items or []
        })


class StandardParsingError(StructureCheckError):
    """标准文件解析错误"""

    def __init__(
            self,
            message: str,
            standard_file: str = None,
            line_number: int = None):
        super().__init__(message, 'STANDARD_PARSING_ERROR')
        self.details.update({
            'standard_file': str(standard_file) if standard_file else None,
            'line_number': line_number
        })


class NamingConventionError(ValidationError):
    """命名规范错误"""

    def __init__(
            self,
            message: str,
            file_path: str = None,
            expected_pattern: str = None):
        super().__init__(message, 'NAMING_CONVENTION')
        self.details.update({
            'file_path': str(file_path) if file_path else None,
            'expected_pattern': expected_pattern
        })


class ForbiddenItemError(ValidationError):
    """禁止项目错误"""

    def __init__(
            self,
            message: str,
            forbidden_path: str = None,
            pattern: str = None):
        super().__init__(message, 'FORBIDDEN_ITEM')
        self.details.update({
            'forbidden_path': str(forbidden_path) if forbidden_path else None,
            'pattern': pattern
        })


class MissingRequiredError(ValidationError):
    """缺少必需项错误"""

    def __init__(
            self,
            message: str,
            missing_type: str = None,
            missing_items: List[str] = None):
        super().__init__(message, 'MISSING_REQUIRED')
        self.details.update({
            'missing_type': missing_type,
            'missing_items': missing_items or []
        })


class PerformanceError(StructureCheckError):
    """性能相关错误"""

    def __init__(
            self,
            message: str,
            operation: str = None,
            duration: float = None):
        super().__init__(message, 'PERFORMANCE_ERROR')
        self.details.update({
            'operation': operation,
            'duration': duration
        })


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
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_info': len(self.info_messages),
            'error_types': self._get_error_types(),
            'has_critical_errors': self._has_critical_errors()
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
        critical_types = [
            ConfigurationError,
            FileSystemError,
            StandardParsingError]
        return any(isinstance(error, tuple(critical_types))
                   for error in self.errors)

    def get_errors_by_type(
            self,
            error_type: type) -> List[StructureCheckError]:
        """按类型获取错误"""
        return [
            error for error in self.errors if isinstance(
                error, error_type)]

    def clear(self):
        """清空所有错误和警告"""
        self.errors.clear()
        self.warnings.clear()
        self.info_messages.clear()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'summary': self.get_summary(),
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'info_messages': self.info_messages.copy()
        }


class ErrorHandler:
    """错误处理器，提供统一的错误处理和报告功能"""

    def __init__(self, collector: ErrorCollector = None):
        self.collector = collector or ErrorCollector()
        self.debug_mode = False

    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.debug_mode = enabled

    def handle_exception(
            self,
            exc: Exception,
            context: str = None) -> StructureCheckError:
        """处理异常，转换为结构化错误"""
        if isinstance(exc, StructureCheckError):
            structured_error = exc
        else:
            # 将普通异常转换为结构化错误
            structured_error = StructureCheckError(
                message=str(exc),
                error_code='UNEXPECTED_ERROR',
                details={
                    'original_exception': exc.__class__.__name__,
                    'context': context,
                    'traceback': traceback.format_exc() if self.debug_mode else None})

        self.collector.add_error(structured_error)
        return structured_error

    def handle_validation_error(
            self,
            message: str,
            validation_type: str = None,
            failed_items: List[str] = None) -> ValidationError:
        """处理验证错误"""
        error = ValidationError(message, validation_type, failed_items)
        self.collector.add_error(error)
        return error

    def handle_warning(
            self,
            message: str,
            warning_type: str = None) -> StructureCheckError:
        """处理警告"""
        warning = StructureCheckError(message, warning_type or 'WARNING')
        self.collector.add_warning(warning)
        return warning

    def safe_execute(self, func, *args, **kwargs):
        """安全执行函数，自动处理异常"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_exception(e, f"执行函数 {func.__name__}")
            return None

    def generate_error_report(self) -> str:
        """生成错误报告"""
        if not self.collector.has_errors() and not self.collector.has_warnings():
            return "✅ 检查完成，未发现问题"

        report_lines = []

        if self.collector.has_errors():
            report_lines.append(
                f"❌ 发现 {
                    self.collector.get_error_count()} 个错误:")
            for i, error in enumerate(self.collector.errors, 1):
                report_lines.append(f"  {i}. {error}")
                if self.debug_mode and error.details:
                    report_lines.append(f"     详情: {error.details}")

        if self.collector.has_warnings():
            report_lines.append(
                f"⚠️ 发现 {
                    self.collector.get_warning_count()} 个警告:")
            for i, warning in enumerate(self.collector.warnings, 1):
                report_lines.append(f"  {i}. {warning}")

        return "\n".join(report_lines)


def create_error_handler(debug_mode: bool = False) -> ErrorHandler:
    """创建错误处理器"""
    handler = ErrorHandler()
    handler.set_debug_mode(debug_mode)
    return handler

# 预定义的常用错误创建函数


def config_not_found_error(config_file: str) -> ConfigurationError:
    """配置文件未找到错误"""
    return ConfigurationError(
        f"配置文件不存在: {config_file}",
        config_file=config_file
    )


def invalid_config_format_error(
        config_file: str,
        details: str = None) -> ConfigurationError:
    """无效配置格式错误"""
    message = f"配置文件格式无效: {config_file}"
    if details:
        message += f" - {details}"
    return ConfigurationError(message, config_file=config_file)


def file_not_found_error(
        file_path: str,
        operation: str = "访问") -> FileSystemError:
    """文件未找到错误"""
    return FileSystemError(
        f"文件不存在: {file_path}",
        file_path=file_path,
        operation=operation
    )


def permission_denied_error(file_path: str,
                            operation: str = "访问") -> FileSystemError:
    """权限拒绝错误"""
    return FileSystemError(
        f"权限不足，无法{operation}: {file_path}",
        file_path=file_path,
        operation=operation
    )


def naming_violation_error(
        file_path: str,
        pattern: str) -> NamingConventionError:
    """命名规范违反错误"""
    return NamingConventionError(
        f"文件名不符合规范: {file_path}",
        file_path=file_path,
        expected_pattern=pattern
    )


def forbidden_item_error(item_path: str, pattern: str) -> ForbiddenItemError:
    """禁止项目错误"""
    return ForbiddenItemError(
        f"发现禁止的文件或目录: {item_path}",
        forbidden_path=item_path,
        pattern=pattern
    )


def missing_required_error(missing_type: str,
                           missing_items: List[str]) -> MissingRequiredError:
    """缺少必需项错误"""
    items_str = ", ".join(missing_items)
    return MissingRequiredError(
        f"缺少必需的{missing_type}: {items_str}",
        missing_type=missing_type,
        missing_items=missing_items
    )
